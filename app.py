import datetime as dt

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Monthly Cost Review", page_icon="💸", layout="wide")

st.title("💸 Monthly Cost Review")
st.caption("Track monthly spending, spot trends, and capture action items.")


def build_default_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Category": "Cloud Infrastructure", "Owner": "Platform", "Cost": 18250.0, "Notes": "Compute + storage"},
            {"Category": "SaaS Subscriptions", "Owner": "IT", "Cost": 6450.0, "Notes": "Renewals due next month"},
            {"Category": "Data Tools", "Owner": "Analytics", "Cost": 5230.0, "Notes": "Warehouse + BI"},
            {"Category": "Marketing", "Owner": "Growth", "Cost": 11890.0, "Notes": "Campaign spend"},
            {"Category": "Customer Support", "Owner": "CX", "Cost": 4100.0, "Notes": "Seat expansion"},
        ]
    )


if "cost_data" not in st.session_state:
    st.session_state.cost_data = build_default_data()

if "actions" not in st.session_state:
    st.session_state.actions = [
        {
            "Action": "Rightsize unused cloud instances",
            "Owner": "Platform",
            "Status": "In progress",
            "Target Month": dt.date.today().strftime("%B"),
        }
    ]


with st.sidebar:
    st.header("Review Settings")
    review_month = st.date_input("Review month", dt.date.today().replace(day=1))
    budget_target = st.number_input("Budget target ($)", min_value=0.0, value=50000.0, step=1000.0)
    prior_month_total = st.number_input("Prior month total ($)", min_value=0.0, value=42000.0, step=500.0)
    st.divider()
    st.write("Adjust costs directly in the table to refresh the dashboard.")

st.subheader(f"Cost summary for {review_month.strftime('%B %Y')}")

edited_data = st.data_editor(
    st.session_state.cost_data,
    num_rows="dynamic",
    use_container_width=True,
    key="cost_editor",
    column_config={
        "Cost": st.column_config.NumberColumn(format="$%.2f"),
    },
)

cost_data = pd.DataFrame(edited_data)
if not cost_data.empty:
    cost_data["Cost"] = pd.to_numeric(cost_data["Cost"], errors="coerce").fillna(0.0)

st.session_state.cost_data = cost_data

current_total = cost_data["Cost"].sum()
variance = current_total - budget_target
variance_pct = (variance / budget_target * 100) if budget_target else 0
mom_change = current_total - prior_month_total
mom_pct = (mom_change / prior_month_total * 100) if prior_month_total else 0

kpi_cols = st.columns(4)
kpi_cols[0].metric("Current total", f"${current_total:,.0f}")
kpi_cols[1].metric("Budget variance", f"${variance:,.0f}", f"{variance_pct:.1f}%")
kpi_cols[2].metric("MoM change", f"${mom_change:,.0f}", f"{mom_pct:.1f}%")
kpi_cols[3].metric("Line items", len(cost_data))

chart_cols = st.columns((2, 1))

with chart_cols[0]:
    st.markdown("#### Spend by category")
    if cost_data.empty:
        st.info("Add cost line items to see charts.")
    else:
        bar_chart = (
            alt.Chart(cost_data)
            .mark_bar(color="#4C78A8")
            .encode(x=alt.X("Category", sort="-y"), y=alt.Y("Cost", axis=alt.Axis(format="$,.0f")))
            .properties(height=320)
        )
        st.altair_chart(bar_chart, use_container_width=True)

with chart_cols[1]:
    st.markdown("#### Top drivers")
    if cost_data.empty:
        st.write("No data yet.")
    else:
        top = cost_data.sort_values("Cost", ascending=False).head(3)
        for _, row in top.iterrows():
            st.write(f"**{row['Category']}** — ${row['Cost']:,.0f}")
            if row.get("Notes"):
                st.caption(row["Notes"])

st.divider()

st.subheader("Action items")
actions_df = pd.DataFrame(st.session_state.actions)
new_actions = st.data_editor(
    actions_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            options=["Not started", "In progress", "Done"],
            required=True,
        )
    },
)

st.session_state.actions = new_actions.to_dict(orient="records")

notes_col, export_col = st.columns((2, 1))
with notes_col:
    st.markdown("#### Key takeaways")
    summary = st.text_area(
        "Summarize wins, risks, and next steps",
        placeholder="Example: Cloud spend rose 8% due to analytics workload. Marketing savings expected next month.",
    )

with export_col:
    st.markdown("#### Export")
    csv = cost_data.to_csv(index=False).encode("utf-8")
    st.download_button("Download cost CSV", csv, file_name="monthly_costs.csv", mime="text/csv")
    actions_csv = pd.DataFrame(st.session_state.actions).to_csv(index=False).encode("utf-8")
    st.download_button("Download actions CSV", actions_csv, file_name="cost_actions.csv", mime="text/csv")

st.divider()

st.markdown("#### Notes for next review")
if summary:
    st.success("Summary captured. Share this with the finance team.")
    st.write(summary)
else:
    st.info("Add a summary above to capture review notes.")
