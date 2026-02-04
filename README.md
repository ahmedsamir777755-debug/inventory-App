# Monthly Cost Review Streamlit App

This Streamlit application analyzes monthly cost data from an Excel file, normalizes the data, calculates variances, detects trends, and flags anomalies for review.

## Features
- Upload Excel files containing **GL name**, **Department**, and month columns (`YYYY/MM`).
- Auto-detects month columns and ignores any **Grand Total** column.
- Normalizes data into: `GL name | Department | Month | Amount`.
- Computes Month-over-Month variance, percent variance, last 3-month average, and trend.
- Detects anomalies: spikes, new costs, negative postings, and z-score outliers.
- Filters by GL name, department, and month.
- Download all outputs to an Excel file.

## Getting Started

### 1) Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Run the app
```bash
streamlit run app.py
```

## Expected Input Format
Your Excel file should contain:
- `GL name`
- `Department`
- One or more month columns formatted as `YYYY/MM` (e.g., `2024/01`, `2024/02`)
- Optional `Grand Total` column (ignored)

Blank cells are treated as `0`. Parentheses values (e.g., `(1,234)`) are parsed as negative numbers.
