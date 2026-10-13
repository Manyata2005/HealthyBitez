
import json
import re
import requests
import pandas as pd
import streamlit as st

from pathlib import Path
from datetime import date, timedelta

BASE = Path(__file__).resolve().parents[1]
ORDERS = BASE / "data" / "processed" / "orders.csv"

MODEL = "qwen2.5:1.5b"
OLLAMA_URL = "http://localhost:11434/api/generate"

STOCK = {
    "Mustard": 6000,
    "Sunflower": 7000,
    "Pea Shoots": 5000,
    "Broccoli": 4000,
    "Radish": 5000,
}

GROWING_DAYS = {
    "Radish": 8,
    "Broccoli": 10,
    "Sunflower": 10,
    "Pea Shoots": 10,
    "Mustard": 8,
}

ALLOWED_CUSTOMER_TYPES = {"household", "cafe", "retailer"}

st.set_page_config(
    page_title="Healthy Bitez GrowWise AI",
    page_icon="🌱",
    layout="wide",
)

st.title("🌱 Healthy Bitez GrowWise AI")
st.caption("AI-assisted microgreens order and production planning")

st.warning(
    "DEMO MODE: Orders are synthetic. Stock levels and growing "
    "durations are illustrative assumptions, not real measurements."
)

if not ORDERS.exists():
    st.error(f"Dataset not found: {ORDERS}")
    st.info("Generate it with: python scripts\\generate_data.py")
    st.stop()

# ---------------- DEMAND DATA ----------------

df = pd.read_csv(ORDERS)

required_columns = {"crop", "quantity_g", "delivery_date"}
if not required_columns.issubset(df.columns):
    st.error("orders.csv is missing required columns.")
    st.stop()

df["quantity_g"] = pd.to_numeric(
    df["quantity_g"], errors="coerce"
)
df = df.dropna(subset=["crop", "quantity_g"])

demand = (
    df.groupby("crop")["quantity_g"]
    .agg(order_count="count", demand_g="sum")
    .reset_index()
)

demand["simulated_stock_g"] = (
    demand["crop"].map(STOCK).fillna(0).astype(int)
)

demand["shortage_g"] = (
    demand["demand_g"] - demand["simulated_stock_g"]
).clip(lower=0).astype(int)

# ---------------- SUMMARY ----------------

c1, c2, c3 = st.columns(3)

c1.metric("Synthetic orders", len(df))
c2.metric("Crop varieties", df["crop"].nunique())
c3.metric(
    "Crops with simulated shortages",
    int((demand["shortage_g"] > 0).sum()),
)

tab1, tab2, tab3 = st.tabs(
    ["Demand & Inventory", "Crop Planner", "AI Order Extractor"]
)

# ---------------- TAB 1: DEMAND ----------------

with tab1:
    st.subheader("Demand by crop")
    st.bar_chart(demand.set_index("crop")["demand_g"])
    st.dataframe(demand, use_container_width=True, hide_index=True)

    st.caption(
        "Demand comes from synthetic orders. Stock figures are "
        "demonstration values and do not represent actual inventory."
    )

# ---------------- TAB 2: CROP PLANNER ----------------

with tab2:
    st.subheader("Illustrative crop-cycle schedule")

    schedules = []

    for _, row in df.drop_duplicates("crop").iterrows():
        crop = str(row["crop"])
        days = GROWING_DAYS.get(crop)

        if days is None or pd.isna(row["delivery_date"]):
            continue

        try:
            delivery = date.fromisoformat(str(row["delivery_date"]))
        except ValueError:
            continue

        sowing = delivery - timedelta(days=days)

        schedules.append({
            "crop": crop,
            "example_delivery_date": delivery.isoformat(),
            "assumed_growing_days": days,
            "suggested_sowing_date": sowing.isoformat(),
            "schedule_status": (
                "Past date - review"
                if sowing < date.today()
                else "Future date"
            ),
        })

    if schedules:
        st.dataframe(
            pd.DataFrame(schedules),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No valid crop schedule could be generated.")

    st.caption(
        "Growing durations are assumptions. Validate them for your "
        "microgreens varieties and actual growing conditions."
    )

# ---------------- TAB 3: AI ORDER EXTRACTOR ----------------

with tab3:
    st.subheader("Extract an order from a customer message")

    message = st.text_area(
        "Customer message",
        "Please deliver 500 g of radish microgreens "
        "to my cafe in Anekal tomorrow.",
    )

    if st.button("Extract order with AI", type="primary"):

        prompt = f"""
Today's date is {date.today().isoformat()}.

Extract these fields as JSON:
crop, quantity_g, delivery_date, customer_type,
delivery_area, special_request.

Strict rules:
- Use JSON null for missing or uncertain fields.
- Never invent a crop, quantity, date, location, or request.
- "Some microgreens" is not a specific crop.
- Only use crop names explicitly mentioned.
- Quantity must be a positive number in grams.
- Convert kilograms to grams: 1 kg = 1000 g.
- Dates must be YYYY-MM-DD.
- Resolve "tomorrow" relative to today's date.
- customer_type must be household, cafe, retailer, or null.
- "my cafe", "our cafe", or "cafe order" mean cafe.
- "my home" or "our household" mean household.
- "retail shop" or "retailer order" mean retailer.
- Only return a special request if explicitly stated.
- Return actual JSON null, not the string "null".
- Return JSON only without Markdown.

Customer message:
{message}
"""

        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                },
                timeout=180,
            )
            response.raise_for_status()

            result = json.loads(response.json()["response"])

            # Keep only supported fields.
            fields = [
                "crop",
                "quantity_g",
                "delivery_date",
                "customer_type",
                "delivery_area",
                "special_request",
            ]

            result = {
                field: result.get(field)
                for field in fields
            }

            # Normalize missing values.
            for key, value in result.items():
                if isinstance(value, str):
                    value = value.strip()
                    if value.lower() in {"", "null", "none", "unknown"}:
                        value = None
                    result[key] = value

            text = message.lower()

            # Require an explicitly stated known crop.
            crop_aliases = {
                "radish": ["radish"],
                "broccoli": ["broccoli"],
                "sunflower": ["sunflower"],
                "pea shoots": ["pea shoots", "pea shoot"],
                "mustard": ["mustard"],
            }

            matched_crop = None

            for canonical, aliases in crop_aliases.items():
                if any(alias in text for alias in aliases):
                    matched_crop = canonical
                    break

            if matched_crop is None:
                result["crop"] = None
            elif result["crop"] is None:
                result["crop"] = matched_crop
            else:
                result["crop"] = matched_crop

            # Require a quantity and unit in the original message.
            quantity_pattern = (
                r"\b(\d+(?:\.\d+)?)\s*"
                r"(g|gram|grams|kg|kilogram|kilograms)\b"
            )

            quantity_match = re.search(quantity_pattern, text)

            if quantity_match is None:
                result["quantity_g"] = None
            else:
                amount = float(quantity_match.group(1))
                unit = quantity_match.group(2)

                if unit in {"kg", "kilogram", "kilograms"}:
                    amount *= 1000

                if amount <= 0:
                    result["quantity_g"] = None
                elif amount.is_integer():
                    result["quantity_g"] = int(amount)
                else:
                    result["quantity_g"] = amount

            # Infer customer type only from explicit phrases.
            if "cafe" in text or "café" in text:
                result["customer_type"] = "cafe"
            elif any(
                phrase in text
                for phrase in [
                    "retailer",
                    "retail shop",
                    "retail store",
                ]
            ):
                result["customer_type"] = "retailer"
            elif any(
                phrase in text
                for phrase in [
                    "household",
                    "my home",
                    "our home",
                    "my family",
                ]
            ):
                result["customer_type"] = "household"
            else:
                result["customer_type"] = None

            # Require an explicit supported date expression.
            tomorrow_pattern = r"\btomorrow\b"
            today_pattern = r"\btoday\b"
            iso_pattern = r"\b\d{4}-\d{2}-\d{2}\b"
            named_date_pattern = (
                r"\b\d{1,2}\s+"
                r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
                r"[a-z]*\s+\d{4}\b"
            )
            month_first_pattern = (
                r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
                r"[a-z]*\s+\d{1,2},?\s+\d{4}\b"
            )

            has_date = any(
                re.search(pattern, text)
                for pattern in [
                    tomorrow_pattern,
                    today_pattern,
                    iso_pattern,
                    named_date_pattern,
                    month_first_pattern,
                ]
            )

            if not has_date:
                result["delivery_date"] = None
            else:
                # Calculate relative dates ourselves.
                if re.search(tomorrow_pattern, text):
                    result["delivery_date"] = (
                        date.today() + timedelta(days=1)
                    ).isoformat()
                elif re.search(today_pattern, text):
                    result["delivery_date"] = date.today().isoformat()
                else:
                    candidate = result["delivery_date"]

                    # Validate any date returned by the model.
                    try:
                        date.fromisoformat(str(candidate))
                    except (ValueError, TypeError):
                        result["delivery_date"] = None

            # Only retain a delivery area if its name appears
            # in the original message.
            known_areas = [
                "Anekal",
                "Electronic City",
                "HSR Layout",
                "Bengaluru",
            ]

            matched_area = next(
                (
                    area for area in known_areas
                    if area.lower() in text
                ),
                None,
            )

            result["delivery_area"] = matched_area

            # Keep special requests only when there is evidence.
            if "morning" in text:
                result["special_request"] = "morning delivery"
            elif "separate packaging" in text or "separately" in text:
                result["special_request"] = "separate packaging"
            elif "freshly packed" in text:
                result["special_request"] = "freshly packed"
            else:
                result["special_request"] = None

            st.subheader("Extracted order")
            st.json(result)

            required = [
                "crop",
                "quantity_g",
                "delivery_date",
                "customer_type",
            ]

            missing = [
                field for field in required
                if result[field] is None
            ]

            if missing:
                st.warning(
                    "Order needs confirmation. Missing or unverified: "
                    + ", ".join(missing)
                )
            else:
                st.success(
                    "Required fields are present. Review the order "
                    "before accepting it."
                )

        except requests.RequestException as error:
            st.error(f"Could not connect to Ollama: {error}")
        except (ValueError, KeyError, TypeError) as error:
            st.error(f"Could not process the AI response: {error}")
