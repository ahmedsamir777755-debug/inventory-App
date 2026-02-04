import io
import re

import numpy as np
import pandas as pd
import streamlit as st


MONTH_PATTERN = re.compile(r"^\d{4}/\d{2}$")


def clean_amount(value: object) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float, np.number)):
        return float(value)
    text = str(value).strip()
    if text == "":
        return 0.0
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]
    text = text.replace(",", "").replace("$", "")
    try:
        number = float(text)
    except ValueError:
        return 0.0
    return -number if negative else number


def detect_month_columns(columns: pd.Index) -> list[str]:
    month_cols = []
    for col in columns:
        name = str(col).strip()
        if MONTH_PATTERN.match(name):
            month_cols.append(col)
    return month_cols


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    columns = list(df.columns)
    month_cols = detect_month_columns(columns)
    non_month_cols = [
        col
        for col in columns
        if col not in month_cols and "grand total" not in str(col).lower()
    ]
    normalized = df.melt(
        id_vars=non_month_cols,
        value_vars=month_cols,
        var_name="Month",
        value_name="Amount",
    )
    normalized["Amount"] = normalized["Amount"].apply(clean_amount)
    normalized["Month"] = pd.to_datetime(
        normalized["Month"].astype(str), format="%Y/%m", errors="coerce"
    )
    normalized = normalized.rename(
        columns={
            non_month_cols[0]: "GL name",
            non_month_cols[1]: "Department",
        }
    )
    normalized = normalized[["GL name", "Department", "Month", "Amount"]]
    normalized["Month"] = normalized["Month"].dt.strftime("%Y/%m")
    return normalized


def variance_analysis(normalized: pd.DataFrame) -> pd.DataFrame:
    data = normalized.copy()
    data["Month_dt"] = pd.to_datetime(data["Month"], format="%Y/%m")
    data = data.sort_values(["GL name", "Department", "Month_dt"])
    grouped = data.groupby(["GL name", "Department"], sort=False)
    data["Previous Amount"] = grouped["Amount"].shift(1)
    data["MoM Variance"] = data["Amount"] - data["Previous Amount"]
    data["MoM Variance %"] = np.where(
        data["Previous Amount"].replace(0, np.nan).notna(),
        data["MoM Variance"] / data["Previous Amount"].replace(0, np.nan),
        np.nan,
    )
    data["Last 3 Mo Avg"] = (
        grouped["Amount"].rolling(3, min_periods=1).mean().reset_index(level=[0, 1], drop=True)
    )
    increase = data["Amount"] > data["Last 3 Mo Avg"] * 1.05
    decrease = data["Amount"] < data["Last 3 Mo Avg"] * 0.95
    data["Trend"] = np.select(
        [increase, decrease], ["Increase", "Decrease"], default="Stable"
    )
    return data.drop(columns=["Month_dt"])


def build_anomaly_log(analysis: pd.DataFrame) -> pd.DataFrame:
    data = analysis.copy()
    data["Month_dt"] = pd.to_datetime(data["Month"], format="%Y/%m")
    data = data.sort_values(["GL name", "Department", "Month_dt"])
    grouped = data.groupby(["GL name", "Department"], sort=False)
    data["Prev 3 Mo Avg"] = (
        grouped["Amount"]
        .apply(lambda s: s.shift(1).rolling(3, min_periods=3).mean())
        .reset_index(level=[0, 1], drop=True)
    )
    data["Prev 3 Mo Sum"] = (
        grouped["Amount"]
        .apply(lambda s: s.shift(1).rolling(3, min_periods=3).sum())
        .reset_index(level=[0, 1], drop=True)
    )
    data["Group Mean"] = grouped["Amount"].transform("mean")
    data["Group Std"] = grouped["Amount"].transform("std").replace(0, np.nan)
    data["Z Score"] = (data["Amount"] - data["Group Mean"]) / data["Group Std"]

    anomalies = []

    spike_mask = data["Prev 3 Mo Avg"].notna() & (
        data["Amount"] > data["Prev 3 Mo Avg"] * 1.3
    )
    spike = data[spike_mask]
    if not spike.empty:
        spike = spike.assign(
            Reason="Sudden spike >30% vs last 3 months",
            **{"Suggested action": "Review driver and validate one-time expense."},
        )
        anomalies.append(spike)

    new_cost_mask = (
        data["Prev 3 Mo Sum"].notna()
        & (data["Prev 3 Mo Sum"] == 0)
        & (data["Amount"] > 0)
    )
    new_cost = data[new_cost_mask]
    if not new_cost.empty:
        new_cost = new_cost.assign(
            Reason="New costs after zero months",
            **{"Suggested action": "Confirm new recurring cost or correct mapping."},
        )
        anomalies.append(new_cost)

    negative_mask = data["Amount"] < 0
    negative = data[negative_mask]
    if not negative.empty:
        negative = negative.assign(
            Reason="Negative posting detected",
            **{"Suggested action": "Verify credit memo or adjustment entry."},
        )
        anomalies.append(negative)

    outlier_mask = data["Z Score"].abs() > 2.5
    outlier = data[outlier_mask]
    if not outlier.empty:
        outlier = outlier.assign(
            Reason="Outlier detected (z-score)",
            **{"Suggested action": "Investigate unusual variance vs baseline."},
        )
        anomalies.append(outlier)

    if not anomalies:
        return pd.DataFrame(
            columns=[
                "GL name",
                "Department",
                "Month",
                "Amount",
                "Reason",
                "Suggested action",
            ]
        )

    anomaly_log = pd.concat(anomalies, ignore_index=True)
    return anomaly_log[
        ["GL name", "Department", "Month", "Amount", "Reason", "Suggested action"]
    ].drop_duplicates()


def build_summary(analysis: pd.DataFrame, anomalies: pd.DataFrame) -> dict[str, pd.DataFrame]:
    summary_metrics = pd.DataFrame(
        {
            "Metric": [
                "Total spend",
                "Average MoM variance",
                "Total anomalies",
            ],
            "Value": [
                analysis["Amount"].sum(),
                analysis["MoM Variance"].mean(),
                anomalies.shape[0],
            ],
        }
    )
    top_variances = (
        analysis.sort_values("MoM Variance", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    return {
        "metrics": summary_metrics,
        "top_variances": top_variances,
    }


def build_excel_download(
    normalized: pd.DataFrame,
    analysis: pd.DataFrame,
    anomalies: pd.DataFrame,
    summary: dict[str, pd.DataFrame],
) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        normalized.to_excel(writer, sheet_name="Normalized Data", index=False)
        analysis.to_excel(writer, sheet_name="Variance Analysis", index=False)
        anomalies.to_excel(writer, sheet_name="Anomaly Log", index=False)
        summary["metrics"].to_excel(writer, sheet_name="Summary Metrics", index=False)
        summary["top_variances"].to_excel(writer, sheet_name="Top Variances", index=False)
    return output.getvalue()


st.set_page_config(page_title="Monthly Cost Review", layout="wide")
st.title("Monthly Cost Review")
st.write(
    "Upload a monthly cost Excel file to review trends, variances, and anomalies."
)

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

if uploaded_file:
    raw_df = pd.read_excel(uploaded_file)
    normalized_df = normalize_data(raw_df)
    analysis_df = variance_analysis(normalized_df)
    anomalies_df = build_anomaly_log(analysis_df)
    summary_outputs = build_summary(analysis_df, anomalies_df)

    gl_options = sorted(normalized_df["GL name"].dropna().unique())
    dept_options = sorted(normalized_df["Department"].dropna().unique())
    month_options = sorted(normalized_df["Month"].dropna().unique())

    with st.expander("Filters", expanded=True):
        selected_gl = st.multiselect("GL name", gl_options, default=gl_options)
        selected_dept = st.multiselect("Department", dept_options, default=dept_options)
        selected_month = st.multiselect("Month", month_options, default=month_options)

    filter_mask = (
        normalized_df["GL name"].isin(selected_gl)
        & normalized_df["Department"].isin(selected_dept)
        & normalized_df["Month"].isin(selected_month)
    )
    filtered_normalized = normalized_df[filter_mask]
    filtered_analysis = analysis_df[filter_mask]
    filtered_anomalies = anomalies_df[
        anomalies_df["GL name"].isin(selected_gl)
        & anomalies_df["Department"].isin(selected_dept)
        & anomalies_df["Month"].isin(selected_month)
    ]

    tabs = st.tabs(
        ["Normalized Data", "Variance Analysis", "Anomaly Log", "Summary"]
    )

    with tabs[0]:
        st.subheader("Normalized Data")
        st.dataframe(filtered_normalized, use_container_width=True)

    with tabs[1]:
        st.subheader("Variance Analysis")
        st.dataframe(filtered_analysis, use_container_width=True)

    with tabs[2]:
        st.subheader("Anomaly Log")
        st.dataframe(filtered_anomalies, use_container_width=True)

    with tabs[3]:
        st.subheader("Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Total Spend",
            f"{summary_outputs['metrics'].loc[0, 'Value']:,.2f}",
        )
        col2.metric(
            "Avg MoM Variance",
            f"{summary_outputs['metrics'].loc[1, 'Value']:,.2f}",
        )
        col3.metric(
            "Total Anomalies",
            int(summary_outputs["metrics"].loc[2, "Value"]),
        )
        st.subheader("Top Variances")
        st.dataframe(summary_outputs["top_variances"], use_container_width=True)

    download_bytes = build_excel_download(
        filtered_normalized,
        filtered_analysis,
        filtered_anomalies,
        summary_outputs,
    )
    st.download_button(
        "Download Excel Outputs",
        data=download_bytes,
        file_name="monthly_cost_review_outputs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.info("Upload an Excel file to begin the monthly cost review.")
