# Cost Review Streamlit App

A lightweight Streamlit app to run monthly cost reviews locally. Capture line-item spend, track budget variance, and keep action items in one place.

## Features
- Editable cost table with automatic totals
- Budget and month-over-month variance metrics
- Category chart and top spend drivers
- Action item tracker
- CSV exports for cost lines and actions

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Usage
1. Update the review month, budget target, and prior month total in the sidebar.
2. Edit the cost table to reflect current month spend.
3. Add action items and capture a summary for stakeholders.
4. Export CSVs for reporting or sharing.

## Requirements
- Python 3.9+
- Streamlit
- pandas
- Altair
