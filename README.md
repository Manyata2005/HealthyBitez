# 🌱 Healthy Bitez GrowWise AI

**AI-assisted microgreens order extraction, demand analysis, and crop planning.**

Healthy Bitez GrowWise AI is a prototype designed to help a microgreens business organize customer orders, review demand, track illustrative inventory levels, and plan crop growing schedules.

## Problem

Microgreens businesses need to coordinate customer orders with crop production. Manual order handling can make it harder to identify missing order details, review demand, and plan production around delivery dates.

## Solution

GrowWise AI combines a Streamlit dashboard, local language-model integration, and explicit extraction rules to demonstrate a structured order-management workflow.

### Key Features

- **Order extraction:** Extracts crop, quantity, delivery date, customer type, delivery area, and special requests from customer messages.
- **Missing-information checks:** Flags orders that lack required details instead of automatically accepting them.
- **Duplicate-order protection:** Checks whether an order with the same message and extracted details has already been saved.
- **Demand dashboard:** Summarizes synthetic order quantities by crop.
- **Illustrative inventory:** Compares demand against example stock values.
- **Crop planning:** Calculates suggested sowing dates using configurable growing-duration assumptions.
- **Order confirmation:** Saves accepted orders to a CSV file.
- **CSV export:** Allows saved confirmed orders to be downloaded.

## Technology Stack

- Python
- Streamlit
- Pandas
- Ollama
- Qwen 2.5 1.5B
- CSV files

## Project Structure

```text
GrowWiseAI/
├── app/
│   ├── dashboard.py
│   └── order_rules.py
├── data/
│   └── processed/
│       ├── orders.csv
│       └── confirmed_orders.csv
├── scripts/
│   ├── evaluate_extraction.py
│   └── generate_data.py
└── README.md
```

## Requirements

- Python installed
- Required Python packages installed
- Ollama installed and running locally
- The configured `qwen2.5:1.5b` model downloaded
- Project data generated or provided in the expected location

## Setup

### 1. Open the project directory

```powershell
cd C:\AIProjects\GrowWiseAI
```

### 2. Install Python dependencies

If the project includes a `requirements.txt` file, run:

```powershell
python -m pip install -r requirements.txt
```

If that file is not present, install the required packages:

```powershell
python -m pip install streamlit pandas requests
```

### 3. Prepare Ollama

Make sure Ollama is running, then download the configured model if needed:

```powershell
ollama pull qwen2.5:1.5b
```

### 4. Prepare the data

If `data/processed/orders.csv` does not exist, run:

```powershell
python scripts/generate_data.py
```

Review the generated data before using it in a demonstration.

### 5. Start the dashboard

```powershell
python -m streamlit run app/dashboard.py
```

Open the local URL printed by Streamlit, usually:

```text
http://localhost:8501
```

## Running the Extraction Evaluation

Run the evaluation script:

```powershell
python scripts/evaluate_extraction.py
```

The current hand-written evaluation dataset contains 20 test messages and compares six extracted fields per message.

A previous run matched 120 out of 120 expected field values. This result measures agreement with those specific test cases; it does **not** establish 100% accuracy on unseen customer messages or measure the raw language model independently.

## Demo Workflow

1. Open the dashboard.
2. Review the Demand & Inventory tab.
3. Inspect the Crop Planner tab.
4. Enter a customer message in AI Order Extractor.
5. Review the extracted order details.
6. Confirm and save an order with all required fields.
7. Try the same message again to demonstrate duplicate protection.
8. Try a vague message to demonstrate missing-information checks.
9. Open Confirmed Orders and download the CSV.

## Limitations

- The project is a prototype, not a production order-management system.
- Example stock values and growing durations are illustrative assumptions.
- The supplied order dataset is synthetic.
- Extraction rules support a limited set of crop names, locations, and phrases.
- The current duplicate check can flag a legitimate repeat order if its message and extracted details are identical to an earlier order.
- CSV storage is suitable for a demonstration but lacks the transactional protections of a production database.
- Production use would require validation with real business data, broader testing, appropriate access controls, and a more robust order-identification strategy.

## Future Improvements

- Expand extraction coverage for more crops, quantities, locations, and natural-language variations.
- Add editable order fields so users can correct extracted information.
- Replace CSV storage with a database.
- Improve inventory calculations and production planning using validated business data.
- Add more evaluation examples and measure performance on messages not used during development.
- Add user authentication and audit history.

## Demo Data Notice

This project uses synthetic order data and illustrative operational assumptions. Results are intended for demonstration and evaluation, not as real stock measurements or production commitments.

## License

Add a license before publicly distributing or reusing this project if required.