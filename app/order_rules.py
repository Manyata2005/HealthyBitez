
import re
from datetime import date, datetime, timedelta

CROP_ALIASES = {
    "Radish": ["radish"],
    "Broccoli": ["broccoli"],
    "Sunflower": ["sunflower"],
    "Pea Shoots": ["pea shoots", "pea shoot"],
    "Mustard": ["mustard"],
}

# Only these areas are approved for order confirmation.
# Add an area here only when your business supports delivery there.
APPROVED_DELIVERY_AREAS = [
    "Electronic City",
    "HSR Layout",
    "Bengaluru",
    "Anekal",
]

# Keep the old name as an alias for existing code that imports AREAS.
AREAS = APPROVED_DELIVERY_AREAS

AREA_STOPWORDS = {
    "the", "a", "an", "my", "our", "your", "home", "house",
    "cafe", "café", "office", "morning", "afternoon", "evening",
    "night", "today", "tomorrow", "yesterday", "monday", "tuesday",
    "wednesday", "thursday", "friday", "saturday", "sunday",
    "next", "this", "week", "month",
}

LOCATION_ENDING_WORDS = AREA_STOPWORDS | {
    "please", "for", "by", "before", "after", "with", "and", "but",
    "quantity", "crop", "microgreens", "microgreen",
}


def extract_explicit_crop(message):
    text = message.lower()

    for crop, aliases in CROP_ALIASES.items():
        for alias in aliases:
            if re.search(r"\b" + re.escape(alias) + r"\b", text):
                return crop

    return None


def extract_explicit_quantity(message):
    pattern = r"\b(\d+(?:\.\d+)?)\s*(kg|kilograms?|g|grams?)\b"
    match = re.search(pattern, message.lower())

    if not match:
        return None

    amount = float(match.group(1))
    unit = match.group(2)

    if unit.startswith("kg") or unit.startswith("kilogram"):
        amount *= 1000

    if amount <= 0:
        return None

    return int(amount) if amount.is_integer() else amount


def extract_explicit_customer_type(message):
    text = message.lower()

    if re.search(r"\bcaf[eé]\b", text):
        return "cafe"

    if re.search(
        r"\bretailer\b|\bretail shop\b|\bretail store\b",
        text,
    ):
        return "retailer"

    if re.search(
        r"\bhousehold\b|\bmy home\b|\bour home\b|"
        r"\bmy family\b|\bfor my home\b",
        text,
    ):
        return "household"

    return None


def validate_delivery_area(area):
    """Return the standard approved area name, or None if unsupported."""
    if not isinstance(area, str) or not area.strip():
        return None

    candidate = area.strip()

    for approved_area in APPROVED_DELIVERY_AREAS:
        if candidate.casefold() == approved_area.casefold():
            return approved_area

    return None


def extract_explicit_area(message):
    """
    Extract a location mentioned in the message.

    This function may return an unapproved location.
    Always call validate_delivery_area() before confirming an order.
    """
    if not isinstance(message, str) or not message.strip():
        return None

    text = message.strip()

    # Prefer known approved areas, preserving standard spelling.
    for area in APPROVED_DELIVERY_AREAS:
        if re.search(
            r"\b" + re.escape(area) + r"\b",
            text,
            re.IGNORECASE,
        ):
            return area

    # Look for a candidate location after a location phrase.
    location_patterns = [
        r"\b(?:in|at|near|around)\s+"
        r"([A-Za-z][A-Za-z'-]*"
        r"(?:\s+[A-Za-z][A-Za-z'-]*){0,2})",

        r"\b(?:deliver|send|ship)\s+to\s+"
        r"(?!my\b|our\b|your\b|the\b|a\b|an\b)"
        r"([A-Za-z][A-Za-z'-]*"
        r"(?:\s+[A-Za-z][A-Za-z'-]*){0,2})",
    ]

    for pattern in location_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            candidate = match.group(1).strip().rstrip(".,!?;:")
            words = candidate.split()

            while words and words[-1].lower() in LOCATION_ENDING_WORDS:
                words.pop()

            if not words:
                continue

            if words[0].lower() in LOCATION_ENDING_WORDS:
                continue

            return " ".join(words).title()

    return None


def extract_explicit_special_request(message):
    text = message.lower()

    if re.search(r"\bmorning\b", text):
        return "morning delivery"

    if (
        "separate packaging" in text
        or re.search(r"\bseparately\b", text)
    ):
        return "separate packaging"

    if "freshly packed" in text:
        return "freshly packed"

    return None


def extract_explicit_date(message):
    text = message.lower()

    if re.search(r"\btomorrow\b", text):
        return (date.today() + timedelta(days=1)).isoformat()

    if re.search(r"\btoday\b", text):
        return date.today().isoformat()

    iso_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)

    if iso_match:
        try:
            return date.fromisoformat(iso_match.group(0)).isoformat()
        except ValueError:
            return None

    cleaned = re.sub(
        r"(\d{1,2})(st|nd|rd|th)\b",
        r"\1",
        text,
    )

    date_pattern = (
        r"\b(?:\d{1,2}\s+)?"
        r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|"
        r"may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|"
        r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"\s+\d{1,2}(?:,)?\s+\d{4}\b|"
        r"\b\d{1,2}\s+"
        r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|"
        r"may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|"
        r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"\s+\d{4}\b"
    )

    for match in re.finditer(date_pattern, cleaned):
        candidate = match.group(0).replace(",", "")

        for fmt in (
            "%d %B %Y",
            "%d %b %Y",
            "%B %d %Y",
            "%b %d %Y",
        ):
            try:
                return datetime.strptime(
                    candidate,
                    fmt,
                ).date().isoformat()
            except ValueError:
                continue

    return None
