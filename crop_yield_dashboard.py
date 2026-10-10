"""
Crop Yield & Rainfall Intelligence Dashboard
--------------------------------------------
Run:
    pip install streamlit pandas plotly
    streamlit run crop_yield_dashboard.py

IMPORTANT DATA NOTE:
The included CSV is a simulated educational dataset created for demonstration.
It is not official agricultural statistics and should not be used for policy,
commercial decisions, or scientific conclusions. Replace it with a verified
public dataset for real-world analysis.
"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Crop Yield & Rainfall Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = Path(__file__).with_name("crop_yield_rainfall_dataset.csv")

@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
    elif DATA_FILE.exists():
        data = pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame()
    numeric_cols = [
        "Year", "Rainfall_mm", "Temperature_C", "Humidity_pct",
        "Area_Hectares", "Yield_Tonnes_per_Hectare", "Production_Tonnes"
    ]
    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    return data.dropna(subset=["Year", "State", "Crop"])

st.title("🌾 Crop Yield & Rainfall Intelligence Dashboard")
st.caption("Explore crop production, weather patterns, and yield across years and regions.")
st.info(
    "Educational demo: the bundled dataset is simulated for learning and dashboard testing. "
    "Use the CSV upload option to analyse verified public data."
)

with st.sidebar:
    st.header("⚙️ Data & Filters")
    uploaded = st.file_uploader("Upload a replacement CSV (optional)", type=["csv"])
    data = load_data(uploaded)
    if data.empty:
        st.error("Dataset not found. Keep crop_yield_rainfall_dataset.csv beside this Python file.")
        st.stop()

    years = sorted(data["Year"].dropna().astype(int).unique().tolist())
    year_range = st.select_slider(
        "Year range",
        options=years,
        value=(years[0], years[-1]),
    )
    state_options = sorted(data["State"].dropna().unique().tolist())
    selected_states = st.multiselect("State / region", state_options, default=state_options)
    crop_options = sorted(data["Crop"].dropna().unique().tolist())
    selected_crops = st.multiselect("Crop", crop_options, default=crop_options)
    season_options = sorted(data["Season"].dropna().unique().tolist())
    selected_seasons = st.multiselect("Season", season_options, default=season_options)

filtered = data[
    data["Year"].between(year_range[0], year_range[1])
    & data["State"].isin(selected_states)
    & data["Crop"].isin(selected_crops)
    & data["Season"].isin(selected_seasons)
].copy()

if filtered.empty:
    st.warning("No rows match these filters. Select at least one state, crop, and season.")
    st.stop()

# KPIs
total_production = filtered["Production_Tonnes"].sum()
avg_yield = filtered["Yield_Tonnes_per_Hectare"].mean()
avg_rainfall = filtered["Rainfall_mm"].mean()
total_area = filtered["Area_Hectares"].sum()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total production", f"{total_production:,.0f} t")
k2.metric("Average yield", f"{avg_yield:,.2f} t/ha")
k3.metric("Average rainfall", f"{avg_rainfall:,.0f} mm")
k4.metric("Total cultivated area", f"{total_area:,.0f} ha")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", "🌱 Crop Analysis", "🌧️ Rainfall", "🗺️ Regional Comparison", "🔎 Data & Insights"
])

with tab1:
    left, right = st.columns(2)
    yearly = filtered.groupby("Year", as_index=False).agg(
        Production_Tonnes=("Production_Tonnes", "sum"),
        Yield_Tonnes_per_Hectare=("Yield_Tonnes_per_Hectare", "mean"),
        Rainfall_mm=("Rainfall_mm", "mean"),
    )
    with left:
        fig = px.line(yearly, x="Year", y="Production_Tonnes", markers=True,
                      title="Total production by year", labels={"Production_Tonnes": "Production (tonnes)"})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        crop_prod = filtered.groupby("Crop", as_index=False)["Production_Tonnes"].sum()
        fig = px.pie(crop_prod, names="Crop", values="Production_Tonnes", hole=0.35,
                     title="Production share by crop")
        st.plotly_chart(fig, use_container_width=True)
    fig = px.scatter(
        filtered, x="Rainfall_mm", y="Yield_Tonnes_per_Hectare",
        color="Crop", size="Area_Hectares", hover_data=["State", "Year", "Season"],
        title="Rainfall vs yield (bubble size = cultivated area)",
        labels={"Rainfall_mm": "Rainfall (mm)", "Yield_Tonnes_per_Hectare": "Yield (tonnes/ha)"}
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    crop_summary = filtered.groupby("Crop", as_index=False).agg(
        Average_Yield=("Yield_Tonnes_per_Hectare", "mean"),
        Production_Tonnes=("Production_Tonnes", "sum"),
        Area_Hectares=("Area_Hectares", "sum"),
    ).sort_values("Average_Yield", ascending=False)
    left, right = st.columns(2)
    with left:
        fig = px.bar(crop_summary, x="Crop", y="Average_Yield", color="Crop",
                     title="Average yield by crop", labels={"Average_Yield": "Yield (tonnes/ha)"})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.bar(crop_summary.sort_values("Production_Tonnes"), x="Production_Tonnes", y="Crop",
                     orientation="h", title="Total production by crop",
                     labels={"Production_Tonnes": "Production (tonnes)"})
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(crop_summary, use_container_width=True, hide_index=True)

with tab3:
    weather = filtered.groupby("Year", as_index=False).agg(
        Rainfall_mm=("Rainfall_mm", "mean"),
        Yield_Tonnes_per_Hectare=("Yield_Tonnes_per_Hectare", "mean"),
        Temperature_C=("Temperature_C", "mean"),
    )
    fig = px.line(weather, x="Year", y=["Rainfall_mm", "Temperature_C"],
                  markers=True, title="Average rainfall and temperature trend")
    st.plotly_chart(fig, use_container_width=True)
    fig = px.scatter(filtered, x="Rainfall_mm", y="Yield_Tonnes_per_Hectare",
                     trendline="ols", color="Season", hover_data=["State", "Crop", "Year"],
                     title="Rainfall-yield relationship")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("A visible relationship is not proof that rainfall alone causes changes in yield.")

with tab4:
    state_summary = filtered.groupby("State", as_index=False).agg(
        Average_Yield=("Yield_Tonnes_per_Hectare", "mean"),
        Production_Tonnes=("Production_Tonnes", "sum"),
        Average_Rainfall_mm=("Rainfall_mm", "mean"),
    ).sort_values("Average_Yield", ascending=False)
    left, right = st.columns(2)
    with left:
        fig = px.bar(state_summary.head(10).sort_values("Average_Yield"),
                     x="Average_Yield", y="State", orientation="h", color="Average_Yield",
                     title="Top 10 states by average yield",
                     labels={"Average_Yield": "Yield (tonnes/ha)"})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.bar(state_summary.sort_values("Production_Tonnes", ascending=False).head(10),
                     x="State", y="Production_Tonnes", color="State",
                     title="Top 10 states by total production",
                     labels={"Production_Tonnes": "Production (tonnes)"})
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(state_summary, use_container_width=True, hide_index=True)

with tab5:
    st.subheader("Correlation heatmap")
    corr_cols = ["Rainfall_mm", "Temperature_C", "Humidity_pct",
                 "Area_Hectares", "Yield_Tonnes_per_Hectare", "Production_Tonnes"]
    corr = filtered[corr_cols].corr(numeric_only=True)
    fig = px.imshow(corr, text_auto=".2f", aspect="auto", color_continuous_scale="RdYlGn",
                    zmin=-1, zmax=1, title="Correlation between numeric variables")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Filtered data")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download filtered data (CSV)",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_crop_yield_rainfall.csv",
        mime="text/csv",
    )
    st.subheader("Quick insights")
    best_crop = filtered.groupby("Crop")["Yield_Tonnes_per_Hectare"].mean().idxmax()
    best_state = filtered.groupby("State")["Yield_Tonnes_per_Hectare"].mean().idxmax()
    st.write(f"- Highest average yield in the current selection: **{best_crop}**.")
    st.write(f"- Highest average-yield state in the current selection: **{best_state}**.")
    st.write(f"- Average rainfall in the current selection: **{filtered['Rainfall_mm'].mean():,.1f} mm**.")
    st.write("- These insights describe the selected dataset only; the included demo data is simulated.")

st.divider()
st.caption("Built with Streamlit, Pandas, and Plotly | Crop Yield & Rainfall Intelligence Dashboard")
