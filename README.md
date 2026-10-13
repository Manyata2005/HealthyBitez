# 🌱 Healthy Bitez GrowWise AI

**AI-assisted microgreens order extraction, demand analysis, and crop planning.**

Healthy Bitez GrowWise AI is a prototype that helps a microgreens business organize customer orders, review demand, explore illustrative inventory levels, and plan crop-growing schedules. It combines a Streamlit dashboard, a local language model, and deterministic extraction rules.

## Problem

Microgreens businesses need to coordinate customer orders with crop production. Manual order handling can make it difficult to identify missing information, understand demand by crop, and plan production around delivery dates.

## Solution

GrowWise AI demonstrates an AI-assisted workflow for extracting order details, checking required information, validating delivery areas, reviewing demand, and saving confirmed orders.

## Key Features

- **AI-assisted order extraction:** Uses Ollama with the `qwen2.5:1.5b` model as part of the extraction workflow.
- **Structured order details:** Extracts crop, quantity, delivery date, customer type, delivery area, and special requests using explicit rules.
- **Missing-information checks:** Flags orders with missing required fields.
- **Approved delivery-area validation:** Blocks confirmation when the delivery area is missing or is not in the configured approved-area list.
- **Duplicate-order protection:** Checks for an already-saved order with the same customer message and extracted details.
- **Demand dashboard:** Summarizes synthetic order quantities by crop.
- **Illustrative inventory analysis:** Compares demand with configured example stock values.
- **Crop planner:** Suggests sowing dates using configured growing-duration assumptions.
- **Order confirmation:** Saves accepted orders to a CSV file.
- **CSV export:** Displays saved confirmed orders and allows them to be downloaded.

## Technology Stack

- Python
- Streamlit
- Pandas
- Requests
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
│       └── confirmed_orders.csv  # Created locally when orders are saved
├── scripts/
│   ├── evaluate_extraction.py
│   └── generate_data.py
├── tests/
├── .gitignore
└── README.md
```

## Setup and Installation

These commands use PowerShell on Windows and assume the project is located at `C:\AIProjects\GrowWiseAI`.

### 1. Open the project directory

```powershell
Set-Location "C:\AIProjects\GrowWiseAI"
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is blocked by PowerShell, use the Python executable inside `.venv` directly or follow your system's approved PowerShell policy.

### 3. Install Python dependencies

This project currently does not include a `requirements.txt` file. Install the packages used by the application:

```powershell
python -m pip install --upgrade pip
python -m pip install streamlit pandas requests
```

### 4. Start Ollama and download the model

Make sure Ollama is installed and running, then run:

```powershell
ollama pull qwen2.5:1.5b
```

The application expects Ollama's local generation API at:

```text
http://localhost:11434/api/generate
```

### 5. Prepare the order dataset

If `data/processed/orders.csv` does not exist, generate the synthetic dataset:

```powershell
python scripts/generate_data.py
```

Review the generated data before using it in a demonstration.

### 6. Run the dashboard

```powershell
python -m streamlit run app/dashboard.py
```

Open the local URL printed by Streamlit, usually:

```text
http://localhost:8501
```

## Using the Application

1. **Demand & Inventory:** Review demand by crop and compare it with illustrative stock values.
2. **Crop Planner:** Inspect suggested sowing dates calculated from delivery dates and configured growing durations.
3. **AI Order Extractor:** Enter a customer message and review the extracted order details.
4. **Validate the order:** Provide all required information and use an approved delivery area.
5. **Confirm and save:** Confirm a valid order to save it to `data/processed/confirmed_orders.csv`.
6. **Confirmed Orders:** Review saved records and download the CSV.

## Delivery-Area Validation

Delivery areas are checked against the configured list in `app/order_rules.py`.

The current example list is:

- Electronic City
- HSR Layout
- Bengaluru
- Anekal

Only add areas that the business intends to support. Unknown or missing areas should not be confirmed. This configured list is an allowlist; it is not a live map lookup or proof of actual delivery coverage.

## Running the Extraction Evaluation

Run:

```powershell
python scripts/evaluate_extraction.py
```

The hand-written evaluation dataset contains 20 test messages and compares six extracted fields per message.

A previous run matched **120 out of 120 expected field values across 20 cases**. This measures agreement with those specific test cases; it does not establish 100% accuracy on unseen customer messages or independently measure the raw language model.

## Demo Workflow

1. Open the dashboard.
2. Review the Demand & Inventory tab.
3. Inspect the Crop Planner tab.
4. Submit a complete order for an approved area, such as Anekal.
5. Review the extracted fields and confirm the order.
6. Submit the same message again to demonstrate duplicate protection.
7. Try an unsupported area, such as `Hello`, to demonstrate blocked confirmation.
8. Submit an incomplete message to demonstrate missing-information checks.
9. Open Confirmed Orders and download the CSV.

Use synthetic data for the demonstration and verify results on the current version before presenting them.

## Limitations

- This is a prototype, not a production order-management system.
- The supplied order dataset is synthetic.
- Stock values and growing durations are illustrative assumptions, not real measurements.
- Extraction rules support a limited set of crop names, locations, and phrases.
- The approved-area list does not verify real-world geography.
- The duplicate check can flag a legitimate repeat order if its message and extracted details are identical to an earlier order.
- CSV storage does not provide the transactional safeguards of a production database.
- The evaluation dataset is small and hand-written.

Production use would require broader testing, validated business data, suitable access controls, reliable order identification, and more robust storage.

## Future Improvements

- Expand extraction coverage for more crops, quantities, locations, and natural-language variations.
- Allow users to correct extracted fields before confirmation.
- Add automated tests for validation, duplicate handling, and saving.
- Expand evaluation with messages not used during development.
- Replace CSV storage with a database.
- Improve inventory calculations using validated business data.
- Add authentication, authorization, and audit history.

## Demo Data Notice

This project uses synthetic order data and illustrative operational assumptions. Its outputs are intended for demonstration and evaluation, not as real stock measurements or production commitments.

## License

No license is specified here. Add an appropriate license before publicly distributing or authorizing reuse of the project.