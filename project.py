import streamlit as st
import pandas as pd
import plotly.express as px


# ------------------------------------------------
# PAGE CONFIG
# -----------------
# "st.set_page_config() is used to configure the Streamlit application's page settings,
#  such as the browser tab title, page icon, and layout.-------------------------------
st.set_page_config(
    page_title="Project Candy Data Science",
    page_icon="🍭",
    layout="wide"
)


# ------------------------------------------------
# TITLE st.markdown() is normally used to display Markdown text in Streamlit.
# unsafe_allow_html=True allows Streamlit to render the HTML instead of displaying 
# the HTML tags as plain text."
# ------------------------------------------------
st.markdown(
    """
    <h1 style='text-align: center; color: white;
               background-color: #420C42;
               padding: 15px;
               border-radius: 10px;'>
        🍬 Nassau Candy Distributor 🍭
    </h1>
    """,
    unsafe_allow_html=True
)


# ------------------------------------------------
# LOAD DATA
# ------------------------------------------------
# Load CSV
df = pd.read_csv("Nassau_Candy_Distributor.csv")

# Calculate Shipping Days once on the full dataset
# so every filtered view inherits the column safely.
df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True, errors="coerce")
df["Ship Date"] = pd.to_datetime(df["Ship Date"], dayfirst=True, errors="coerce")
df["Shipping Days"] = (df["Ship Date"] - df["Order Date"]).dt.days



# ============================================
# ADDING  SIDEBAR FILTERS
# ============================================

st.sidebar.header("🔎 Dashboard Filters")

# Region filter
region_options = ["All"] + sorted(df["Region"].dropna().unique().tolist())

selected_region = st.sidebar.selectbox(
    "🌎 Select Region",
    region_options
)

# # State filter
state_options = ["All"] + sorted(
    df["State/Province"].dropna().unique().tolist()
)

selected_state = st.sidebar.selectbox(
    "🗺️ Select State",
    state_options
)

# Division filter
division_options = ["All"] + sorted(
        df["Division"].dropna().unique().tolist()
)

selected_division = st.sidebar.selectbox(
    "🍬 Select Division",
    division_options
)

# Ship Mode filter
ship_mode_options = ["All"] + sorted(
        df["Ship Mode"].dropna().unique().tolist()
)

selected_ship_mode = st.sidebar.selectbox(
    "🚢 Select Ship Mode",
    ship_mode_options
)


# ============================================
# APPLY FILTERS
# ============================================

filtered_df = df.copy()

if selected_region != "All":
    filtered_df = filtered_df[
        filtered_df["Region"] == selected_region
    ]

if selected_state != "All":
    filtered_df = filtered_df[
        filtered_df["State/Province"] == selected_state
    ]

if selected_division != "All":
    filtered_df = filtered_df[
        filtered_df["Division"] == selected_division
    ]

if selected_ship_mode != "All":
    filtered_df = filtered_df[
        filtered_df["Ship Mode"] == selected_ship_mode
    ]

# Prevent ValueError: attempt to get argmax of an empty sequence
if filtered_df.empty:
    st.warning("⚠️ No data found for the selected filters. Please change or reset the filters.")
    st.stop()

# ------------------------------------------------

# ================================================================
# OVERALL DIVISION SUMMARY
# ================================================================

summary = (
    filtered_df.groupby("Division")
    .agg(
        Sales=("Sales", "sum"),
        Gross_Profit=("Gross Profit", "sum")
    )
    .reset_index()
)


# Calculate Gross Margin % - replace(0, pd.NA) 0 in the Sales column and replace it 
# with a missing value (pd.NA).
summary["Gross Margin %"] = (
    summary["Gross_Profit"] /
    summary["Sales"].replace(0, pd.NA)
) * 100


# Find division with highest gross margin, 
top_division = summary.loc[
    summary["Gross Margin %"].idxmax(),
    "Division"
]

top_margin = summary["Gross Margin %"].max()


# ================================================================
# METRIC CARD STYLING
# st.metric() cards are getting their visual styling from the CSS you injected using st.markdown().
# Now the important part: div[data-testid="stMetric"]
# ================================================================

st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background-color: #E3F2FD;
        border: 2px solid #2196F3;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.15);
    }

    div[data-testid="stMetricLabel"] {
        color: #1565C0;
        font-size: 16px;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #0D47A1;
        font-size: 30px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ================================================================
# KEY METRICS
# ================================================================

total_orders = filtered_df["Order ID"].nunique()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Total Orders",
    f"{total_orders:,}"
)

col2.metric(
    "Highest Margin Product Line",
    top_division
)

col3.metric(
    "Highest Gross Margin",
    f"{top_margin:.2f}%"
)

col4.metric(
    "Total Sales",
    f"${filtered_df['Sales'].sum():,.2f}"
)

col5.metric(
    "Total Gross Profit",
    f"${filtered_df['Gross Profit'].sum():,.2f}"
)



# ============================================
# CREATE EQUAL WIDTH COLUMNS
# ============================================

col1, col2 = st.columns(2)


# ============================================
# COLUMN 1
# ============================================

with col1:

    with st.container(border=True):

        st.markdown(
            "<h3 style='text-align:center; margin-top:0;'>"
            "🚚 Top 10 Most Efficient Routes"
            "</h3>",
            unsafe_allow_html=True
        )

        route_efficiency = (
            filtered_df.groupby("City")
            .agg(
                Minimum_Shipping_Time=("Shipping Days", "min"),
                Average_Shipping_Time=("Shipping Days", "mean"),
                Total_Shipments=("Order ID", "count")
            )
            .reset_index()
        )

        route_efficiency["Average_Shipping_Time"] = (
            route_efficiency["Average_Shipping_Time"].round(2)
        )

        top_5_min_time = (
            route_efficiency
            .sort_values(
                by="Minimum_Shipping_Time",
                ascending=True
            )
            .head(10)
        )

        st.dataframe(
            top_5_min_time,
            use_container_width=True,
            hide_index=True,
            height=400
        )


# ============================================
# COLUMN 2
# ============================================

with col2:

    with st.container(border=True):

        st.markdown(
            "<h3 style='text-align:center; margin-top:0;'>"
            "🚨 Highest Delayed Shipments"
            "</h3>",
            unsafe_allow_html=True
        )

        # Delayed orders
        # agg stands for aggregate. It allows you to perform multiple calculations at once.
        filtered_df["Delayed"] = filtered_df["Shipping Days"] > 1320.84

        delay_by_route = (
            filtered_df.groupby("City")
            .agg(
                Total_Shipments=("Order ID", "count"),
                Delayed_Shipments=("Delayed", "sum"),
                Maximum_Shipping_Time=("Shipping Days", "max"),
                Average_Shipping_Time=("Shipping Days", "mean")
            )
            .reset_index()
        )
       
        delay_by_route["Delay_Rate_%"] = (
            delay_by_route["Delayed_Shipments"]
            / delay_by_route["Total_Shipments"]
            * 100
        ).round(2)

        delay_by_route["Average_Shipping_Time"] = (
            delay_by_route["Average_Shipping_Time"].round(2)
        )

        top_5_delayed_routes = (
            delay_by_route
            .sort_values(
                by="Delayed_Shipments",
                ascending=False
            )
            .head(5)
        )

        fig = px.bar(
            top_5_delayed_routes,
            x="City",
            y="Delayed_Shipments",
            text="Delayed_Shipments",
            color="Delayed_Shipments"
        )

        fig.update_traces(
            texttemplate="%{text}",
            textposition="outside"
        )

        fig.update_layout(
            height=400,
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10
            ),
            xaxis_title="Customer Location",
            yaxis_title="Delayed Shipments",
            showlegend=False
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key="top_5_delayed_routes"
        )

###3  How shipping performance varies by region, state, and ship mode
# Shipping Days already calculated above.\n\n# ============================================
# REGION SHIPPING
# ============================================

region_shipping = (
    filtered_df.groupby("Region")["Shipping Days"]
      .mean()
      .reset_index()
)

region_shipping["Shipping Days"] = (
    region_shipping["Shipping Days"].round(1)
)


# ============================================
# STATE SHIPPING
# ============================================

state_shipping = (
    filtered_df.groupby("State/Province")["Shipping Days"]
      .mean()
      .reset_index()
      .sort_values("Shipping Days", ascending=True)
)

state_shipping["Shipping Days"] = (
    state_shipping["Shipping Days"].round(1)
)


# ============================================
# TWO EQUAL COLUMNS
# ============================================

col1, col2 = st.columns([1, 1])


# ============================================
# COLUMN 1 - REGION PIE CHART
# ============================================

with col1:

    st.markdown(
        """
        <h3 style="
            text-align:center;
            font-size:22px;
            font-weight:700;
            margin-bottom:10px;
        ">
        🌎 Average Shipping Days by Region
        </h3>
        """,
        unsafe_allow_html=True
    )

    fig_region = px.pie(
        region_shipping,
        names="Region",
        values="Shipping Days",
        hole=0.35
    )

    fig_region.update_traces(
        textinfo="label+percent",
        texttemplate="%{label}<br>%{percent}",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Average Shipping Days: %{value:.1f}<extra></extra>"
        )
    )

    fig_region.update_layout(
        height=450,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )

    st.plotly_chart(
        fig_region,
        use_container_width=True,
        key="average_shipping_region_pie"
    )


# ============================================
# COLUMN 2 - STATE BAR CHART
# ============================================

with col2:

    st.markdown(
        """
        <h3 style="
            text-align:center;
            font-size:22px;
            font-weight:700;
            margin-bottom:10px;
            # color:green;
        ">
        📍 Average Shipping Days by State
        </h3>
        """,
        unsafe_allow_html=True
    )

    fig_state = px.bar(
        state_shipping,
        x="Shipping Days",
        y="State/Province",
        orientation="h",
        text="Shipping Days",
         color="Shipping Days",
    color_continuous_scale="Viridis"
        
    )

    fig_state.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside"
    )

    fig_state.update_layout(
        height=450,
        margin=dict(
            l=20,
            r=30,
            t=20,
            b=20
        ),
        xaxis_title="Average Shipping Days",
        yaxis_title="State / Province",
        showlegend=False
    )

    st.plotly_chart(
        fig_state,
        use_container_width=True,
        key="average_shipping_state"
    )

# SHIP  Mode comparison 

# ============================================
# SHIPPING PERFORMANCE ANALYSIS
# ============================================



st.markdown(
    """
    <h2 style="
        text-align:center;
        font-size:26px;
        font-weight:700;
        margin-top:30px;
        margin-bottom:20px;
    ">
    🚚 Shipping Performance Analysis
    </h2>
    """,
    unsafe_allow_html=True
)

# ---------- REGION ----------
region_shipping = (
    filtered_df.groupby("Region")
    .agg(
        Average_Shipping_Days=("Shipping Days", "mean"),
        Total_Shipments=("Order ID", "count")
    )
    .reset_index()
)

# ---------- STATE ----------
state_shipping = (
    filtered_df.groupby("State/Province")
    .agg(
        Average_Shipping_Days=("Shipping Days", "mean")
    )
    .reset_index()
)

# ---------- SHIP MODE ----------
ship_mode_comparison = (
    filtered_df.groupby("Ship Mode")
    .agg(
        Average_Lead_Time=("Shipping Days", "mean"),
        Total_Shipments=("Order ID", "count")
    )
    .reset_index()
)


# Create 3 columns
col1, col2, col3 = st.columns(3)


# ============================================
# 1️⃣ REGION — BAR CHART
# ============================================

with col1:

    st.markdown("### 🌎 Region Shipping")

    fig_region = px.bar(
        region_shipping,
        x="Region",
        y="Average_Shipping_Days",
        text="Average_Shipping_Days",
        title="Average Shipping Days by Region"
    )

    fig_region.update_traces(
        texttemplate="%{text:.2f} days",
        textposition="outside"
    )

    fig_region.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="Region",
        yaxis_title="Avg Shipping Days",
        showlegend=False
    )

    st.plotly_chart(
        fig_region,
        use_container_width=True,
        key="region_bar_chart"
    )


# ============================================
# 2️⃣ STATE — PIE CHART
# ============================================

with col2:

    st.markdown("### 🗺️ State Shipping")

    # Top 8 states for cleaner visualization
    state_pie = (
        state_shipping
        .sort_values("Average_Shipping_Days", ascending=False)
        .head(8)
    )

    fig_state = px.pie(
        state_pie,
        names="State/Province",
        values="Average_Shipping_Days",
        title="Shipping Time Distribution by State",
        hole=0.40
    )

    fig_state.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    fig_state.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=50, b=10),
        showlegend=False
    )

    st.plotly_chart(
        fig_state,
        use_container_width=True,
        key="state_pie_chart"
    )


# ============================================
# 3️⃣ SHIP MODE — SCATTER CHART
# ============================================

with col3:

    st.markdown("### 🚢 Ship Mode")

    fig_ship = px.scatter(
        ship_mode_comparison,
        x="Total_Shipments",
        y="Average_Lead_Time",
        size="Total_Shipments",
        text="Ship Mode",
        hover_name="Ship Mode",
        title="Ship Mode: Speed vs Volume"
    )

    fig_ship.update_traces(
        textposition="top center"
    )

    fig_ship.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="Total Shipments",
        yaxis_title="Average Lead Time (Days)",
        showlegend=False
    )

    st.plotly_chart(
        fig_ship,
        use_container_width=True,
        key="ship_mode_scatter_chart"
    )
