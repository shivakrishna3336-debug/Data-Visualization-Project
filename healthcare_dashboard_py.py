import io

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Healthcare Data Storytelling Dashboard",
    page_icon="🏥",
    layout="wide"
)

REQUIRED_COLUMNS = [
    "Visit Date",
    "Patient ID",
    "Age",
    "Gender",
    "Department",
    "Visit Type",
    "Diagnosis Group",
    "Treatment",
    "Length of Stay (Days)",
    "Outcome",
    "Bill Amount (INR)"
]


# =========================================================
# 2. SYNTHETIC HEALTHCARE SAMPLE DATA
# =========================================================
@st.cache_data
def load_sample_data():
    """Generate fictional educational healthcare visit records."""

    rng = np.random.default_rng(42)
    row_count = 900

    departments = [
        "Cardiology",
        "Neurology",
        "Orthopedics",
        "General Medicine",
        "Pediatrics",
        "Dermatology"
    ]

    diagnosis_groups = [
        "Heart Disease",
        "Diabetes",
        "Fever",
        "Fracture",
        "Respiratory Disease",
        "Neurological Disorder"
    ]

    treatments = [
        "Medication",
        "Surgery",
        "Physiotherapy",
        "Diagnostic Test",
        "Observation",
        "Counselling"
    ]

    visit_dates = rng.choice(
        pd.date_range("2024-01-02", "2026-12-31", freq="D"),
        size=row_count
    )

    patient_numbers = rng.integers(1, 351, size=row_count)

    sample = pd.DataFrame({
        "Visit Date": visit_dates,
        "Patient ID": [f"P{number:04d}" for number in patient_numbers],
        "Age": rng.integers(1, 100, size=row_count),
        "Gender": rng.choice(
            ["Male", "Female", "Other"],
            size=row_count,
            p=[0.49, 0.49, 0.02]
        ),
        "Department": rng.choice(departments, size=row_count),
        "Visit Type": rng.choice(
            ["Inpatient", "Outpatient"],
            size=row_count,
            p=[0.35, 0.65]
        ),
        "Diagnosis Group": rng.choice(diagnosis_groups, size=row_count),
        "Treatment": rng.choice(treatments, size=row_count),
        "Length of Stay (Days)": rng.integers(0, 16, size=row_count),
        "Outcome": rng.choice(
            ["Recovered", "Under Treatment", "Referred", "Discharged"],
            size=row_count,
            p=[0.35, 0.25, 0.10, 0.30]
        ),
        "Bill Amount (INR)": rng.integers(500, 50001, size=row_count)
    })

    return sample


# =========================================================
# 3. DATA VALIDATION AND PREPARATION
# =========================================================
def prepare_data(raw_data):
    df = raw_data.copy()
    df.columns = df.columns.astype(str).str.strip()

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing_columns)
        )

    df["Visit Date"] = pd.to_datetime(
        df["Visit Date"],
        errors="coerce"
    )

    numeric_columns = [
        "Age",
        "Length of Stay (Days)",
        "Bill Amount (INR)"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=REQUIRED_COLUMNS).copy()

    df = df[
        (df["Age"] >= 0)
        & (df["Age"] <= 110)
        & (df["Length of Stay (Days)"] >= 0)
        & (df["Bill Amount (INR)"] >= 0)
    ].copy()

    if df.empty:
        raise ValueError(
            "No valid healthcare records remain after data cleaning."
        )

    df["Age Group"] = pd.cut(
        df["Age"],
        bins=[-1, 17, 35, 55, 75, 110],
        labels=["0–17", "18–35", "36–55", "56–75", "76+"]
    )

    df["Visit Month"] = (
        df["Visit Date"].dt.to_period("M").dt.to_timestamp()
    )

    return df


# =========================================================
# 4. HELPER FUNCTIONS
# =========================================================
def inr(value):
    return f"₹{value:,.0f}"


def make_excel_report(data, summary, monthly, department_summary,
                      treatment_summary):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        data.to_excel(
            writer,
            index=False,
            sheet_name="Filtered Visits"
        )
        summary.to_excel(
            writer,
            index=False,
            sheet_name="KPI Summary"
        )
        monthly.to_excel(
            writer,
            index=False,
            sheet_name="Monthly Trends"
        )
        department_summary.to_excel(
            writer,
            index=False,
            sheet_name="Departments"
        )
        treatment_summary.to_excel(
            writer,
            index=False,
            sheet_name="Treatments"
        )

    output.seek(0)
    return output.getvalue()


def make_pdf_report(data, monthly, department_summary, treatment_summary):
    output = io.BytesIO()

    total_visits = len(data)
    unique_patients = data["Patient ID"].nunique()
    average_age = data["Age"].mean()
    average_stay = data["Length of Stay (Days)"].mean()
    total_bill = data["Bill Amount (INR)"].sum()

    with PdfPages(output) as pdf:
        # Page 1: Executive overview
        fig = plt.figure(figsize=(11.7, 8.3))
        fig.suptitle(
            "Healthcare Data Storytelling - Summary Report",
            fontsize=17,
            fontweight="bold"
        )

        lines = [
            "Synthetic educational dataset - not real patient records.",
            f"Filtered visits: {total_visits:,}",
            f"Unique sample patients: {unique_patients:,}",
            f"Average age: {average_age:.1f} years",
            f"Average length of stay: {average_stay:.1f} days",
            f"Total recorded bill amount: {inr(total_bill)}",
            (
                "Selected date range: "
                f"{data['Visit Date'].min():%d %b %Y} to "
                f"{data['Visit Date'].max():%d %b %Y}"
            ),
            "",
            "Interpretation: These summaries describe only selected",
            "synthetic records. They do not measure quality of care,",
            "prove treatment effectiveness, or provide medical advice."
        ]

        fig.text(
            0.08, 0.82, "\n".join(lines),
            va="top", fontsize=12, linespacing=1.7
        )
        plt.axis("off")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # Page 2: Monthly visits
        fig, ax = plt.subplots(figsize=(11, 6))
        if not monthly.empty:
            ax.plot(
                monthly["Visit Month"],
                monthly["Visits"],
                marker="o",
                label="Visits"
            )
            ax.set_title("Monthly Hospital Visits")
            ax.set_xlabel("Month")
            ax.set_ylabel("Visit count")
            ax.tick_params(axis="x", rotation=35)
            ax.legend()
            ax.grid(True, alpha=0.25)
        fig.tight_layout()
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # Page 3: Department comparison
        fig, ax = plt.subplots(figsize=(11, 6))
        if not department_summary.empty:
            ax.bar(
                department_summary["Department"],
                department_summary["Visits"]
            )
            ax.set_title("Visits by Department")
            ax.set_ylabel("Visit count")
            ax.tick_params(axis="x", rotation=25)
        fig.tight_layout()
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # Page 4: Treatment comparison
        fig, ax = plt.subplots(figsize=(11, 6))
        if not treatment_summary.empty:
            ordered = treatment_summary.sort_values("Visits")
            ax.barh(ordered["Treatment"], ordered["Visits"])
            ax.set_title("Visits by Recorded Treatment")
            ax.set_xlabel("Visit count")
        fig.tight_layout()
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    output.seek(0)
    return output.getvalue()


# =========================================================
# 5. DASHBOARD HEADER
# =========================================================
st.title("🏥 Healthcare Data Storytelling Dashboard")
st.caption(
    "B.Tech Mini Project | Python • Streamlit • Pandas • Plotly"
)

st.warning(
    "Privacy and safety: The built-in dataset contains fictional sample "
    "records and IDs. Do not upload identifiable patient records. "
    "This academic dashboard is not a clinical decision tool and does "
    "not provide medical advice."
)


# =========================================================
# 6. SIDEBAR: DATA UPLOAD AND FILTERS
# =========================================================
with st.sidebar:
    st.header("Data & Filters")

    uploaded_file = st.file_uploader(
        "Upload healthcare CSV",
        type=["csv"]
    )

    try:
        if uploaded_file is not None:
            raw_data = pd.read_csv(uploaded_file)
            data_source = "Uploaded CSV"
        else:
            raw_data = load_sample_data()
            data_source = "Generated synthetic sample"

        all_data = prepare_data(raw_data)

    except Exception as error:
        st.error(f"Could not load data: {error}")
        st.markdown(
            "**Required columns:** " + ", ".join(REQUIRED_COLUMNS)
        )
        st.stop()

    st.caption(
        f"Source: {data_source} | Valid visits: {len(all_data):,}"
    )

    minimum_date = all_data["Visit Date"].min().date()
    maximum_date = all_data["Visit Date"].max().date()

    selected_dates = st.date_input(
        "Visit date range",
        value=(minimum_date, maximum_date),
        min_value=minimum_date,
        max_value=maximum_date
    )

    selected_departments = st.multiselect(
        "Department",
        options=sorted(all_data["Department"].unique()),
        default=sorted(all_data["Department"].unique())
    )

    selected_visit_types = st.multiselect(
        "Visit type",
        options=sorted(all_data["Visit Type"].unique()),
        default=sorted(all_data["Visit Type"].unique())
    )

    selected_outcomes = st.multiselect(
        "Outcome",
        options=sorted(all_data["Outcome"].unique()),
        default=sorted(all_data["Outcome"].unique())
    )


# =========================================================
# 7. APPLY FILTERS
# =========================================================
if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
elif isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 1:
    start_date = end_date = selected_dates[0]
else:
    start_date = end_date = selected_dates

if start_date > end_date:
    start_date, end_date = end_date, start_date

df = all_data[
    (all_data["Visit Date"].dt.date >= start_date)
    & (all_data["Visit Date"].dt.date <= end_date)
    & (all_data["Department"].isin(selected_departments))
    & (all_data["Visit Type"].isin(selected_visit_types))
    & (all_data["Outcome"].isin(selected_outcomes))
].copy()

if df.empty:
    st.warning(
        "No records match the selected filters. "
        "Change the filters in the sidebar."
    )
    st.stop()


# =========================================================
# 8. KEY PERFORMANCE INDICATORS
# =========================================================
total_visits = len(df)
unique_patients = df["Patient ID"].nunique()
average_age = df["Age"].mean()
average_stay = df["Length of Stay (Days)"].mean()
total_bill = df["Bill Amount (INR)"].sum()
average_bill = df["Bill Amount (INR)"].mean()

st.subheader("The healthcare story")
st.markdown(
    "**How many visits are recorded, how are hospital services used, "
    "and what patterns appear across departments and treatments?**"
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Visits", f"{total_visits:,}")
k2.metric("Unique Sample Patients", f"{unique_patients:,}")
k3.metric("Average Age", f"{average_age:.1f} years")
k4.metric("Average Stay", f"{average_stay:.1f} days")
k5.metric("Recorded Bill Total", inr(total_bill))

st.caption(
    f"Selected period: {start_date:%d %b %Y} - {end_date:%d %b %Y} | "
    f"Average recorded bill: {inr(average_bill)}. "
    "Repeated patient IDs represent multiple visits in this sample, "
    "not necessarily readmissions."
)


# =========================================================
# 9. SHARED DATA SUMMARIES
# =========================================================
monthly = (
    df.groupby("Visit Month", as_index=False)
    .agg(
        Visits=("Patient ID", "size"),
        Unique_Patients=("Patient ID", "nunique"),
        Average_Stay=("Length of Stay (Days)", "mean"),
        Bill_Total=("Bill Amount (INR)", "sum")
    )
)

department_summary = (
    df.groupby("Department", as_index=False)
    .agg(
        Visits=("Patient ID", "size"),
        Unique_Patients=("Patient ID", "nunique"),
        Average_Stay=("Length of Stay (Days)", "mean"),
        Bill_Total=("Bill Amount (INR)", "sum")
    )
)

treatment_summary = (
    df.groupby("Treatment", as_index=False)
    .agg(
        Visits=("Patient ID", "size"),
        Average_Stay=("Length of Stay (Days)", "mean"),
        Average_Bill=("Bill Amount (INR)", "mean")
    )
)

diagnosis_summary = (
    df.groupby("Diagnosis Group", as_index=False)
    .agg(
        Visits=("Patient ID", "size"),
        Average_Stay=("Length of Stay (Days)", "mean"),
        Average_Bill=("Bill Amount (INR)", "mean")
    )
)


# =========================================================
# 10. DASHBOARD TABS - STRUCTURE ADAPTED FROM THE PDF
# =========================================================
tabs = st.tabs([
    "1. Executive Overview",
    "2. Healthcare Visit Trends",
    "3. Department Insights",
    "4. Patient & Treatment Analysis",
    "5. Records & Exports"
])


# =========================================================
# TAB 1: EXECUTIVE OVERVIEW
# =========================================================
with tabs[0]:
    st.header("1. Executive Overview")

    left, right = st.columns(2)

    with left:
        visit_type_summary = (
            df["Visit Type"]
            .value_counts()
            .rename_axis("Visit Type")
            .reset_index(name="Visits")
        )

        st.plotly_chart(
            px.pie(
                visit_type_summary,
                names="Visit Type",
                values="Visits",
                hole=0.45,
                title="Inpatient vs Outpatient Visits"
            ),
            use_container_width=True
        )

    with right:
        outcome_summary = (
            df["Outcome"]
            .value_counts()
            .rename_axis("Outcome")
            .reset_index(name="Visits")
        )

        st.plotly_chart(
            px.bar(
                outcome_summary,
                x="Outcome",
                y="Visits",
                title="Recorded Visit Outcomes"
            ),
            use_container_width=True
        )

    busiest_department = department_summary.loc[
        department_summary["Visits"].idxmax()
    ]

    st.info(
        f"Healthcare story: **{busiest_department['Department']}** "
        f"has the highest visit volume in this selection "
        f"({int(busiest_department['Visits'])} visits). "
        "Visit volume describes service activity, not care quality "
        "or clinical performance."
    )

    st.markdown(
        "**What this means:** Begin with the overall patient-visit picture. "
        "Then investigate monthly trends, department activity and the "
        "recorded treatment patterns."
    )


# =========================================================
# TAB 2: HEALTHCARE VISIT TRENDS
# =========================================================
with tabs[1]:
    st.header("2. Healthcare Visit Trends")

    st.plotly_chart(
        px.line(
            monthly,
            x="Visit Month",
            y="Visits",
            markers=True,
            title="Monthly Hospital Visit Trend"
        ),
        use_container_width=True
    )

    st.plotly_chart(
        px.line(
            monthly,
            x="Visit Month",
            y="Average_Stay",
            markers=True,
            title="Average Length of Stay by Month"
        ),
        use_container_width=True
    )

    st.plotly_chart(
        px.bar(
            monthly,
            x="Visit Month",
            y="Unique_Patients",
            title="Unique Sample Patients by Month"
        ),
        use_container_width=True
    )

    peak_month = monthly.loc[monthly["Visits"].idxmax()]
    lowest_month = monthly.loc[monthly["Visits"].idxmin()]

    st.info(
        f"Trend insight: Visit volume is highest in "
        f"**{peak_month['Visit Month']:%B %Y}** "
        f"({int(peak_month['Visits'])} visits) and lowest in "
        f"**{lowest_month['Visit Month']:%B %Y}** "
        f"({int(lowest_month['Visits'])} visits). These patterns can "
        "prompt questions about appointment timing, seasonal demand "
        "and resource planning; this dataset alone cannot establish causes."
    )

    st.dataframe(
        monthly,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# TAB 3: DEPARTMENT INSIGHTS
# =========================================================
with tabs[2]:
    st.header("3. Department Insights")

    left, right = st.columns(2)

    with left:
        st.plotly_chart(
            px.bar(
                department_summary.sort_values("Visits"),
                x="Visits",
                y="Department",
                orientation="h",
                title="Visit Volume by Department"
            ),
            use_container_width=True
        )

    with right:
        st.plotly_chart(
            px.bar(
                department_summary.sort_values("Average_Stay"),
                x="Average_Stay",
                y="Department",
                orientation="h",
                title="Average Length of Stay by Department"
            ),
            use_container_width=True
        )

    st.plotly_chart(
        px.bar(
            department_summary,
            x="Department",
            y="Bill_Total",
            title="Recorded Bill Amount by Department"
        ),
        use_container_width=True
    )

    highest_volume_department = department_summary.loc[
        department_summary["Visits"].idxmax()
    ]

    highest_stay_department = department_summary.loc[
        department_summary["Average_Stay"].idxmax()
    ]

    st.info(
        f"Department insight: **{highest_volume_department['Department']}** "
        f"has the highest visit volume "
        f"({int(highest_volume_department['Visits'])} visits). "
        f"**{highest_stay_department['Department']}** has the highest "
        f"average stay ({highest_stay_department['Average_Stay']:.1f} days). "
        "These are operational observations, not measures of department quality."
    )

    st.dataframe(
        department_summary.sort_values("Visits", ascending=False),
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# TAB 4: PATIENT AND TREATMENT ANALYSIS
# =========================================================
with tabs[3]:
    st.header("4. Patient & Treatment Analysis")

    left, right = st.columns(2)

    with left:
        age_summary = (
            df["Age Group"]
            .value_counts()
            .sort_index()
            .rename_axis("Age Group")
            .reset_index(name="Visits")
        )

        st.plotly_chart(
            px.bar(
                age_summary,
                x="Age Group",
                y="Visits",
                title="Visit Distribution by Age Group"
            ),
            use_container_width=True
        )

    with right:
        gender_summary = (
            df["Gender"]
            .value_counts()
            .rename_axis("Gender")
            .reset_index(name="Visits")
        )

        st.plotly_chart(
            px.pie(
                gender_summary,
                names="Gender",
                values="Visits",
                hole=0.4,
                title="Visits by Recorded Gender"
            ),
            use_container_width=True
        )

    st.plotly_chart(
        px.bar(
            treatment_summary.sort_values("Visits"),
            x="Visits",
            y="Treatment",
            orientation="h",
            title="Most Frequently Recorded Treatments"
        ),
        use_container_width=True
    )

    st.plotly_chart(
        px.treemap(
            df.groupby(
                ["Diagnosis Group", "Treatment"],
                as_index=False
            ).size(),
            path=["Diagnosis Group", "Treatment"],
            values="size",
            title="Visit Counts by Diagnosis Group and Treatment"
        ),
        use_container_width=True
    )

    most_common_treatment = treatment_summary.loc[
        treatment_summary["Visits"].idxmax()
    ]

    most_common_age = df["Age Group"].mode().iloc[0]

    st.info(
        f"Patient and treatment insight: The most common age band by "
        f"visit count is **{most_common_age}**. "
        f"**{most_common_treatment['Treatment']}** is the most frequently "
        "recorded treatment. Frequency does not indicate treatment "
        "effectiveness or clinical appropriateness."
    )

    st.subheader("Diagnosis group summary")
    st.dataframe(
        diagnosis_summary.sort_values("Visits", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Treatment summary")
    st.dataframe(
        treatment_summary.sort_values("Visits", ascending=False),
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# TAB 5: RECORDS AND EXPORTS
# =========================================================
with tabs[4]:
    st.header("5. Records & Exports")

    st.dataframe(
        df[REQUIRED_COLUMNS + ["Age Group"]].sort_values(
            "Visit Date",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

    summary = pd.DataFrame({
        "Metric": [
            "Total visits",
            "Unique sample patients",
            "Average age (years)",
            "Average length of stay (days)",
            "Total recorded bill amount (INR)",
            "Average recorded bill amount (INR)"
        ],
        "Value": [
            total_visits,
            unique_patients,
            round(average_age, 2),
            round(average_stay, 2),
            round(total_bill, 2),
            round(average_bill, 2)
        ]
    })

    st.subheader("Download reports")

    st.download_button(
        "⬇️ Download filtered records (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_healthcare_visits.csv",
        mime="text/csv"
    )

    st.download_button(
        "⬇️ Download KPI summary (CSV)",
        data=summary.to_csv(index=False).encode("utf-8"),
        file_name="healthcare_kpi_summary.csv",
        mime="text/csv"
    )

    st.download_button(
        "⬇️ Download Excel report",
        data=make_excel_report(
            df,
            summary,
            monthly,
            department_summary,
            treatment_summary
        ),
        file_name="healthcare_storytelling_report.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

    st.download_button(
        "⬇️ Download PDF summary",
        data=make_pdf_report(
            df,
            monthly,
            department_summary,
            treatment_summary
        ),
        file_name="healthcare_storytelling_summary.pdf",
        mime="application/pdf"
    )

    # PNG export: visits by department.
    chart_data = department_summary.sort_values(
        "Visits",
        ascending=False
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(chart_data["Department"], chart_data["Visits"])
    ax.set_title("Hospital Visits by Department")
    ax.set_ylabel("Visit count")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()

    png_output = io.BytesIO()
    fig.savefig(
        png_output,
        format="png",
        dpi=180,
        bbox_inches="tight"
    )
    plt.close(fig)

    st.download_button(
        "⬇️ Download department chart (PNG)",
        data=png_output.getvalue(),
        file_name="healthcare_department_visits.png",
        mime="image/png"
    )


# =========================================================
# 11. HEALTHCARE DATA STORYTELLING GUIDE
# =========================================================
st.divider()
st.subheader("How to present the healthcare data story")

st.markdown("""
1. **Question:** How many visits are recorded and which hospital services are used most?
2. **Observation:** Describe the visit, patient, department and treatment patterns shown in the charts.
3. **Meaning:** Explain what the counts and averages show about activity in this selected sample.
4. **Action to investigate:** Authorized hospital teams may review appointment scheduling, staffing and resource planning using validated operational information.
5. **Limit:** Synthetic records cannot establish causes, treatment effectiveness, quality of care or medical recommendations.
""")

st.caption(
    "Academic demonstration only. All built-in records are fictional. "
    "Never use this dashboard to make clinical decisions."
)
