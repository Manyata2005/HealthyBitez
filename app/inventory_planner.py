import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
ORDERS_FILE = BASE_DIR / "data" / "processed" / "orders.csv"

# Demonstration values only; not actual Healthy Bitez stock.
SIMULATED_STOCK_G = {
    "Mustard": 6000,
    "Sunflower": 7000,
    "Pea Shoots": 5000,
    "Broccoli": 4000,
    "Radish": 5000,
}


def create_inventory_plan():
    if not ORDERS_FILE.exists():
        print("orders.csv not found. Generate the dataset first.")
        return

    df = pd.read_csv(ORDERS_FILE)
    df["quantity_g"] = pd.to_numeric(
        df["quantity_g"], errors="coerce"
    )
    df = df.dropna(subset=["crop", "quantity_g"])

    demand = df.groupby("crop")["quantity_g"].sum()
    rows = []

    for crop, total_demand in demand.items():
        stock = SIMULATED_STOCK_G.get(crop, 0)
        shortage = max(0, int(total_demand) - stock)
        surplus = max(0, stock - int(total_demand))

        rows.append({
            "crop": crop,
            "demand_g": int(total_demand),
            "simulated_stock_g": stock,
            "shortage_g": shortage,
            "surplus_g": surplus,
            "status": "SHORTAGE" if shortage > 0 else "Stock covers demand",
        })

    plan = pd.DataFrame(rows).sort_values(
        "shortage_g", ascending=False
    )

    print("\nHEALTHY BITEZ - DEMONSTRATION INVENTORY PLAN")
    print("=" * 70)
    print(plan.to_string(index=False))
    print("\nWARNING: Stock values are simulated examples, not real inventory.")


if __name__ == "__main__":
    create_inventory_plan()
