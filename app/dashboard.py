
import json
import uuid
from pathlib import Path
from datetime import date, datetime, timedelta

import pandas as pd
import requests
import streamlit as st

from order_rules import (
    extract_explicit_crop,
    extract_explicit_quantity,
    extract_explicit_date,
    extract_explicit_customer_type,
    extract_explicit_area,
    extract_explicit_special_request,
    validate_delivery_area,
    APPROVED_DELIVERY_AREAS,
)


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

ORDER_FIELDS = [
    "crop",
    "quantity_g",
    "delivery_date",
    "customer_type",
    "delivery_area",
    "special_request",
]

REQUIRED_FIELDS = [
    "crop",
    "quantity_g",
    "delivery_date",
    "customer_type",
]


# ---------------- ORDER EXTRACTION ----------------

def extract_order_with_ai(message):
    """Validate the AI response and extract explicit order details."""

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

    # Verify that Ollama returned valid JSON.
    json.loads(response.json()["response"])

    # Use the shared rules to determine displayed values.
    return {
        "crop": extract_explicit_crop(message),
        "quantity_g": extract_explicit_quantity(message),
        "delivery_date": extract_explicit_date(message),
        "customer_type": extract_explicit_customer_type(message),
        "delivery_area": extract_explicit_area(message),
        "special_request": extract_explicit_special_request(message),
    }


# ---------------- DUPLICATE PROTECTION ----------------

def clean_value(value):
    """Normalize values for comparing saved CSV fields."""

    if pd.isna(value):
        return ""

    return str(value).strip().casefold()


def order_already_saved(message, order):
    """Check whether the same message and order details are saved."""

    if not CONFIRMED_ORDERS.exists():
        return False

    try:
        saved = pd.read_csv(
            CONFIRMED_ORDERS,
            keep_default_na=False,
        )
    except pd.errors.EmptyDataError:
        return False

    if saved.empty:
        return False

    comparison_fields = ["customer_message"] + ORDER_FIELDS

    if not all(field in saved.columns for field in comparison_fields):
        return False

    for _, row in saved.iterrows():
        same_message = (
            clean_value(row["customer_message"])
            == clean_value(message)
        )

        same_details = all(
            clean_value(row[field]) == clean_value(order.get(field))
            for field in ORDER_FIELDS
        )

        if same_message and same_details:
            return True

    return False


def save_confirmed_order(message, order, order_id):
    """Save an order only if it is complete and its area is approved."""

    # Enforce validation again at the saving boundary.
    # This prevents unsupported areas from being saved accidentally.
    approved_area = validate_delivery_area(
        order.get("delivery_area")
    )

    if approved_area is None:
        raise ValueError(
            "Cannot save this order: its delivery area is missing "
            "or is not on the approved delivery-area list."
        )

    missing = [
        field
        for field in REQUIRED_FIELDS
        if order.get(field) is None or order.get(field) == ""
    ]

    if missing:
        raise ValueError(
            "Cannot save this order. Missing required fields: "
            + ", ".join(missing)
        )

    # Save the standard spelling of the approved area.
    order_to_save = dict(order)
    order_to_save["delivery_area"] = approved_area

    CONFIRMED_ORDERS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if order_already_saved(message, order_to_save):
        return False

    record = {
        "order_id": order_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "customer_message": message,
        **order_to_save,
    }

    new_order = pd.DataFrame([record])

    if CONFIRMED_ORDERS.exists():
        try:
            existing = pd.read_csv(
                CONFIRMED_ORDERS,
                keep_default_na=False,
            )
        except pd.errors.EmptyDataError:
            existing = pd.DataFrame()

        updated = pd.concat(
            [existing, new_order],
            ignore_index=True,
        )
    else:
        updated = new_order

    updated.to_csv(CONFIRMED_ORDERS, index=False)
    return True


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
    st.info("Generate it with: python scripts/generate_data.py")
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

    st.bar_chart(demand.set_index("crop")["demand_g"])

    st.dataframe(
        demand,
        width="stretch",
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
        except (ValueError, TypeError):
            continue

        sowing = delivery - timedelta(days=days)

        schedules.append(
            {
                "crop": crop,
                "example_delivery_date": delivery.isoformat(),
                "assumed_growing_days": days,
                "suggested_sowing_date": sowing.isoformat(),
                "schedule_status": (
                    "Past date - review"
                    if sowing < date.today()
                    else "Future date"
                ),
            }
        )

    if schedules:
        st.dataframe(
            pd.DataFrame(schedules),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No valid crop schedule could be generated.")

    st.caption(
        "Growing durations are assumptions. Validate them "
        "against your varieties and growing conditions."
    )


# ---------------- TAB 3: ORDER EXTRACTOR ----------------

with tab3:
    st.subheader("Extract an order from a customer message")

    st.caption(
        "Orders can only be confirmed for approved delivery areas: "
        + ", ".join(APPROVED_DELIVERY_AREAS)
    )

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

                previous_message = st.session_state.get(
                    "pending_message"
                )

                previous_order = st.session_state.get(
                    "pending_order"
                )

                previous_id = st.session_state.get(
                    "pending_order_id"
                )

                previous_saved = st.session_state.get(
                    "pending_saved",
                    False,
                )

                # Reuse the order ID when the same message and
                # extracted details are submitted again.
                if (
                    previous_message == message
                    and previous_order == result
                    and previous_id
                ):
                    st.session_state["pending_order_id"] = previous_id
                    st.session_state["pending_saved"] = previous_saved
                else:
                    st.session_state["pending_order_id"] = str(
                        uuid.uuid4()
                    )
                    st.session_state["pending_saved"] = False

                st.session_state["pending_order"] = result
                st.session_state["pending_message"] = message

            except requests.RequestException as error:
                st.error(f"Could not connect to Ollama: {error}")

            except (ValueError, KeyError, TypeError) as error:
                st.error(f"Could not process the AI response: {error}")

    pending = st.session_state.get("pending_order")

    if pending is not None:
        st.subheader("Extracted order")

        # Friendly summary instead of displaying raw JSON.
        with st.container(border=True):
            st.markdown("#### Order details")

            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    "**Crop**",
                    pending.get("crop") or "Not provided",
                )

                quantity = pending.get("quantity_g")
                st.write(
                    "**Quantity**",
                    f"{quantity} g"
                    if quantity not in (None, "")
                    else "Not provided",
                )

                st.write(
                    "**Delivery date**",
                    pending.get("delivery_date") or "Not provided",
                )

            with col2:
                st.write(
                    "**Customer type**",
                    pending.get("customer_type") or "Not provided",
                )

                st.write(
                    "**Delivery area**",
                    pending.get("delivery_area") or "Not provided",
                )

                st.write(
                    "**Special request**",
                    pending.get("special_request") or "None",
                )

        missing = [
            field
            for field in REQUIRED_FIELDS
            if pending.get(field) is None or pending.get(field) == ""
        ]

        # Validate the area against the approved list.
        raw_area = pending.get("delivery_area")
        approved_area = validate_delivery_area(raw_area)
        area_is_valid = approved_area is not None

        if area_is_valid:
            pending["delivery_area"] = approved_area

        if missing:
            st.warning(
                "Order needs more information. Missing fields: "
                + ", ".join(missing)
            )

            st.info(
                "Obtain the missing details from the customer "
                "before accepting this order."
            )

        if not area_is_valid:
            st.error(
                "Delivery area is missing or unsupported. "
                "Confirmation is disabled. Approved areas: "
                + ", ".join(APPROVED_DELIVERY_AREAS)
            )

        if not missing and area_is_valid:
            st.success(
                "Required fields are present and the delivery area "
                "is approved. Review the order before accepting it."
            )

        with st.expander("Review order details", expanded=True):
            st.write("**Crop:**", pending.get("crop") or "Not provided")

            quantity = pending.get("quantity_g")
            st.write(
                "**Quantity:**",
                f"{quantity} g"
                if quantity not in (None, "")
                else "Not provided",
            )

            st.write(
                "**Delivery date:**",
                pending.get("delivery_date") or "Not provided",
            )

            st.write(
                "**Customer type:**",
                pending.get("customer_type") or "Not provided",
            )

            st.write(
                "**Delivery area:**",
                pending.get("delivery_area") or "Not provided",
            )

            st.write(
                "**Special request:**",
                pending.get("special_request") or "None",
            )

        if st.session_state.get("pending_saved"):
            st.success("This order has already been processed.")

        elif not area_is_valid:
            st.button(
                "Confirm and save order",
                type="primary",
                disabled=True,
                key="confirm_invalid_area",
            )

        elif missing:
            st.button(
                "Confirm and save order",
                type="primary",
                disabled=True,
                key="confirm_missing_fields",
            )

        elif st.button(
            "Confirm and save order",
            type="primary",
            key="confirm_valid_order",
        ):
            try:
                saved = save_confirmed_order(
                    st.session_state["pending_message"],
                    pending,
                    st.session_state["pending_order_id"],
                )

                # Prevent repeated confirmation clicks.
                st.session_state["pending_saved"] = True

                if saved:
                    st.success("Order saved successfully!")
                else:
                    st.info(
                        "This order is already saved. "
                        "No duplicate was added."
                    )

                st.caption(
                    "Saved to data/processed/confirmed_orders.csv"
                )

            except (
                OSError,
                PermissionError,
                pd.errors.ParserError,
                ValueError,
            ) as error:
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
                    width="stretch",
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
