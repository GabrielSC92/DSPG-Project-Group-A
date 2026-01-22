"""
Researcher View - Data Table Page
Displays quantitative data extracted from government reports with filtering capabilities.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# Import the metric card component
from components.single_metric_card import render_metric_row

# Try to import database functions
try:
    from utils.database import get_all_interactions, is_database_connected
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Page configuration with logo
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.markdown("""
    <div class="page-header">
        <h1>Data Table</h1>
        <p>View and analyze quantitative indicators extracted from government reports</p>
    </div>
    """,
                unsafe_allow_html=True)
with header_col2:
    st.image("Utrecht_University_logo_square.png", width=80)

# Privacy note
st.info(
    ":material/warning: **Privacy Notice**: Raw chat content is never stored. Only synthesized summaries and metrics are available for analysis.",
    icon=":material/lock:")


def calculate_user_normalized_satisfaction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate user-normalized satisfaction scores per Topic.
    
    Each user gets one "vote" per topic = their average satisfaction on that topic.
    This prevents a single user from skewing metrics by spamming queries.
    """
    if df is None or len(df) == 0 or "Topic" not in df.columns:
        return df

    # Calculate mean satisfaction per (User ID, Topic)
    df['User-Norm. Score'] = df.groupby(
        ['User ID', 'Topic'])['Satisfaction (Raw)'].transform('mean').round(2)
    df['User Topic Queries'] = df.groupby(
        ['User ID',
         'Topic'])['Satisfaction (Raw)'].transform('count').astype(int)

    return df


def load_from_database() -> pd.DataFrame:
    """Load data from the database."""
    if not DB_AVAILABLE or not is_database_connected():
        return None

    interactions = get_all_interactions(limit=1000)
    if not interactions:
        return None

    df = pd.DataFrame(interactions)

    # Rename columns to match display format
    df = df.rename(
        columns={
            'interaction_id': 'ID',
            'user_id': 'User ID',
            'interaction_date': 'Date',
            'topic': 'Topic',  # Now comes from topics table join
            'summary': 'Subtopic',
            'satisfaction_raw': 'Satisfaction (Raw)',
            'correlation_index': 'Response Quality Score',
            'verification_flag': 'Verified'
        })

    # Convert verification flag to boolean
    df['Verified'] = df['Verified'].apply(lambda x: x == 'V' if x else False)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Source'] = 'User Interaction'

    df = calculate_user_normalized_satisfaction(df)
    return df


def generate_demo_data(n_rows: int = 150) -> pd.DataFrame:
    """Generate demo data with separate Topic and Subtopic columns."""

    # Topics with their subtopics
    topics = {
        "Defence": [
            "Border Control", "Submarine Procurement", "Military Budget",
            "Cybersecurity", "Personnel"
        ],
        "Finance": [
            "Budget Oversight", "Expenditure Audits", "Cost Reduction",
            "Financial Reporting"
        ],
        "Healthcare": [
            "Hospital Efficiency", "Medication Costs", "Wait Times",
            "Emergency Response"
        ],
        "Education": [
            "School Performance", "Teacher Training", "Digital Learning",
            "Student Outcomes"
        ],
        "Infrastructure": [
            "Road Maintenance", "Public Transport", "Bridge Safety",
            "Urban Planning"
        ],
        "Environment": [
            "Climate Policy", "Waste Management", "Air Quality",
            "Renewable Energy"
        ]
    }

    topic_list = list(topics.keys())
    n_users = max(12, n_rows // 10)
    users = [f"USR_{str(i).zfill(3)}" for i in range(1, n_users + 1)]

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    # Track user-topic history for realistic repeat queries
    user_topic_history = {}

    rows = []
    for i in range(n_rows):
        # 30% chance of repeat query on same topic
        if i > 0 and random.random() < 0.3 and user_topic_history:
            user_id, topic = random.choice(list(user_topic_history.keys()))
            base_score = sum(user_topic_history[(user_id, topic)]) / len(
                user_topic_history[(user_id, topic)])
            satisfaction = max(
                1, min(5,
                       int(round(base_score)) + random.randint(-1, 1)))
        else:
            user_id = random.choice(users)
            topic = random.choice(topic_list)
            satisfaction = random.randint(1, 5)

        subtopic = random.choice(topics[topic])

        # Track history
        key = (user_id, topic)
        if key not in user_topic_history:
            user_topic_history[key] = []
        user_topic_history[key].append(satisfaction)

        rows.append({
            "ID":
            f"QRY_{str(i+1).zfill(5)}",
            "User ID":
            user_id,
            "Date":
            start_date + timedelta(days=random.randint(0, 365)),
            "Topic":
            topic,
            "Subtopic":
            subtopic,
            "Satisfaction (Raw)":
            satisfaction,
            "Response Quality Score":
            round(random.uniform(0.5, 1.0), 3),
            "Verified":
            random.choice([True, False]),
            "Source":
            random.choice(["Court of Audit", "Auditdienst Rijk", "IOB"])
        })

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date", ascending=False).reset_index(drop=True)
    df = calculate_user_normalized_satisfaction(df)
    return df


@st.cache_data(ttl=60)
def get_data():
    """Load data from database or generate demo data."""
    db_data = load_from_database()
    if db_data is not None and len(db_data) > 0:
        return db_data, True
    return generate_demo_data(150), False


# Load data
df, using_db = get_data()

# Show data source indicator
if using_db:
    st.success(f":material/bar_chart: Showing {len(df)} records from database",
               icon=":material/check_circle:")
else:
    st.warning(
        ":material/bar_chart: Showing demo data (database empty or not connected)",
        icon=":material/warning:")

# --- FILTERS ---
st.markdown("### :material/filter_list: Filters")

col1, col2, col3, col4 = st.columns(4)

with col1:
    date_range = st.date_input("Date Range",
                               value=(df["Date"].min().date(),
                                      df["Date"].max().date()),
                               key="date_filter")

with col2:
    topic_options = ["All"] + sorted(df["Topic"].unique().tolist())
    selected_topic = st.selectbox("Topic", topic_options, key="topic_filter")

with col3:
    users = ["All"] + sorted(df["User ID"].unique().tolist())
    selected_user = st.selectbox("User ID", users, key="user_filter")

with col4:
    verification_options = ["All", "Verified Only", "Unverified Only"]
    selected_verification = st.selectbox("Status",
                                         verification_options,
                                         key="verification_filter")

search_term = st.text_input(":material/search: Search",
                            placeholder="Search across all columns...",
                            key="search_box")

# Apply filters
filtered_df = df.copy()

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[(filtered_df["Date"].dt.date >= start_date)
                              & (filtered_df["Date"].dt.date <= end_date)]

if selected_topic != "All":
    filtered_df = filtered_df[filtered_df["Topic"] == selected_topic]

if selected_user != "All":
    filtered_df = filtered_df[filtered_df["User ID"] == selected_user]

if selected_verification == "Verified Only":
    filtered_df = filtered_df[filtered_df["Verified"] == True]
elif selected_verification == "Unverified Only":
    filtered_df = filtered_df[filtered_df["Verified"] == False]

if search_term:
    mask = filtered_df.astype(str).apply(lambda x: x.str.lower().str.contains(
        search_term.lower(), na=False)).any(axis=1)
    filtered_df = filtered_df[mask]

st.markdown("---")

# --- METRICS EXPLANATION ---
with st.expander(":material/info: Understanding the Metrics", expanded=False):
    st.markdown("""
    ### User-Normalized Satisfaction
    Prevents users from skewing metrics by submitting many queries on the same topic.
    
    **How it works:** Each user gets **one vote per topic** = their average satisfaction for that topic.
    
    **Example:**
    - User A queries "Defence" 5 times with scores: 5, 5, 5, 4, 5 → User A's vote = 4.8
    - User B queries "Defence" 1 time with score: 2 → User B's vote = 2.0
    - **Raw average**: (5+5+5+4+5+2) / 6 = 4.33 — User A dominates
    - **Normalized average**: (4.8 + 2.0) / 2 = **3.4** — each user counts equally
    
    ---
    
    ### Response Quality Score (RQS)
    Measures how well the system answered a user's question based on source citations, 
    response length, and relevance. Score ≥0.30 = Verified (✅).
    """)

# --- METRICS ROW ---
avg_satisfaction = filtered_df["Satisfaction (Raw)"].mean() if len(
    filtered_df) > 0 else 0
avg_quality = filtered_df["Response Quality Score"].mean() if len(
    filtered_df) > 0 else 0
verified_pct = (filtered_df["Verified"].sum() / len(filtered_df) *
                100) if len(filtered_df) > 0 else 0
unique_users = filtered_df["User ID"].nunique()

# Calculate normalized average (one vote per user-topic pair)
if len(filtered_df) > 0 and "User-Norm. Score" in filtered_df.columns:
    user_topic_votes = filtered_df.groupby(['User ID', 'Topic'
                                            ])['User-Norm. Score'].first()
    avg_normalized = user_topic_votes.mean() if len(
        user_topic_votes) > 0 else 0
    n_votes = len(user_topic_votes)
else:
    avg_normalized = avg_satisfaction
    n_votes = 0

metrics = [
    {
        "label": "Total Records",
        "value": str(len(filtered_df)),
        "icon": "",
        "color": "#3b82f6",
        "help_text": "Total records matching filters"
    },
    {
        "label": "Avg. Satisfaction (Raw)",
        "value": f"{avg_satisfaction:.1f}/5",
        "icon": "",
        "color": "#f59e0b",
        "help_text": "Simple average (can be skewed by repeat queries)"
    },
    {
        "label":
        "Avg. Satisfaction (Norm.)",
        "value":
        f"{avg_normalized:.2f}/5",
        "icon":
        "",
        "color":
        "#10b981",
        "help_text":
        f"User-normalized: each user gets one vote per topic ({n_votes} votes)"
    },
    {
        "label": "Avg. Quality Score",
        "value": f"{avg_quality:.3f}",
        "icon": "",
        "color": "#8b5cf6",
        "help_text": "Average Response Quality Score"
    },
    {
        "label": "Verified %",
        "value": f"{verified_pct:.1f}%",
        "icon": "",
        "color": "#ec4899",
        "help_text": "Percentage of verified records"
    },
    {
        "label": "Unique Users",
        "value": str(unique_users),
        "icon": "",
        "color": "#6366f1",
        "help_text": "Number of unique users"
    },
]

render_metric_row(metrics, height=115)

st.markdown("---")

# --- DATA TABLE ---
st.markdown("### :material/list: Records")

display_df = filtered_df.copy()
display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
display_df["Verified"] = display_df["Verified"].map({True: "✅", False: "❌"})

column_config = {
    "ID":
    st.column_config.TextColumn("ID", width="small"),
    "User ID":
    st.column_config.TextColumn("User ID", width="small"),
    "Date":
    st.column_config.TextColumn("Date", width="small"),
    "Topic":
    st.column_config.TextColumn("Topic", width="small"),
    "Subtopic":
    st.column_config.TextColumn("Subtopic", width="medium"),
    "Satisfaction (Raw)":
    st.column_config.ProgressColumn("Raw Score",
                                    min_value=1,
                                    max_value=5,
                                    format="%d/5"),
    "User-Norm. Score":
    st.column_config.ProgressColumn("Norm. Score",
                                    min_value=1,
                                    max_value=5,
                                    format="%.1f/5",
                                    help="User's average for this topic"),
    "User Topic Queries":
    st.column_config.NumberColumn("# Queries",
                                  format="%d",
                                  help="User's query count for this topic"),
    "Response Quality Score":
    st.column_config.ProgressColumn("Quality",
                                    min_value=0,
                                    max_value=1,
                                    format="%.2f"),
    "Verified":
    st.column_config.TextColumn("Status", width="small"),
    "Source":
    st.column_config.TextColumn("Source", width="small"),
    "topic_id":
    None  # Hide the raw ID column
}

st.dataframe(display_df,
             column_config=column_config,
             use_container_width=True,
             hide_index=True,
             height=500)

st.markdown("---")
st.caption(
    f"Showing {len(filtered_df)} of {len(df)} total records • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
