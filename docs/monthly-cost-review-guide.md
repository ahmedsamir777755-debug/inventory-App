# Monthly Cost Review Guide (Pivot to Normalized + Anomaly Logic)

## 1) Convert Pivot-Style Table to a Normalized Table
**Goal:** Turn a cross-tab pivot table into a “long” table so each row is one GL name, one department, one month, one amount.

### Input (pivot-style)
Columns:
- GL name
- Department
- 2026/01, 2026/02, 2026/03, 2026/04, 2026/05
- Grand Total (exclude this column)

### Output (normalized)
Columns:
- GL name
- Department
- Month
- Amount

### Key rules
- **Exclude Grand Total.**
- **Blanks = zero.**
- **Parentheses = negative.** (e.g., “(1,234)” becomes -1234)

### Plain-language steps
1. **Load the pivot table into Power Query.**
2. **Remove “Grand Total.”** We don’t want to treat it like a month.
3. **Unpivot the month columns.** This converts the month columns into two columns: Month and Amount.
4. **Clean the Amount values.** Convert blanks to zero and parentheses to negatives.
5. **Keep only four columns:** GL name, Department, Month, Amount.

---

## 2) Monthly Cost Review Logic (MoM, Trends, and Anomalies)

### A. Month-over-Month (MoM) variance
For each GL + Department + Month:
- **MoM variance (value):** Current Month Amount – Prior Month Amount
- **MoM variance (%):**
  - If prior month is 0 and current month is not 0 → treat as **100%+** or flag as “New Cost.”
  - Otherwise: (Current – Prior) ÷ Prior

### B. Trend analysis
Compute a rolling baseline using the last 3 months (or as many as exist):
- **3‑month average**
- **3‑month standard deviation (optional)**

Use these to assess whether a new value is outside normal range. A basic trend summary can be:
- **Upward trend** if last 3 months are increasing or current > 3‑month average by a threshold.
- **Downward trend** if last 3 months are decreasing or current < 3‑month average by a threshold.
- **Stable** if current is within a normal band of the 3‑month average.

### C. Identification of unusual/incorrect expenses
Use rules in Section 3 to label each row with an anomaly type. That anomaly type becomes a talking point for review.

---

## 3) Anomaly Detection Rules
Apply these rules per GL name + Department + Month.

1. **Sudden spike vs last 3 months**
   - If Current > (3‑month average × 1.5) **and** absolute increase > a materiality threshold (e.g., $5,000), flag as **Spike**.
2. **New cost after zero months**
   - If last 2–3 months are 0 and current month > 0, flag as **New Cost**.
3. **Negative or reversed postings**
   - If Amount < 0, flag as **Negative/Reverse**.
4. **Unusual department for a GL account**
   - Maintain a simple mapping of “expected departments” per GL.
   - If a GL appears in a department not listed, flag as **Unusual Department**.
5. **Dormant account reactivated**
   - If last 6 months are 0 and current month > 0, flag as **Reactivation**.
6. **Volatility**
   - If Current is outside **3‑month average ± (2 × std dev)**, flag as **Volatile** (optional if you calculate std dev).

---

## 4) Power Query (M) Code for Excel
Below is a reusable Power Query template. Adjust the source step to your file name or table name.

```powerquery
let
    // 1) Load data from a table named "PivotTable" in the workbook
    Source = Excel.CurrentWorkbook(){[Name="PivotTable"]}[Content],

    // 2) Remove Grand Total column
    RemovedGrandTotal = Table.RemoveColumns(Source, {"Grand Total"}),

    // 3) Unpivot month columns (assumes GL name and Department are the only id columns)
    UnpivotedMonths = Table.UnpivotOtherColumns(
        RemovedGrandTotal,
        {"GL name", "Department"},
        "Month",
        "Amount"
    ),

    // 4) Replace blanks/nulls with zero
    ReplaceNulls = Table.ReplaceValue(
        UnpivotedMonths,
        null,
        0,
        Replacer.ReplaceValue,
        {"Amount"}
    ),

    // 5) Convert parentheses to negative and remove commas
    //    Example: (1,234) -> -1234
    CleanAmountText = Table.TransformColumns(
        ReplaceNulls,
        {{"Amount", each Text.Replace(Text.Replace(Text.From(_), ",", ""), "(", "-"), type text}}
    ),
    RemoveRightParen = Table.TransformColumns(
        CleanAmountText,
        {{"Amount", each Text.Replace(_, ")", ""), type text}}
    ),

    // 6) Convert Amount to number
    AmountAsNumber = Table.TransformColumnTypes(
        RemoveRightParen,
        {{"Amount", type number}}
    ),

    // 7) Optional: Ensure Month is date type (if month values are like 2026/01)
    // Adjust this if your month labels are different.
    MonthAsDate = Table.TransformColumns(
        AmountAsNumber,
        {{"Month", each Date.FromText(_ & "/01"), type date}}
    )

in
    MonthAsDate
```

---

## 5) Step-by-Step Explanation (Non-Technical)

1. **Load data**
   - We tell Excel to read your pivot table into Power Query so we can transform it.
2. **Remove Grand Total**
   - Grand Total is not a month, so we remove it.
3. **Unpivot months**
   - This converts columns like “2026/01, 2026/02…” into two columns: Month and Amount.
4. **Replace blanks with zero**
   - Blank cells are treated as zero costs.
5. **Fix negative values in parentheses**
   - We convert “(1,234)” into “-1234” so Excel can read it as a number.
6. **Convert Amount to number**
   - This makes sure calculations will work.
7. **Convert Month to a date**
   - This allows sorting, time intelligence, and MoM calculations.

---

## 6) Suggested Management Comments (by anomaly type)

- **Spike**
  - “Costs increased sharply vs the 3‑month average. Please confirm if this reflects a one‑time purchase, accrual, or misposting.”
- **New Cost**
  - “A new expense appeared after months of zero activity. Please confirm business reason and correct department.”
- **Negative/Reverse**
  - “Negative posting detected. Please verify if this is a valid reversal or correction.”
- **Unusual Department**
  - “GL posted to an unexpected department. Please confirm correct cost center.”
- **Reactivation**
  - “Dormant GL activity resumed after extended inactivity. Please confirm if planned.”
- **Volatile**
  - “Amount is outside normal range. Please confirm if timing or coding issues exist.”

---

## 7) Suggested Next Steps for Automation
1. Refresh the Power Query each month to load new data.
2. Add calculated columns for MoM and rolling averages in Excel or Power Pivot.
3. Use conditional formatting or a PivotChart to highlight anomalies.
4. Maintain a small reference table that maps GLs to expected departments.

---

## 8) Common Adjustments
- If month columns are not named like 2026/01, update the Month conversion logic.
- If your data is in a CSV or external file, replace the Source step accordingly.
- You can add more filters (e.g., materiality thresholds) depending on your review policy.
