import sys
from pathlib import Path
from datetime import date, timedelta

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "app"))

from order_rules import (
    extract_explicit_crop,
    extract_explicit_quantity,
    extract_explicit_date,
    extract_explicit_customer_type,
    extract_explicit_area,
    extract_explicit_special_request,
)

FIELDS = [
    "crop",
    "quantity_g",
    "delivery_date",
    "customer_type",
    "delivery_area",
    "special_request",
]

TEST_CASES = [
    ("Deliver 500 g of radish microgreens to my cafe in Anekal tomorrow.",
     {"crop": "Radish", "quantity_g": 500, "delivery_date": "tomorrow",
      "customer_type": "cafe", "delivery_area": "Anekal", "special_request": None}),
    ("Our household needs 100 grams of broccoli in Bengaluru.",
     {"crop": "Broccoli", "quantity_g": 100, "delivery_date": None,
      "customer_type": "household", "delivery_area": "Bengaluru", "special_request": None}),
    ("A retailer wants 250 g of sunflower microgreens in HSR Layout.",
     {"crop": "Sunflower", "quantity_g": 250, "delivery_date": None,
      "customer_type": "retailer", "delivery_area": "HSR Layout", "special_request": None}),
    ("Please send 150 g of mustard microgreens to my cafe.",
     {"crop": "Mustard", "quantity_g": 150, "delivery_date": None,
      "customer_type": "cafe", "delivery_area": None, "special_request": None}),
    ("We need 200 grams of pea shoots for our household.",
     {"crop": "Pea Shoots", "quantity_g": 200, "delivery_date": None,
      "customer_type": "household", "delivery_area": None, "special_request": None}),
    ("Send 75 g radish microgreens to my home in Anekal tomorrow morning.",
     {"crop": "Radish", "quantity_g": 75, "delivery_date": "tomorrow",
      "customer_type": "household", "delivery_area": "Anekal", "special_request": "morning delivery"}),
    ("Cafe order: 1 kg broccoli microgreens, deliver to Bengaluru on 20 October 2026.",
     {"crop": "Broccoli", "quantity_g": 1000, "delivery_date": "2026-10-20",
      "customer_type": "cafe", "delivery_area": "Bengaluru", "special_request": None}),
    ("Please pack 300 grams of sunflower shoots separately for our retailer in HSR Layout.",
     {"crop": "Sunflower", "quantity_g": 300, "delivery_date": None,
      "customer_type": "retailer", "delivery_area": "HSR Layout", "special_request": "separate packaging"}),
    ("I want radish microgreens.",
     {"crop": "Radish", "quantity_g": None, "delivery_date": None,
      "customer_type": None, "delivery_area": None, "special_request": None}),
    ("Deliver 2 kg of pea shoots to my cafe in Anekal on 25 October 2026.",
     {"crop": "Pea Shoots", "quantity_g": 2000, "delivery_date": "2026-10-25",
      "customer_type": "cafe", "delivery_area": "Anekal", "special_request": None}),
    ("Our retail shop needs 125 g mustard microgreens, freshly packed.",
     {"crop": "Mustard", "quantity_g": 125, "delivery_date": None,
      "customer_type": "retailer", "delivery_area": None, "special_request": "freshly packed"}),
    ("Can you supply 400 g of broccoli to my household in Electronic City by 30 October 2026?",
     {"crop": "Broccoli", "quantity_g": 400, "delivery_date": "2026-10-30",
      "customer_type": "household", "delivery_area": "Electronic City", "special_request": None}),
    ("Need 50 grams of radish microgreens for a cafe. Morning delivery, please.",
     {"crop": "Radish", "quantity_g": 50, "delivery_date": None,
      "customer_type": "cafe", "delivery_area": None, "special_request": "morning delivery"}),
    ("Please deliver 600 g of pea shoots to our retailer in Bengaluru tomorrow.",
     {"crop": "Pea Shoots", "quantity_g": 600, "delivery_date": "tomorrow",
      "customer_type": "retailer", "delivery_area": "Bengaluru", "special_request": None}),
    ("We need 350 g sunflower microgreens in Anekal, packed separately.",
     {"crop": "Sunflower", "quantity_g": 350, "delivery_date": None,
      "customer_type": None, "delivery_area": "Anekal", "special_request": "separate packaging"}),
    ("Order 90 g of mustard for my home in Bengaluru.",
     {"crop": "Mustard", "quantity_g": 90, "delivery_date": None,
      "customer_type": "household", "delivery_area": "Bengaluru", "special_request": None}),
    ("Cafe in Electronic City needs 750 grams of broccoli microgreens for 28 October 2026.",
     {"crop": "Broccoli", "quantity_g": 750, "delivery_date": "2026-10-28",
      "customer_type": "cafe", "delivery_area": "Electronic City", "special_request": None}),
    ("Can I get some fresh microgreens delivered?",
     {"crop": None, "quantity_g": None, "delivery_date": None,
      "customer_type": None, "delivery_area": None, "special_request": None}),
    ("Send 220 g of pea shoots to our cafe in Anekal, separate packaging, on 29 October 2026.",
     {"crop": "Pea Shoots", "quantity_g": 220, "delivery_date": "2026-10-29",
      "customer_type": "cafe", "delivery_area": "Anekal", "special_request": "separate packaging"}),
    ("Retailer order: 180 grams of radish microgreens in HSR Layout, freshly packed, delivery 31 October 2026.",
     {"crop": "Radish", "quantity_g": 180, "delivery_date": "2026-10-31",
      "customer_type": "retailer", "delivery_area": "HSR Layout", "special_request": "freshly packed"}),
]


def extract_using_rules(message):
    return {
        "crop": extract_explicit_crop(message),
        "quantity_g": extract_explicit_quantity(message),
        "delivery_date": extract_explicit_date(message),
        "customer_type": extract_explicit_customer_type(message),
        "delivery_area": extract_explicit_area(message),
        "special_request": extract_explicit_special_request(message),
    }


def resolve_expected(value):
    if value == "tomorrow":
        return (date.today() + timedelta(days=1)).isoformat()
    return value


def main():
    total = 0
    matched = 0
    perfect_cases = 0

    print("HEALTHY BITEZ - EXTRACTION RULE EVALUATION")
    print("=" * 55)

    for index, (message, expected) in enumerate(TEST_CASES, start=1):
        actual = extract_using_rules(message)
        case_matches = 0
        differences = []

        for field in FIELDS:
            total += 1
            expected_value = resolve_expected(expected[field])
            if actual[field] == expected_value:
                matched += 1
                case_matches += 1
            else:
                differences.append(
                    f"{field}: expected={expected_value!r}, got={actual[field]!r}"
                )

        if case_matches == len(FIELDS):
            perfect_cases += 1

        print(f"Test {index:02}: {case_matches}/{len(FIELDS)} fields matched")
        for difference in differences:
            print("  " + difference)

    print("\n" + "=" * 55)
    print(f"Field-level accuracy: {matched / total * 100:.1f}% ({matched}/{total})")
    print(f"Entire cases correct: {perfect_cases}/{len(TEST_CASES)}")
    print("This tests deterministic rules on a small hand-written dataset.")
    print("It does not measure raw AI model accuracy.")


if __name__ == "__main__":
    main()