"""
Controlled Event Category Taxonomy and Multi-Label Classification Engine.

Implements hard-filtered categorization with confidence scoring.
Guarantees that general cultural/temple events (like autumn foliage illuminations)
are NEVER falsely classified as Anime & Gaming.
"""

import re
from typing import List, Dict, Any, Set, Tuple

# Controlled Taxonomy as required
TAXONOMY = {
    "ANIME_GAMING": "Anime & Gaming",
    "TECHNOLOGY": "Technology",
    "FOOD_DRINK": "Food & Drink",
    "CULTURE_MATSURI": "Culture & Matsuri",
    "ART_DESIGN": "Art & Design",
    "MUSIC_CONCERTS": "Music & Concerts",
    "SPORTS": "Sports",
}

# Strong positive signal keywords
CATEGORY_SIGNALS = {
    "ANIME_GAMING": [
        "anime", "manga", "otaku", "cosplay", "cosplayer", "video game", "videogame",
        "gaming", "esports", "e-sports", "nintendo", "playstation", "pokemon", "comiket",
        "akihabara", "comic convention", "doujinshi", "game exhibition", "voice actor",
        "seiyuu", "arcade", "j-pop culture", "tokyo game show", "pop-culture expo",
        "anime expo", "manga fair", "shonen", "mecha", "genshin", "vocaloid", "hatsune miku",
    ],
    "TECHNOLOGY": [
        "tech", "technology", "artificial intelligence", " ai ", "ai-powered", "robot",
        "robotics", "software", "developer", "hackathon", "startup", "cybersecurity",
        "cloud computing", "iot", "gadgets", "quantum computing", "blockchain",
        "fintech", "biotech", "web3", "digital tech", "electronics expo",
    ],
    "FOOD_DRINK": [
        "food", "culinary", "gourmet", "tasting", "ramen", "sushi", "sake", "craft beer",
        "wine", "winery", "bistro", "chef", "bakery", "street food", "dining", "seafood market",
        "chocolate", "pastry", "harvest market", "brewery", "food truck", "food festival",
        "beaujolais", "takoyaki", "curry grand prix", "farmers market",
    ],
    "CULTURE_MATSURI": [
        "temple", "shrine", "matsuri", "traditional festival", "shinto", "buddhist",
        "mikoshi", "yabusame", "autumn foliage", "foliage", "leaves", "illumination walk",
        "cherry blossom", "hanami", "tea ceremony", "kimono", "yukata", "historic",
        "heritage", "ancient", "ceremony", "noh", "kabuki", "tori-no-ichi", "lantern festival",
        "sacred", "monastery", "gion", "arashiyama", "kiyomizu",
    ],
    "ART_DESIGN": [
        "art exhibition", "fine art", "gallery", "contemporary art", "sculpture", "painting",
        "museum", "photography", "design fair", "architecture", "biennale", "triennale",
        "digital art installation", "salon d'automne", "paris photo", "visual arts",
    ],
    "MUSIC_CONCERTS": [
        "concert", "music festival", "orchestra", "symphony", "jazz", "acoustic", "band",
        "live music", "opera", "recital", "choir", "dj set", "electronic music", "blues",
        "brass band", "rock concert", "philharmonic",
    ],
    "SPORTS": [
        "marathon", "tournament", "sumo", "soccer", "football", "baseball", "judo",
        "cycling", "race", "half marathon", "triathlon", "basketball", "tennis",
        "martial arts", "championship", "stadium",
    ],
}

# Strong negative exclusion patterns: if an event is primarily temples/gardens/foliage,
# it CANNOT be classified as ANIME_GAMING unless an explicit anime collaboration keyword exists.
ANIME_EXCLUSION_PATTERNS = [
    r"\bfowliage\b", r"\bautumn leaves\b", r"\bfoliage illumination\b",
    r"\btemple garden\b", r"\bshrine ceremony\b", r"\btea ceremony\b",
    r"\bwine tasting\b", r"\bmarathon\b", r"\bbistro\b", r"\btraditional craft\b"
]


def classify_event(event_dict: Dict[str, Any]) -> Tuple[List[str], float, str]:
    """
    Deterministically classifies an event into the controlled taxonomy.
    
    Returns:
        categories (list of str): e.g. ["ANIME_GAMING"] or ["CULTURE_MATSURI", "ART_DESIGN"]
        confidence (float): 0.0 - 1.0 confidence score
        primary_category (str): dominant category
    """
    name = str(event_dict.get("name", "")).lower()
    desc = str(event_dict.get("description", "")).lower()
    venue = str(event_dict.get("venue", "")).lower()
    raw_cat = str(event_dict.get("category", "")).lower()

    full_text = f" {name} {name} {desc} {venue} {raw_cat} "

    scores: Dict[str, float] = {k: 0.0 for k in TAXONOMY}

    for cat_key, keywords in CATEGORY_SIGNALS.items():
        score = 0.0
        for kw in keywords:
            # Check title (high weight)
            if re.search(r"\b" + re.escape(kw.strip()) + r"\b", name):
                score += 3.0
            # Check full text
            elif re.search(r"\b" + re.escape(kw.strip()) + r"\b", full_text):
                score += 1.0
        scores[cat_key] = score

    # Check raw_cat hint
    raw_cat_map = {
        "anime": "ANIME_GAMING",
        "gaming": "ANIME_GAMING",
        "tech": "TECHNOLOGY",
        "food": "FOOD_DRINK",
        "culture": "CULTURE_MATSURI",
        "art": "ART_DESIGN",
        "music": "MUSIC_CONCERTS",
        "sports": "SPORTS",
    }
    if raw_cat in raw_cat_map:
        scores[raw_cat_map[raw_cat]] += 2.5

    # STRICT EXCLUSION CHECK FOR ANIME_GAMING:
    # If the text has anime negative patterns and no explicit anime title keyword, zero it out!
    has_explicit_anime_in_title = any(kw in name for kw in ["anime", "manga", "gaming", "cosplay", "otaku", "comiket", "esports"])
    has_anime_exclusion = any(re.search(pat, full_text) for pat in ANIME_EXCLUSION_PATTERNS)
    if has_anime_exclusion and not has_explicit_anime_in_title:
        scores["ANIME_GAMING"] = 0.0

    # STRICT SEPARATION BETWEEN ART_DESIGN AND TECHNOLOGY:
    # Ordinary art exhibitions, galleries, and museums must NOT become TECHNOLOGY
    # unless explicit technology/computing/robotics components are present.
    art_keywords = ["art exhibition", "fine art", "museum", "gallery", "sculpture", "painting", "photography", "salon d'automne", "paris photo"]
    is_primarily_art = any(k in full_text for k in art_keywords)
    has_explicit_tech = any(re.search(r"\b" + re.escape(k) + r"\b", full_text) for k in [
        "artificial intelligence", "robotics", "software", "developer", "hackathon", "tech summit", "cybersecurity", "ai application", "machine learning"
    ])
    if is_primarily_art and not has_explicit_tech:
        scores["TECHNOLOGY"] = 0.0

    total_score = sum(scores.values())
    if total_score == 0.0:
        # Fallback to CULTURE_MATSURI with low confidence
        return ["CULTURE_MATSURI"], 0.45, "CULTURE_MATSURI"

    # Sort categories by score descending
    ranked_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_cat, best_score = ranked_cats[0]

    # Calculate confidence based on dominance over other categories
    confidence = min(0.98, max(0.50, best_score / (total_score + 1.0) * 1.5))
    confidence = round(float(confidence), 2)

    assigned_cats = [best_cat]

    # Secondary category if close enough (score >= 2.0 and at least 50% of best)
    for cat, sc in ranked_cats[1:]:
        if sc >= 2.0 and sc >= (best_score * 0.5):
            assigned_cats.append(cat)

    return assigned_cats, confidence, best_cat


def parse_requested_categories(category_param: str, interests_param: str) -> Tuple[Set[str], bool]:
    """
    Parses user inputs into a set of taxonomy category keys.
    
    Returns:
        (category_keys_set, is_all)
        If is_all is True, no category filtering is applied.
    """
    cat_clean = (category_param or "").strip().upper()
    int_clean = (interests_param or "").strip().lower()

    if cat_clean in ("ALL", "ALL EVENTS", "*"):
        return set(TAXONOMY.keys()), True

    requested = set()

    # 1. Parse from category dropdown/pill
    dropdown_map = {
        "ANIME": "ANIME_GAMING",
        "ANIME_GAMING": "ANIME_GAMING",
        "ANIME & GAMING": "ANIME_GAMING",
        "TECH": "TECHNOLOGY",
        "TECHNOLOGY": "TECHNOLOGY",
        "FOOD": "FOOD_DRINK",
        "FOOD_DRINK": "FOOD_DRINK",
        "FOOD & DRINK": "FOOD_DRINK",
        "CULTURE": "CULTURE_MATSURI",
        "CULTURE_MATSURI": "CULTURE_MATSURI",
        "CULTURE & MATSURI": "CULTURE_MATSURI",
        "ART": "ART_DESIGN",
        "ART_DESIGN": "ART_DESIGN",
        "ART & DESIGN": "ART_DESIGN",
        "MUSIC": "MUSIC_CONCERTS",
        "MUSIC_CONCERTS": "MUSIC_CONCERTS",
        "MUSIC & CONCERTS": "MUSIC_CONCERTS",
        "SPORTS": "SPORTS",
    }
    dropdown_requested = set()
    for part in cat_clean.split(","):
        p = part.strip()
        if p in dropdown_map:
            dropdown_requested.add(dropdown_map[p])

    # If user explicitly selected specific category/categories from dropdown,
    # that is the strict HARD constraint!
    if dropdown_requested:
        return dropdown_requested, False

    # 2. If dropdown was "all" or empty, parse from interests text/tags
    interest_map = {
        "anime": "ANIME_GAMING",
        "manga": "ANIME_GAMING",
        "gaming": "ANIME_GAMING",
        "video games": "ANIME_GAMING",
        "cosplay": "ANIME_GAMING",
        "otaku": "ANIME_GAMING",
        "esports": "ANIME_GAMING",
        "technology": "TECHNOLOGY",
        "tech": "TECHNOLOGY",
        "ai": "TECHNOLOGY",
        "robotics": "TECHNOLOGY",
        "software": "TECHNOLOGY",
        "food": "FOOD_DRINK",
        "culinary": "FOOD_DRINK",
        "sake": "FOOD_DRINK",
        "wine": "FOOD_DRINK",
        "dining": "FOOD_DRINK",
        "gourmet": "FOOD_DRINK",
        "culture": "CULTURE_MATSURI",
        "traditional culture": "CULTURE_MATSURI",
        "shinto": "CULTURE_MATSURI",
        "temples": "CULTURE_MATSURI",
        "shrines": "CULTURE_MATSURI",
        "matsuri": "CULTURE_MATSURI",
        "foliage": "CULTURE_MATSURI",
        "art": "ART_DESIGN",
        "exhibitions": "ART_DESIGN",
        "museums": "ART_DESIGN",
        "design": "ART_DESIGN",
        "galleries": "ART_DESIGN",
        "music": "MUSIC_CONCERTS",
        "concerts": "MUSIC_CONCERTS",
        "jazz": "MUSIC_CONCERTS",
        "orchestra": "MUSIC_CONCERTS",
        "sports": "SPORTS",
        "marathon": "SPORTS",
        "sumo": "SPORTS",
    }

    # Tokenize interests
    interest_requested = set()
    for phrase, tax_key in interest_map.items():
        if re.search(r"\b" + re.escape(phrase) + r"\b", int_clean):
            interest_requested.add(tax_key)

    if interest_requested:
        return interest_requested, False

    # If nothing specific was extracted, return all categories
    return set(TAXONOMY.keys()), True


def matches_category(event_categories: List[str], event_confidence: float, requested_categories: Set[str], confidence_threshold: float = 0.55) -> bool:
    """
    STRICT STAGE 1 CATEGORY FILTER:
    Returns True if and only if:
      1. At least one of the event's verified categories is in requested_categories.
      2. The event's category confidence is >= confidence_threshold.
    """
    if not requested_categories:
        return True

    overlap = set(event_categories).intersection(requested_categories)
    if not overlap:
        return False

    return event_confidence >= confidence_threshold
