"""Extract valid JSON objects from LLM/Groq responses (markdown, preamble text, etc.)."""
import json
import logging
import re
from json import JSONDecodeError
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

_JSON_DECODER = json.JSONDecoder()

# Root keys expected from the itinerary Groq prompt (prefer these over nested objects).
_ITINERARY_ROOT_KEYS = frozenset({"days", "flights", "hotels", "visa_details"})


def _normalize_text(raw: str) -> str:
    text = str(raw).replace("\ufeff", "").strip()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def _strip_fence_prefix(line: str) -> str:
    """Remove leading ``` or ```json from a single line."""
    s = line.strip()
    if s.startswith("```"):
        s = s[3:].strip()
        if s.lower().startswith("json"):
            s = s[4:].strip()
    return s


def _remove_markdown_fences(text: str) -> str:
    """
    Remove markdown code fences from the full response.
    Handles ```json, ```, optional whitespace, and missing closing fence.
    """
    t = text.strip()

    # Repeatedly peel fenced blocks (non-greedy, case-insensitive)
    for _ in range(5):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", t, re.IGNORECASE)
        if match:
            t = match.group(1).strip()
            continue
        break

    lines = t.split("\n")
    if lines and lines[0].strip().startswith("```"):
        close_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip().startswith("```"):
                close_idx = i
                break
        if close_idx is not None:
            inner_lines = [_strip_fence_prefix(lines[0])] + lines[1:close_idx]
            t = "\n".join(inner_lines).strip()
        else:
            t = "\n".join([_strip_fence_prefix(lines[0])] + lines[1:]).strip()

    # Strip stray fence tokens on edges
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```$", "", t)
    return t.strip()


def _sanitize_json_text(text: str) -> str:
    """Fix common LLM JSON mistakes without changing structure."""
    # Trailing commas before } or ]
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return text.strip()


def _try_json_loads(text: str) -> Tuple[Optional[dict], Optional[str]]:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed, None
        return None, "root is not a JSON object"
    except JSONDecodeError as exc:
        return None, str(exc)


def _is_itinerary_root(obj: dict) -> bool:
    """Root itinerary must expose at least one of days/flights/hotels as arrays."""
    if not isinstance(obj, dict):
        return False
    for key in ("days", "flights", "hotels"):
        if key in obj and isinstance(obj.get(key), list):
            return True
    return False


def _is_visa_leaf(obj: dict) -> bool:
    return isinstance(obj, dict) and "required" in obj and not _is_itinerary_root(obj)


def _itinerary_score(obj: dict) -> int:
    """Higher score = more likely the root itinerary object (never a nested child)."""
    if not _is_itinerary_root(obj):
        if _is_visa_leaf(obj):
            return 1
        if "day" in obj and "activities" in obj:
            return 2
        return 0
    score = 0
    for key in ("days", "flights", "hotels"):
        items = obj.get(key)
        if isinstance(items, list):
            score += 100 + len(items)
    if isinstance(obj.get("visa_details"), dict):
        score += 10
    return score


def _merge_itinerary_fragments(objects: List[dict]) -> dict:
    """Combine partial dicts when the model returned split JSON objects."""
    merged: dict = {"days": [], "flights": [], "hotels": [], "visa_details": {}}
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        if _is_itinerary_root(obj):
            for key in ("days", "flights", "hotels"):
                if isinstance(obj.get(key), list) and obj[key]:
                    merged[key] = obj[key]
            if isinstance(obj.get("visa_details"), dict):
                merged["visa_details"] = obj["visa_details"]
            continue
        if "day" in obj and isinstance(obj.get("activities"), list):
            merged["days"].append(obj)
        elif "airline" in obj and ("departure" in obj or "arrival" in obj):
            merged["flights"].append(obj)
        elif "name" in obj and ("price_per_night" in obj or "location" in obj or "rating" in obj):
            merged["hotels"].append(obj)
        elif _is_visa_leaf(obj):
            merged["visa_details"] = obj
    return merged


def _find_all_objects_via_raw_decode(text: str) -> List[Tuple[dict, str]]:
    """
    Scan for '{' and use JSONDecoder.raw_decode (respects strings; not greedy).
    Returns all successfully parsed dicts with their extracted snippets.
    """
    found: List[Tuple[dict, str]] = []
    seen_ids = set()
    last_error: Optional[str] = None
    i = 0
    while i < len(text):
        start = text.find("{", i)
        if start == -1:
            break
        advanced = False
        for slice_text in (text[start:], _sanitize_json_text(text[start:])):
            try:
                obj, end = _JSON_DECODER.raw_decode(slice_text)
                if isinstance(obj, dict):
                    oid = id(obj)
                    if oid not in seen_ids:
                        seen_ids.add(oid)
                        extracted = slice_text[:end]
                        found.append((obj, extracted))
                    i = start + end
                    advanced = True
                    break
            except JSONDecodeError as exc:
                last_error = str(exc)
        if not advanced:
            i = start + 1
    return found, last_error


def _select_best_itinerary_dict(objects: List[Tuple[dict, str]]) -> Tuple[Optional[dict], Optional[str]]:
    if not objects:
        return None, None
    roots = [(obj, snip) for obj, snip in objects if _is_itinerary_root(obj)]
    if roots:
        scored = sorted(roots, key=lambda pair: _itinerary_score(pair[0]), reverse=True)
        return scored[0]

    # If no itinerary roots, check if any of the parsed objects are non-empty visa / destination context / etc.
    valid_objs = [(obj, snip) for obj, snip in objects if isinstance(obj, dict) and obj]
    if valid_objs:
        best_obj, best_snip = max(valid_objs, key=lambda pair: len(pair[0]))
        destination_keys = {"landmarks", "neighborhoods", "food_spots", "activities", "hidden_gems", "shopping_areas"}
        if any(k in best_obj for k in destination_keys) or "required" in best_obj:
            return best_obj, best_snip

    merged = _merge_itinerary_fragments([obj for obj, _ in objects])
    if (merged.get("days") or merged.get("flights") or merged.get("hotels") or merged.get("visa_details")):
        return merged, None
    return None, None


def _collect_parse_candidates(raw: str) -> List[str]:
    """Build ordered unique candidate strings to attempt parsing."""
    normalized = _normalize_text(raw)
    seen = set()
    candidates: List[str] = []

    def add(s: str) -> None:
        s = s.strip()
        if not s or s in seen:
            return
        seen.add(s)
        candidates.append(s)

    add(normalized)
    unfenced = _remove_markdown_fences(normalized)
    add(unfenced)
    add(_sanitize_json_text(normalized))
    add(_sanitize_json_text(unfenced))

    return candidates


def parse_llm_json_response(raw: str) -> dict:
    """
    Parse a JSON object from model output.

    Supports: pure JSON, markdown fences, preamble/postamble text.
    Never raises except ValueError with a stable user-facing message.
    """
    if raw is None or not str(raw).strip():
        logger.error("[itinerary] Empty LLM response (length=0)")
        raise ValueError("Failed to parse response as JSON")

    original = _normalize_text(raw)
    logger.info("[itinerary] Parsing LLM response (length=%d chars)", len(original))

    candidates = _collect_parse_candidates(original)
    last_load_error: Optional[str] = None
    last_decode_error: Optional[str] = None

    best_fallback: Optional[dict] = None

    for idx, candidate in enumerate(candidates):
        parsed, err = _try_json_loads(candidate)
        if parsed is not None:
            if _is_itinerary_root(parsed):
                snippet = candidate[:400] + ("…" if len(candidate) > 400 else "")
                logger.info(
                    "[itinerary] Parsed root JSON via loads (candidate=%d). keys=%s",
                    idx,
                    list(parsed.keys()),
                )
                return parsed
            if best_fallback is None:
                best_fallback = parsed
            logger.debug(
                "[itinerary] loads returned non-root object (candidate=%d), keys=%s",
                idx,
                list(parsed.keys()),
            )
        last_load_error = err
        logger.debug("[itinerary] json.loads failed candidate=%d: %s", idx, err)

        objects, decode_err = _find_all_objects_via_raw_decode(candidate)
        if decode_err:
            last_decode_error = decode_err
        if objects:
            parsed, extracted = _select_best_itinerary_dict(objects)
            if parsed is not None and (_is_itinerary_root(parsed) or _itinerary_score(parsed) >= 100):
                snippet = (extracted or candidate)[:400]
                if extracted and len(extracted) > 400:
                    snippet += "…"
                logger.info(
                    "[itinerary] Parsed JSON via raw_decode (candidate=%d, objects=%d, "
                    "score=%d, days=%d, flights=%d, hotels=%d). Snippet: %s",
                    idx,
                    len(objects),
                    _itinerary_score(parsed),
                    len(parsed.get("days") or []),
                    len(parsed.get("flights") or []),
                    len(parsed.get("hotels") or []),
                    snippet.replace("\n", " "),
                )
                return parsed
        if decode_err:
            logger.debug("[itinerary] raw_decode failed candidate=%d: %s", idx, decode_err)

    if best_fallback is not None:
        if _is_visa_leaf(best_fallback):
            logger.warning("[itinerary] Wrapping visa-only fallback into itinerary root")
            return {
                "days": [],
                "flights": [],
                "hotels": [],
                "visa_details": best_fallback,
            }
        logger.warning(
            "[itinerary] Using non-root loads fallback, keys=%s",
            list(best_fallback.keys()),
        )
        return best_fallback

    fail_snippet = original[:600].replace("\n", " ")
    logger.error(
        "[itinerary] JSON parse failed (length=%d). loads_error=%s raw_decode_error=%s. Snippet: %s",
        len(original),
        last_load_error,
        last_decode_error,
        fail_snippet,
    )
    raise ValueError("Failed to parse response as JSON")
