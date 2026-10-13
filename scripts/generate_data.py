
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

CROPS = ["Radish", "Broccoli", "Sunflower", "Pea Shoots", "Mustard"]
CUSTOMERS = ["Household", "Cafe", "Retailer"]
AREAS = ["Anekal", "Electronic City", "HSR Layout", "Bengaluru"]
QUANTITIES = [50, 100, 150, 200, 250, 500, 1000]

TEMPLATES = [
    "Please deliver {quantity}g of {crop} microgreens on {day}.",
    "We need {quantity} grams of {crop} for our order due {day}.",
    "Hi, order {quantity}g {crop} microgreens for {day}.",
    "Can you supply {quantity}g of {crop} microgreens by {day}?",
]

today = date.today()
rows = []

for i in range(120):
    crop = random.choice(CROPS)
    quantity = random.choice(QUANTITIES)
    delivery_date = today + timedelta(days=random.randint(1, 14))

    rows.append({
        "order_id": f"SIM-{i + 1:03d}",
        "message": random.choice(TEMPLATES).format(
            quantity=quantity,
            crop=crop,
            day=delivery_date.strftime("%d %b %Y"),
        ),
        "crop": crop,
        "quantity_g": quantity,
        "delivery_date": delivery_date.isoformat(),
        "customer_type": random.choice(CUSTOMERS),
        "delivery_area": random.choice(AREAS),
        "special_request": random.choice([
            "None", "Freshly packed",
            "Morning delivery", "Separate packaging"
        ]),
        "data_type": "synthetic",
    })

output = (
    Path(__file__).resolve().parents[1]
    / "data" / "processed" / "orders.csv"
)
output.parent.mkdir(parents=True, exist_ok=True)

with output.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Created {len(rows)} simulated orders.")
print(f"Saved to: {output}")
print("These are simulated orders, not actual Healthy Bitez sales.")