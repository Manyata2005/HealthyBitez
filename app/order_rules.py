import re
from datetime import date, datetime, timedelta

CROP_ALIASES = {
    "Radish": ["radish"],
    "Broccoli": ["broccoli"],
    "Sunflower": ["sunflower"],
    "Pea Shoots": ["pea shoots", "pea shoot"],
    "Mustard": ["mustard"],
}

AREAS = [
    "Electronic City",
    "HSR Layout",
    "Bengaluru",
    "Anekal",
]


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

    if re.search(r"\bretailer\b|\bretail shop\b|\bretail store\b", text):
        return "retailer"

    if re.search(
        r"\bhousehold\b|\bmy home\b|\bour home\b|"
        r"\bmy family\b|\bfor my home\b",
        text,
    ):
        return "household"

    return None


def extract_explicit_area(message):
    text = message.lower()
    for area in AREAS:
        if re.search(r"\b" + re.escape(area.lower()) + r"\b", text):
            return area
    return None


def extract_explicit_special_request(message):
    text = message.lower()

    if re.search(r"\bmorning\b", text):
        return "morning delivery"

    if "separate packaging" in text or re.search(r"\bseparately\b", text):
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

    cleaned = re.sub(r"(\d{1,2})(st|nd|rd|th)\b", r"\1", text)

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
        for fmt in ("%d %B %Y", "%d %b %Y", "%B %d %Y", "%b %d %Y"):
            try:
                return datetime.strptime(candidate, fmt).date().isoformat()
            except ValueError:
                continue

    return None