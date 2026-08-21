import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="RecoverAI | Revenue Recovery",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------

st.markdown("""
<style>

.main {
    background-color: #0b1220;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

.hero {
    background: linear-gradient(135deg, #111c35, #172554);
    padding: 30px;
    border-radius: 20px;
    border: 1px solid #26365c;
    margin-bottom: 25px;
}

.hero-title {
    font-size: 38px;
    font-weight: 800;
    color: white;
    margin-bottom: 5px;
}

.hero-subtitle {
    font-size: 16px;
    color: #a9b7d0;
}

.kpi {
    background: linear-gradient(145deg, #111827, #18243b);
    padding: 22px;
    border-radius: 16px;
    border: 1px solid #263653;
    min-height: 130px;
}

.kpi-label {
    color: #94a3b8;
    font-size: 14px;
    margin-bottom: 8px;
}

.kpi-value {
    color: white;
    font-size: 30px;
    font-weight: 800;
}

.kpi-caption {
    color: #67e8f9;
    font-size: 13px;
    margin-top: 5px;
}

.section-title {
    font-size: 24px;
    font-weight: 750;
    color: white;
    margin-top: 30px;
    margin-bottom: 12px;
}

.insight {
    background: #111827;
    border-left: 5px solid #22d3ee;
    padding: 18px;
    border-radius: 12px;
    color: #dbeafe;
    margin-bottom: 10px;
}

.priority-high {
    background: #3b1720;
    color: #fecaca;
    padding: 5px 10px;
    border-radius: 20px;
    font-weight: 700;
}

.priority-medium {
    background: #3b2e12;
    color: #fde68a;
    padding: 5px 10px;
    border-radius: 20px;
    font-weight: 700;
}

.priority-low {
    background: #12352b;
    color: #a7f3d0;
    padding: 5px 10px;
    border-radius: 20px;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "transactions.csv"

try:
    df = pd.read_csv(CSV_FILE)
except Exception as e:
    st.error(f"Could not load transactions.csv: {e}")
    st.stop()


# ---------------------------------------------------------
# CLEAN COLUMN NAMES
# ---------------------------------------------------------

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# Make sure important columns exist
required_columns = [
    "transaction_id",
    "customer",
    "amount",
    "status",
    "failure_reason",
    "payment_method"
]

for column in required_columns:
    if column not in df.columns:
        df[column] = "Unknown"


# ---------------------------------------------------------
# DATA CLEANING
# ---------------------------------------------------------

df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

df["status"] = (
    df["status"]
    .astype(str)
    .str.strip()
    .str.title()
)

df["failure_reason"] = (
    df["failure_reason"]
    .fillna("None")
    .astype(str)
    .str.strip()
)

df["payment_method"] = (
    df["payment_method"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
)

if "retry_count" in df.columns:
    df["retry_count"] = pd.to_numeric(
        df["retry_count"],
        errors="coerce"
    ).fillna(0)

else:
    df["retry_count"] = 0


# ---------------------------------------------------------
# RECOVERY SCORE
# ---------------------------------------------------------

def calculate_recovery_score(row):

    score = 50

    if row["status"] == "Failed":
        score += 20

    if row["amount"] >= 5000:
        score += 10

    if row["payment_method"].lower() == "upi":
        score += 10

    if row["retry_count"] <= 2:
        score += 10

    if row["failure_reason"].lower() in [
        "network error",
        "bank timeout"
    ]:
        score += 5

    return min(score, 100)


df["recovery_score"] = df.apply(
    calculate_recovery_score,
    axis=1
)


# ---------------------------------------------------------
# RECOVERY PRIORITY
# ---------------------------------------------------------

def get_priority(score):

    if score >= 80:
        return "High"

    elif score >= 60:
        return "Medium"

    return "Low"


df["priority"] = df["recovery_score"].apply(get_priority)


# ---------------------------------------------------------
# RECOVERY ACTION
# ---------------------------------------------------------

def recovery_action(row):

    reason = row["failure_reason"].lower()

    if "insufficient" in reason:
        return "Retry after balance confirmation"

    if "network" in reason:
        return "Retry transaction"

    if "timeout" in reason:
        return "Retry with alternate route"

    if "declined" in reason:
        return "Suggest alternate payment method"

    return "Send recovery reminder"


df["recommended_action"] = df.apply(
    recovery_action,
    axis=1
)


# ---------------------------------------------------------
# HERO SECTION
# ---------------------------------------------------------

st.markdown("""
<div class="hero">

<div class="hero-title">
💳 RecoverAI
</div>

<div class="hero-subtitle">
AI-Powered Revenue Recovery Agent
</div>

<p style="color:#cbd5e1; margin-top:15px;">
RecoverAI analyzes failed payment transactions, identifies
high-value recovery opportunities, prioritizes customers and
recommends the next best recovery action.
</p>

</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------

st.sidebar.markdown("## 🎛️ Dashboard Filters")

status_options = ["All"] + sorted(
    df["status"].dropna().unique().tolist()
)

selected_status = st.sidebar.selectbox(
    "Payment Status",
    status_options
)

payment_options = ["All"] + sorted(
    df["payment_method"].dropna().unique().tolist()
)

selected_payment = st.sidebar.selectbox(
    "Payment Method",
    payment_options
)

priority_options = ["All", "High", "Medium", "Low"]

selected_priority = st.sidebar.selectbox(
    "Recovery Priority",
    priority_options
)


# ---------------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------------

filtered_df = df.copy()

if selected_status != "All":
    filtered_df = filtered_df[
        filtered_df["status"] == selected_status
    ]

if selected_payment != "All":
    filtered_df = filtered_df[
        filtered_df["payment_method"] == selected_payment
    ]

if selected_priority != "All":
    filtered_df = filtered_df[
        filtered_df["priority"] == selected_priority
    ]


# ---------------------------------------------------------
# KPI CALCULATIONS
# ---------------------------------------------------------

total_transactions = len(filtered_df)

failed_df = filtered_df[
    filtered_df["status"].str.lower() == "failed"
]

successful_df = filtered_df[
    filtered_df["status"].str.lower() == "Successful".lower()
]

failed_payments = len(failed_df)

failed_value = failed_df["amount"].sum()

successful_value = successful_df["amount"].sum()

recovery_opportunity = failed_df[
    failed_df["recovery_score"] >= 60
]["amount"].sum()

if failed_payments > 0:
    failure_rate = (
        failed_payments / total_transactions
    ) * 100
else:
    failure_rate = 0


# ---------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">📊 Business Overview</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-label">Total Transactions</div>
        <div class="kpi-value">{total_transactions:,}</div>
        <div class="kpi-caption">Processed payments</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-label">Failed Payments</div>
        <div class="kpi-value">{failed_payments:,}</div>
        <div class="kpi-caption">{failure_rate:.1f}% failure rate</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-label">Failed Payment Value</div>
        <div class="kpi-value">₹{failed_value:,.0f}</div>
        <div class="kpi-caption">Potential revenue at risk</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-label">Recovery Opportunity</div>
        <div class="kpi-value">₹{recovery_opportunity:,.0f}</div>
        <div class="kpi-caption">AI-prioritized value</div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# CHARTS
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">📈 Payment Intelligence</div>',
    unsafe_allow_html=True
)

chart1, chart2 = st.columns(2)

with chart1:

    status_counts = (
        filtered_df["status"]
        .value_counts()
        .reset_index()
    )

    status_counts.columns = ["Status", "Count"]

    fig_status = px.bar(
        status_counts,
        x="Status",
        y="Count",
        title="Payment Status Distribution",
        text="Count"
    )

    fig_status.update_layout(
        template="plotly_dark",
        height=400,
        showlegend=False
    )

    st.plotly_chart(
        fig_status,
        use_container_width=True
    )


with chart2:

    reason_data = failed_df[
        failed_df["failure_reason"].str.lower() != "none"
    ]

    reason_counts = (
        reason_data["failure_reason"]
        .value_counts()
        .reset_index()
    )

    reason_counts.columns = [
        "Failure Reason",
        "Count"
    ]

    if len(reason_counts) > 0:

        fig_reason = px.pie(
            reason_counts,
            names="Failure Reason",
            values="Count",
            title="Why Payments Are Failing"
        )

        fig_reason.update_layout(
            template="plotly_dark",
            height=400
        )

        st.plotly_chart(
            fig_reason,
            use_container_width=True
        )

    else:
        st.info("No failure reasons available.")


# ---------------------------------------------------------
# RECOVERY OPPORTUNITIES
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">🚨 Recovery Opportunities</div>',
    unsafe_allow_html=True
)

opportunities = failed_df.sort_values(
    by="recovery_score",
    ascending=False
).copy()

if len(opportunities) > 0:

    display_columns = [
        "transaction_id",
        "customer",
        "amount",
        "failure_reason",
        "payment_method",
        "retry_count",
        "recovery_score",
        "priority",
        "recommended_action"
    ]

    display_columns = [
        col for col in display_columns
        if col in opportunities.columns
    ]

    display_df = opportunities[display_columns].head(10)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "🎉 No failed transactions match the current filters."
    )


# ---------------------------------------------------------
# FAILURE VALUE BY REASON
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">💰 Revenue at Risk by Failure Reason</div>',
    unsafe_allow_html=True
)

if len(failed_df) > 0:

    risk_data = (
        failed_df
        .groupby("failure_reason", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )

    risk_data.columns = [
        "Failure Reason",
        "Amount at Risk"
    ]

    fig_risk = px.bar(
        risk_data,
        x="Failure Reason",
        y="Amount at Risk",
        text_auto=".2s",
        title="Potential Revenue Loss by Failure Reason"
    )

    fig_risk.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(
        fig_risk,
        use_container_width=True
    )


# ---------------------------------------------------------
# AI INSIGHTS
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">🤖 AI Recovery Insights</div>',
    unsafe_allow_html=True
)

if len(failed_df) > 0:

    top_reason = (
        failed_df["failure_reason"]
        .value_counts()
        .idxmax()
    )

    highest_value_customer = failed_df.loc[
        failed_df["amount"].idxmax(),
        "customer"
    ]

    high_priority_count = len(
        failed_df[
            failed_df["priority"] == "High"
        ]
    )

    st.markdown(f"""
    <div class="insight">
    🔎 <b>Most common failure:</b> {top_reason}
    </div>

    <div class="insight">
    💰 <b>Highest-value failed transaction:</b>
    {highest_value_customer}
    </div>

    <div class="insight">
    🚨 <b>High-priority recovery cases:</b>
    {high_priority_count}
    </div>

    <div class="insight">
    🎯 <b>Recommended strategy:</b>
    Prioritize high-value failed payments with strong recovery
    scores before lower-value transactions.
    </div>
    """, unsafe_allow_html=True)

else:

    st.success(
        "No failed payments available for AI analysis."
    )


# ---------------------------------------------------------
# TRANSACTION EXPLORER
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">🔍 Transaction Explorer</div>',
    unsafe_allow_html=True
)

search = st.text_input(
    "Search by customer or transaction ID"
)

search_df = filtered_df.copy()

if search:

    search = search.lower()

    search_df = search_df[
        search_df["customer"]
        .astype(str)
        .str.lower()
        .str.contains(search, na=False)
        |
        search_df["transaction_id"]
        .astype(str)
        .str.lower()
        .str.contains(search, na=False)
    ]

st.dataframe(
    search_df,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.markdown("""
<hr>

<div style="
text-align:center;
color:#64748b;
padding:20px;
">

<b>RecoverAI</b> • AI-Powered Revenue Recovery Dashboard<br>
Built with Python • Pandas • Streamlit • Plotly

</div>
""", unsafe_allow_html=True)