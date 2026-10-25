"""Tavily live web search for itinerary factual research."""
import logging
from typing import Any, Dict, List

import requests

from config import TAVILY_API_KEY

logger = logging.getLogger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


def tavily_search(
    query: str,
    max_results: int = 8,
    include_answer: bool = True,
    search_depth: str = "advanced",
) -> Dict[str, Any]:
    """
    Run Tavily search. Returns {snippets, answer, raw_results}.
  snippets are formatted for Groq extraction (source-attributed).
    """
    if not TAVILY_API_KEY:
        logger.warning("[itinerary] TAVILY_API_KEY not set — skipped: %s", query[:90])
        return {"snippets": [], "answer": "", "raw_results": []}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TAVILY_API_KEY}",
    }
    payload = {
        "query": query,
        "max_results": max_results,
        "include_answer": include_answer,
        "search_depth": search_depth,
        "topic": "general",
    }

    try:
        resp = requests.post(TAVILY_SEARCH_URL, json=payload, headers=headers, timeout=45)
        if resp.status_code != 200:
            logger.warning("[itinerary] Tavily HTTP %s: %s", resp.status_code, resp.text[:300])
            return {"snippets": [], "answer": "", "raw_results": []}

        data = resp.json()
        snippets: List[str] = []
        for item in (data.get("results") or [])[:max_results]:
            title = item.get("title") or ""
            content = item.get("content") or ""
            url = item.get("url") or ""
            if title or content:
                snippets.append(f"Title: {title}\n{content}\nURL: {url}".strip())

        answer = (data.get("answer") or "").strip()
        if answer:
            snippets.insert(0, f"Tavily summary:\n{answer}")

        logger.info("[itinerary] Tavily %d snippets for: %s", len(snippets), query[:70])
        return {
            "snippets": snippets,
            "answer": answer,
            "raw_results": data.get("results") or [],
        }
    except requests.RequestException as exc:
        logger.warning("[itinerary] Tavily failed: %s", exc)
        return {"snippets": [], "answer": "", "raw_results": []}


def search_snippets(query: str, num: int = 8) -> List[str]:
    """Backward-compatible helper returning snippet strings only."""
    return tavily_search(query, max_results=num).get("snippets") or []


def multi_search_snippets(queries: List[str], max_results: int = 6) -> List[str]:
    seen = set()
    merged: List[str] = []
    for q in queries:
        for s in tavily_search(q, max_results=max_results).get("snippets") or []:
            key = s[:120]
            if key not in seen:
                seen.add(key)
                merged.append(s)
    return merged
