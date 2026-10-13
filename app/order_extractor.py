
import json
import requests
from datetime import date

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:1.5b"


def extract_order(message: str) -> dict:
    prompt = f"""
Extract order details from this customer message.
Return only a JSON object with these keys:
crop, quantity_g, delivery_date, customer_type,
delivery_area, special_request.

Rules:
- crop: crop name, or null if unknown.
- quantity_g: numeric quantity in grams, or null if unknown.
- delivery_date: YYYY-MM-DD, or null if unknown.
- customer_type: household, cafe, retailer, or unknown.
- delivery_area: location stated, or null if unknown.
- special_request: stated request, or null if none.
- Do not invent missing details.
- Today's date is {date.today().isoformat()}.
- Resolve "tomorrow" relative to today's date.

Customer message: {message}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "format": "json",
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()

    result = json.loads(response.json()["response"])

    keys = [
        "crop",
        "quantity_g",
        "delivery_date",
        "customer_type",
        "delivery_area",
        "special_request",
    ]
    return {key: result.get(key) for key in keys}


if __name__ == "__main__":
    message = (
        "Please deliver 500 g of radish microgreens "
        "to my cafe in Anekal tomorrow."
    )

    try:
        print(json.dumps(extract_order(message), indent=2))
    except requests.RequestException as error:
        print("Ollama connection error:", error)
    except (ValueError, json.JSONDecodeError) as error:
        print("Could not parse AI response:", error)