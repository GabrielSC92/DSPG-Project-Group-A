"""
Researcher View - Data Table Page
Displays quantitative data extracted from government reports with filtering capabilities.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# Try to import database functions
try:
    from utils.database import get_all_interactions, is_database_connected
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Page configuration
st.markdown("""
<div class="page-header">
    <h1>📊 Data Table</h1>
    <p>View and analyze quantitative indicators extracted from government reports</p>
</div>
""", unsafe_allow_html=True)

# Privacy note
st.info("⚠️ **Privacy Notice**: Raw chat content is never stored. Only synthesized summaries and metrics are available for analysis.", icon="🔒")


def load_from_database() -> pd.DataFrame:
    """Load data from the database."""
    if not DB_AVAILABLE or not is_database_connected():
        return None
    
    interactions = get_all_interactions(limit=1000)
    if not interactions:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(interactions)
    
    # Rename columns to match display format
    df = df.rename(columns={
        'interaction_id': 'ID',
        'user_id': 'User ID',
        'interaction_date': 'Date',
        'summary': 'Topic Summary',
        'satisfaction_raw': 'Satisfaction (Raw)',
        'satisfaction_normalized': 'Satisfaction (Normalized)',
        'correlation_index': 'Correlation Index',
        'verification_flag': 'Verified'
    })
    
    # Convert verification flag to boolean
    df['Verified'] = df['Verified'].apply(lambda x: x == 'V' if x else False)
    
    # Convert date column
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Add Source column (placeholder - would come from RAG system)
    df['Source'] = 'User Interaction'
    
    return df


def generate_demo_data(n_rows: int = 100) -> pd.DataFrame:
    """Generate demo data matching the DB Quant schema (fallback)."""
    
    topics = [
        "Financial Management",
        "Policy Effectiveness", 
        "Administrative Efficiency",
        "Service Delivery",
        "Transparency & Accountability",
        "Human Resources",
        "Digital Transformation",
        "Citizen Engagement",
        "Regulatory Compliance",
        "Strategic Planning"
    ]
    
    # Generate dates over the past year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    data = {
        "ID": [f"QRY_{str(i).zfill(5)}" for i in range(1, n_rows + 1)],
        "User ID": [f"USR_{str(random.randint(1, 50)).zfill(3)}" for _ in range(n_rows)],
        "Date": [start_date + timedelta(days=random.randint(0, 365)) for _ in range(n_rows)],
        "Topic Summary": [random.choice(topics) for _ in range(n_rows)],
        "Satisfaction (Raw)": [random.randint(1, 10) for _ in range(n_rows)],
        "Satisfaction (Normalized)": [round(random.uniform(0, 1), 3) for _ in range(n_rows)],
        "Correlation Index": [round(random.uniform(0.5, 1.0), 3) for _ in range(n_rows)],
        "Verified": [random.choice([True, False]) for _ in range(n_rows)],
        "Source": [random.choice(["Court of Audit", "Auditdienst Rijk", "IOB"]) for _ in range(n_rows)]
    }
    
    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values("Date", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_data():
    """Load data from database or generate demo data as fallback."""
    db_data = load_from_database()
    if db_data is not None and len(db_data) > 0:
        return db_data, True  # Return data and flag indicating DB source
    return generate_demo_data(150), False  # Fallback to demo data


# Load data
df, using_db = get_data()

# Show data source indicator
if using_db:
    st.success(f"📊 Showing {len(df)} records from database", icon="✅")
else:
    st.warning("📊 Showing demo data (database empty or not connected)", icon="⚠️")

# --- FILTERS SECTION ---
st.markdown("### 🔍 Filters")

col1, col2, col3, col4 = st.columns(4)

with col1:
    # Date range filter
    date_range = st.date_input(
        "Date Range",
        value=(df["Date"].min().date(), df["Date"].max().date()),
        key="date_filter"
    )

with col2:
    # Topic filter
    topics = ["All"] + sorted(df["Topic Summary"].unique().tolist())
    selected_topic = st.selectbox("Topic", topics, key="topic_filter")

with col3:
    # User ID filter
    users = ["All"] + sorted(df["User ID"].unique().tolist())
    selected_user = st.selectbox("User ID", users, key="user_filter")

with col4:
    # Verification status filter
    verification_options = ["All", "Verified Only", "Unverified Only"]
    selected_verification = st.selectbox("Verification Status", verification_options, key="verification_filter")

# Search box
search_term = st.text_input("🔎 Search", placeholder="Search across all columns...", key="search_box")

# Apply filters
filtered_df = df.copy()

# Date filter
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df["Date"].dt.date >= start_date) & 
        (filtered_df["Date"].dt.date <= end_date)
    ]

# Topic filter
if selected_topic != "All":
    filtered_df = filtered_df[filtered_df["Topic Summary"] == selected_topic]

# User filter
if selected_user != "All":
    filtered_df = filtered_df[filtered_df["User ID"] == selected_user]

# Verification filter
if selected_verification == "Verified Only":
    filtered_df = filtered_df[filtered_df["Verified"] == True]
elif selected_verification == "Unverified Only":
    filtered_df = filtered_df[filtered_df["Verified"] == False]

# Search filter
if search_term:
    search_term_lower = search_term.lower()
    mask = filtered_df.astype(str).apply(
        lambda x: x.str.lower().str.contains(search_term_lower, na=False)
    ).any(axis=1)
    filtered_df = filtered_df[mask]

st.markdown("---")

# --- METRICS ROW ---
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Records", len(filtered_df))
    
with col2:
    avg_satisfaction = filtered_df["Satisfaction (Raw)"].mean()
    st.metric("Avg. Satisfaction", f"{avg_satisfaction:.1f}/10")

with col3:
    avg_correlation = filtered_df["Correlation Index"].mean()
    st.metric("Avg. Correlation", f"{avg_correlation:.3f}")

with col4:
    verified_pct = (filtered_df["Verified"].sum() / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
    st.metric("Verified %", f"{verified_pct:.1f}%")

with col5:
    unique_users = filtered_df["User ID"].nunique()
    st.metric("Unique Users", unique_users)

st.markdown("---")

# --- DATA TABLE ---
st.markdown("### 📋 Records")

# Format the dataframe for display
display_df = filtered_df.copy()
display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
display_df["Verified"] = display_df["Verified"].map({True: "✅", False: "❌"})

# Column configuration for better display
column_config = {
    "ID": st.column_config.TextColumn("ID", width="small"),
    "User ID": st.column_config.TextColumn("User ID", width="small"),
    "Date": st.column_config.TextColumn("Date", width="small"),
    "Topic Summary": st.column_config.TextColumn("Topic", width="medium"),
    "Satisfaction (Raw)": st.column_config.ProgressColumn(
        "Satisfaction",
        min_value=0,
        max_value=10,
        format="%d/10"
    ),
    "Satisfaction (Normalized)": st.column_config.NumberColumn(
        "Norm. Score",
        format="%.3f"
    ),
    "Correlation Index": st.column_config.ProgressColumn(
        "Correlation",
        min_value=0,
        max_value=1,
        format="%.2f"
    ),
    "Verified": st.column_config.TextColumn("Status", width="small"),
    "Source": st.column_config.TextColumn("Source", width="small")
}

# Display the data table
st.dataframe(
    display_df,
    column_config=column_config,
    use_container_width=True,
    hide_index=True,
    height=500
)

# Quick stats
st.markdown("---")
st.caption(f"Showing {len(filtered_df)} of {len(df)} total records • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

