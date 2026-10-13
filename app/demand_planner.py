
import pandas as pd
from pathlib import Path

DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "data" / "processed" / "orders.csv"
)


def create_demand_plan():
    if not DATA_FILE.exists():
        print(f"Dataset not found: {DATA_FILE}")
        print("Please generate orders.csv first.")
        return

    df = pd.read_csv(DATA_FILE)

    df["quantity_g"] = pd.to_numeric(
        df["quantity_g"], errors="coerce"
    )
    df = df.dropna(subset=["crop", "quantity_g"])

    demand = (
        df.groupby("crop")
        .agg(
            order_count=("quantity_g", "count"),
            total_demand_g=("quantity_g", "sum"),
        )
        .reset_index()
        .sort_values("total_demand_g", ascending=False)
    )

    print("\nHEALTHY BITEZ — SIMULATED DEMAND PLAN")
    print("=" * 45)
    print(demand.to_string(index=False))
    print("\nThese are simulated orders, not actual sales.")
    print("Stock levels and crop yields are not measured yet.")


if __name__ == "__main__":
    create_demand_plan()