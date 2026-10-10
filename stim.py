
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Medicine Analytics Dashboard",
    page_icon="💊",
    layout="wide"
)

# ---------------- SAMPLE DATA ----------------
# Demonstration data only, not real pharmacy records.

@st.cache_data
def load_data():
    rng = np.random.default_rng(42)

    medicines = [
        ("Paracetamol", "Pain Relief", "HealthPlus", 25),
        ("Ibuprofen", "Pain Relief", "MediCare", 45),
        ("Amoxicillin", "Antibiotics", "LifeMed", 85),
        ("Azithromycin", "Antibiotics", "HealthPlus", 110),
        ("Cetirizine", "Allergy", "MediCare", 30),
        ("Loratadine", "Allergy", "LifeMed", 55),
        ("Metformin", "Diabetes", "HealthPlus", 65),
        ("Glimepiride", "Diabetes", "MediCare", 75),
        ("Amlodipine", "Heart Care", "LifeMed", 50),
        ("Atorvastatin", "Heart Care", "HealthPlus", 95),
        ("Omeprazole", "Digestive Health", "MediCare", 60),
        ("Pantoprazole", "Digestive Health", "LifeMed", 70),
    ]

    rows = []
    months = pd.date_range("2026-01-01", periods=12, freq="MS")

    for name, category, supplier, price in medicines:
        stock = int(rng.integers(100, 800))

        for month in months:
            sold = int(rng.integers(20, 180))
            rows.append({
                "Month": month,
                "Medicine": name,
                "Category": category,
                "Supplier": supplier,
                "Unit Price (₹)": price,
                "Units Sold": sold,
                "Stock": stock,
                "Sales Revenue (₹)": sold * price,
            })

    return pd.DataFrame(rows)


df = load_data()

# ---------------- HEADER ----------------
st.title("💊 Medicine Analytics Dashboard")
st.caption(
    "Medicine inventory, sales, category analysis and price distribution"
)

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.header("🔎 Dashboard Filters")

categories = sorted(df["Category"].unique())
selected_categories = st.sidebar.multiselect(
    "Select medicine categories",
    categories,
    default=categories
)

available = df[df["Category"].isin(selected_categories)]
medicine_options = sorted(available["Medicine"].unique())

selected_medicines = st.sidebar.multiselect(
    "Select medicines",
    medicine_options,
    default=medicine_options
)

supplier_options = sorted(available["Supplier"].unique())
selected_suppliers = st.sidebar.multiselect(
    "Select suppliers",
    supplier_options,
    default=supplier_options
)

date_range = st.sidebar.date_input(
    "Select date range",
    value=(df["Month"].min().date(), df["Month"].max().date()),
    min_value=df["Month"].min().date(),
    max_value=df["Month"].max().date()
)

# ---------------- APPLY FILTERS ----------------
filtered = df[
    df["Category"].isin(selected_categories)
    & df["Medicine"].isin(selected_medicines)
    & df["Supplier"].isin(selected_suppliers)
].copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        filtered["Month"].between(
            pd.Timestamp(start_date),
            pd.Timestamp(end_date)
        )
    ]

if filtered.empty:
    st.warning("No data matches your filters. Please select other options.")
    st.stop()

# ---------------- KPI CARDS ----------------
total_medicines = filtered["Medicine"].nunique()
total_stock = (
    filtered.sort_values("Month")
    .groupby("Medicine")["Stock"]
    .last()
    .sum()
)
total_sold = filtered["Units Sold"].sum()
total_revenue = filtered["Sales Revenue (₹)"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("💊 Medicines", f"{total_medicines}")
c2.metric("📦 Current Stock", f"{total_stock:,}")
c3.metric("🛒 Units Sold", f"{total_sold:,}")
c4.metric("💰 Sales Revenue", f"₹{total_revenue:,.0f}")

st.divider()

# ---------------- BAR CHART ----------------
st.subheader("📊 Medicine-wise Sales")

bar_data = (
    filtered.groupby("Medicine", as_index=False)["Units Sold"]
    .sum()
    .sort_values("Units Sold", ascending=False)
)

fig_bar = px.bar(
    bar_data,
    x="Medicine",
    y="Units Sold",
    color="Units Sold",
    title="Total Units Sold by Medicine",
    text_auto=True,
    color_continuous_scale="Blues"
)
fig_bar.update_layout(xaxis_tickangle=-35)
st.plotly_chart(fig_bar, use_container_width=True)

# ---------------- TWO-COLUMN CHARTS ----------------
left, right = st.columns(2)

with left:
    st.subheader("🥧 Stock by Medicine Category")

    latest_stock = (
        filtered.sort_values("Month")
        .groupby("Medicine", as_index=False)
        .tail(1)
    )

    category_stock = (
        latest_stock.groupby("Category", as_index=False)["Stock"].sum()
    )

    fig_pie = px.pie(
        category_stock,
        names="Category",
        values="Stock",
        hole=0.4,
        title="Inventory Distribution"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with right:
    st.subheader("📈 Monthly Sales Trend")

    monthly_sales = (
        filtered.groupby("Month", as_index=False)["Sales Revenue (₹)"]
        .sum()
    )

    fig_line = px.line(
        monthly_sales,
        x="Month",
        y="Sales Revenue (₹)",
        markers=True,
        title="Monthly Revenue Trend"
    )
    st.plotly_chart(fig_line, use_container_width=True)

# ---------------- HISTOGRAM ----------------
st.subheader("📉 Medicine Price Distribution")

unique_medicines = filtered.drop_duplicates("Medicine")

fig_hist = px.histogram(
    unique_medicines,
    x="Unit Price (₹)",
    nbins=8,
    color="Category",
    title="Distribution of Medicine Prices",
    labels={"Unit Price (₹)": "Price per Unit (₹)"}
)
st.plotly_chart(fig_hist, use_container_width=True)

# ---------------- SCATTER CHART ----------------
st.subheader("🔬 Price vs Units Sold")

medicine_summary = (
    filtered.groupby(
        ["Medicine", "Category", "Unit Price (₹)"],
        as_index=False
    )
    .agg({"Units Sold": "sum", "Sales Revenue (₹)": "sum"})
)

fig_scatter = px.scatter(
    medicine_summary,
    x="Unit Price (₹)",
    y="Units Sold",
    color="Category",
    size="Sales Revenue (₹)",
    hover_name="Medicine",
    title="Medicine Price and Sales Relationship"
)
st.plotly_chart(fig_scatter, use_container_width=True)

# ---------------- DATA TABLE ----------------
st.subheader("📋 Filtered Medicine Records")

display_data = filtered.copy()
display_data["Month"] = display_data["Month"].dt.strftime("%Y-%m")

st.dataframe(
    display_data.sort_values(["Month", "Medicine"]),
    use_container_width=True,
    hide_index=True
)

# ---------------- CSV DOWNLOAD ----------------
csv_data = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download Filtered Data (CSV)",
    data=csv_data,
    file_name="medicine_dashboard_data.csv",
    mime="text/csv"
)

st.caption(
    "Note: All records are randomly generated demonstration data. "
    "They are not real medical, prescription or pharmacy records."
)
