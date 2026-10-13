import pandas as pd
from pathlib import Path
from datetime import date, timedelta

BASE_DIR = Path(__file__).resolve().parents[1]
ORDERS_FILE = BASE_DIR / "data" / "processed" / "orders.csv"

# Illustrative growing durations only; validate before real use.
GROWING_DAYS = {
    "Radish": 8,
    "Broccoli": 10,
    "Sunflower": 10,
    "Pea Shoots": 10,
    "Mustard": 8,
}


def create_crop_plan():
    if not ORDERS_FILE.exists():
        print("Orders dataset not found.")
        return

    df = pd.read_csv(ORDERS_FILE)
    today = date.today()
    rows = []

    for crop, group in df.groupby("crop"):
        days = GROWING_DAYS.get(crop)

        if days is None:
            continue

        for _, order in group.head(1).iterrows():
            delivery = date.fromisoformat(order["delivery_date"])
            sowing = delivery - timedelta(days=days)

            rows.append({
                "crop": crop,
                "delivery_date": delivery.isoformat(),
                "assumed_growing_days": days,
                "suggested_sowing_date": sowing.isoformat(),
                "sowing_status": (
                    "Sow date has passed"
                    if sowing < today
                    else "Future sowing date"
                ),
            })

    plan = pd.DataFrame(rows)
    print("\nHEALTHY BITEZ - SIMULATED CROP-CYCLE PLAN")
    print(plan.to_string(index=False))
    print("\nGrowing durations are illustrative assumptions.")


if __name__ == "__main__":
    create_crop_plan()
