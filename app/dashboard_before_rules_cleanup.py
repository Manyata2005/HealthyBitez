
import json
import re
import uuid
import requests
import pandas as pd
import streamlit as st

from order_rules import (
    extract_explicit_crop,
    extract_explicit_quantity,
    extract_explicit_date,
    extract_explicit_customer_type,
    extract_explicit_area,
    extract_explicit_special_request,
)

from pathlib import Path
from datetime import date, datetime, timedelta


# ---------------- CONFIGURATION ----------------

BASE = Path(__file__).resolve().parents[1]

ORDERS = BASE / "data" / "processed" / "orders.csv"
CONFIRMED_ORDERS = (
    BASE / "data" / "processed" / "confirmed_orders.csv"
)

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

CUSTOMER_TYPES = {"household", "cafe", "retailer"}

ORDER_FIELDS = [
    "crop",
    "quantity_g",
    "delivery_date",
    "customer_type",
    "delivery_area",
    "special_request",
]


# ---------------- HELPER FUNCTIONS ----------------

def extract_explicit_crop(message):
    text = message.lower()

    for crop, aliases in CROP_ALIASES.items():
        for alias in aliases:
            if re.search(
                r"\b" + re.escape(alias) + r"\b",
                text,
            ):
                return crop

    return None


def extract_explicit_quantity(message):
    pattern = (
        r"\b(\d+(?:\.\d+)?)\s*"
        r"(kg|kilograms?|g|grams?)\b"
    )

    match = re.search(pattern, message.lower())

    if not match:
        return None

    amount = float(match.group(1))
    unit = match.group(2)

    if unit.startswith("kg") or unit.startswith("kilogram"):
        amount *= 1000

    if amount <= 0:
        return None

    if amount.is_integer():
        return int(amount)

    return amount


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


def extract_explicit_area(message):
    text = message.lower()

    for area in AREAS:
        if re.search(
            r"\b" + re.escape(area.lower()) + r"\b",
            text,
        ):
            return area

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

    # An explicit ISO date, such as 2026-10-20.
    iso_match = re.search(
        r"\b\d{4}-\d{2}-\d{2}\b",
        text,
    )

    if iso_match:
        try:
            return date.fromisoformat(
                iso_match.group(0)
            ).isoformat()
        except ValueError:
            return None

    # Dates such as 20 October 2026 or October 20, 2026.
    cleaned = re.sub(
        r"(\d{1,2})(st|nd|rd|th)\b",
        r"\1",
        text,
    )

    formats = [
        "%d %B %Y",
        "%d %b %Y",
        "%B %d %Y",
        "%b %d %Y",
    ]

    for fmt in formats:
        for match in re.finditer(
            r"\b(?:\d{1,2}\s+)?"
            r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|"
            r"apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
            r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
            r"nov(?:ember)?|dec(?:ember)?)"
            r"\s+\d{1,2}(?:,)?\s+\d{4}\b|"
            r"\b\d{1,2}\s+"
            r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|"
            r"apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
            r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
            r"nov(?:ember)?|dec(?:ember)?)"
            r"\s+\d{4}\b",
            cleaned,
        ):
            candidate = match.group(0).replace(",", "")
            try:
                return datetime.strptime(
                    candidate,
                    fmt,
                ).date().isoformat()
            except ValueError:
                continue

    return None


def extract_order_with_ai(message):
    prompt = f"""
Today's date is {date.today().isoformat()}.

Extract customer order details from this message.
Return JSON with exactly these keys:
crop, quantity_g, delivery_date, customer_type,
delivery_area, special_request.

Use null for missing information.
Do not invent details.
Return numeric quantities in grams.
Return dates as YYYY-MM-DD.
Return JSON only.

Customer message:
{message}
"""

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

    model_result = json.loads(
        response.json()["response"]
    )

    # Deterministic extraction from the original message
    # overrides unsupported model guesses.
    return {
        "crop": extract_explicit_crop(message),
        "quantity_g": extract_explicit_quantity(message),
        "delivery_date": extract_explicit_date(message),
        "customer_type": extract_explicit_customer_type(message),
        "delivery_area": extract_explicit_area(message),
        "special_request": extract_explicit_special_request(message),
    }


# ---------------- PAGE SETUP ----------------

st.set_page_config(
    page_title="Healthy Bitez GrowWise AI",
    page_icon="🌱",
    layout="wide",
)

st.title("🌱 Healthy Bitez GrowWise AI")
st.caption("AI-assisted microgreens order and production planning")

st.warning(
    "DEMO MODE: Orders are synthetic. Stock values and growing "
    "durations are illustrative assumptions, not real measurements."
)


# ---------------- LOAD DATA ----------------

if not ORDERS.exists():
    st.error(f"Dataset not found: {ORDERS}")
    st.info("Generate it with: python scripts\\generate_data.py")
    st.stop()

df = pd.read_csv(ORDERS)

required_columns = {"crop", "quantity_g", "delivery_date"}

if not required_columns.issubset(df.columns):
    st.error("orders.csv is missing required columns.")
    st.stop()

df["quantity_g"] = pd.to_numeric(
    df["quantity_g"],
    errors="coerce",
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


# ---------------- TABS ----------------

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Demand & Inventory",
        "Crop Planner",
        "AI Order Extractor",
        "Confirmed Orders",
    ]
)


# ---------------- TAB 1: DEMAND ----------------

with tab1:
    st.subheader("Demand by crop")

    st.bar_chart(
        demand.set_index("crop")["demand_g"]
    )

    st.dataframe(
        demand,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Demand comes from synthetic order records. "
        "Stock values are simulated."
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
            delivery = date.fromisoformat(
                str(row["delivery_date"])
            )
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
        "Growing durations are assumptions. Validate them "
        "against your varieties and growing conditions."
    )


# ---------------- TAB 3: AI ORDER EXTRACTOR ----------------

with tab3:
    st.subheader("Extract an order from a customer message")

    message = st.text_area(
        "Customer message",
        "Please deliver 500 g of radish microgreens "
        "to my cafe in Anekal tomorrow.",
        key="customer_message",
    )

    if st.button("Extract order with AI", type="primary"):
        if not message.strip():
            st.warning("Please enter a customer message.")
        else:
            try:
                with st.spinner("Extracting order details..."):
                    result = extract_order_with_ai(message)

                # Save the pending order across Streamlit reruns.
                st.session_state["pending_order"] = result
                st.session_state["pending_message"] = message
                st.session_state["pending_order_id"] = str(uuid.uuid4())
                st.session_state["pending_saved"] = False

            except requests.RequestException as error:
                st.error(
                    f"Could not connect to Ollama: {error}"
                )
            except (ValueError, KeyError, TypeError) as error:
                st.error(
                    f"Could not process the AI response: {error}"
                )

    pending = st.session_state.get("pending_order")

    if pending is not None:
        st.subheader("Extracted order")
        st.json(pending)

        required = [
            "crop",
            "quantity_g",
            "delivery_date",
            "customer_type",
        ]

        missing = [
            field for field in required
            if pending.get(field) is None
        ]

        if missing:
            st.warning(
                "Order needs confirmation. Missing information: "
                + ", ".join(missing)
            )
            st.info(
                "Please obtain the missing details from the customer "
                "before accepting this order."
            )
        else:
            st.success(
                "Required fields are present. Review the order "
                "before accepting it."
            )

            with st.expander("Review order details", expanded=True):
                st.write("**Crop:**", pending["crop"])
                st.write("**Quantity:**", f'{pending["quantity_g"]} g')
                st.write("**Delivery date:**", pending["delivery_date"])
                st.write("**Customer type:**", pending["customer_type"])
                st.write("**Delivery area:**", pending["delivery_area"] or "Not provided")
                st.write("**Special request:**", pending["special_request"] or "None")

            if st.session_state.get("pending_saved"):
                st.success("This order has already been saved.")
            elif st.button("Confirm and save order", type="primary"):
                try:
                    CONFIRMED_ORDERS.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    order_record = {
                        "order_id": st.session_state["pending_order_id"],
                        "created_at": datetime.now().isoformat(
                            timespec="seconds"
                        ),
                        "customer_message": st.session_state.get(
                            "pending_message", ""
                        ),
                        **pending,
                    }

                    new_order = pd.DataFrame([order_record])

                    if CONFIRMED_ORDERS.exists():
                        existing = pd.read_csv(
                            CONFIRMED_ORDERS
                        )

                        # Avoid saving the same pending order twice.
                        if (
                            "order_id" in existing.columns
                            and order_record["order_id"]
                            in existing["order_id"].astype(str).values
                        ):
                            st.session_state["pending_saved"] = True
                            st.success("This order is already saved.")
                        else:
                            updated = pd.concat(
                                [existing, new_order],
                                ignore_index=True,
                            )
                            updated.to_csv(
                                CONFIRMED_ORDERS,
                                index=False,
                            )
                            st.session_state["pending_saved"] = True
                            st.success("Order saved successfully!")
                    else:
                        new_order.to_csv(
                            CONFIRMED_ORDERS,
                            index=False,
                        )
                        st.session_state["pending_saved"] = True
                        st.success("Order saved successfully!")

                    st.caption(
                        "Saved to data/processed/confirmed_orders.csv"
                    )

                except (OSError, PermissionError, pd.errors.ParserError) as error:
                    st.error(f"Could not save the order: {error}")


# ---------------- TAB 4: CONFIRMED ORDERS ----------------

with tab4:
    st.subheader("Saved confirmed orders")

    if CONFIRMED_ORDERS.exists():
        try:
            saved_orders = pd.read_csv(CONFIRMED_ORDERS)

            if saved_orders.empty:
                st.info("No confirmed orders have been saved yet.")
            else:
                st.metric("Saved orders", len(saved_orders))

                st.dataframe(
                    saved_orders,
                    use_container_width=True,
                    hide_index=True,
                )

                csv_data = saved_orders.to_csv(
                    index=False
                ).encode("utf-8")

                st.download_button(
                    "Download confirmed orders CSV",
                    data=csv_data,
                    file_name="confirmed_orders.csv",
                    mime="text/csv",
                )

        except (OSError, pd.errors.ParserError) as error:
            st.error(f"Could not read saved orders: {error}")
    else:
        st.info(
            "No confirmed orders yet. Extract and confirm a valid "
            "order in the AI Order Extractor tab."
        )
