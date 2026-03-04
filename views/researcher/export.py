"""
Researcher View - Export Page
Export data and visualizations in various formats.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import io

try:
    from utils.database import get_all_interactions, get_available_topics, is_database_connected
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

header_col1, header_col2 = st.columns([4, 1])
with header_col2:
    st.image("Utrecht_University_logo_square.png", width=80)


def load_from_database() -> pd.DataFrame:
    """Load interaction data from the database for export."""
    if not DB_AVAILABLE or not is_database_connected():
        return None

    interactions = get_all_interactions(limit=5000)
    if not interactions:
        return None

    df = pd.DataFrame(interactions)

    topics_list = get_available_topics()
    topic_source_map = {}
    if topics_list:
        for t in topics_list:
            folder = t.get('source_folder', '')
            topic_source_map[t['label_en']] = folder.replace('_', ' ').title()

    df = df.rename(columns={
        'interaction_id': 'ID',
        'user_id': 'User ID',
        'interaction_date': 'Date',
        'topic': 'Topic',
        'summary': 'Subtopic',
        'satisfaction_raw': 'Satisfaction (Raw)',
        'correlation_index': 'Response Quality Score',
        'verification_flag': 'Verified_raw'
    })

    df['Date'] = pd.to_datetime(df['Date'])
    df['Verified'] = df['Verified_raw'].apply(lambda x: x == 'V' if x else False)
    df['Source'] = df['Topic'].map(topic_source_map).fillna('Unknown')

    df['Satisfaction (Raw)'] = pd.to_numeric(df['Satisfaction (Raw)'], errors='coerce')
    df['Response Quality Score'] = pd.to_numeric(df['Response Quality Score'], errors='coerce')

    df = df.drop(columns=['Verified_raw', 'topic_id'], errors='ignore')

    return df.sort_values("Date", ascending=False).reset_index(drop=True)


def generate_demo_data(n_rows: int = 200) -> pd.DataFrame:
    """Generate demo data for export (fallback when DB is unavailable)."""

    topics = {
        "Defence": ["Submarine Procurement", "Military Budget", "Cybersecurity", "Personnel"],
        "Climate": ["Energy Transition", "Climate Monitoring", "Policy Impact", "Citizen Council"],
    }

    topic_source_map = {"Defence": "Defensie", "Climate": "Climate"}
    topic_list = list(topics.keys())

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    rows = []
    for i in range(n_rows):
        topic = random.choice(topic_list)
        rows.append({
            "ID": f"QRY_{str(i + 1).zfill(5)}",
            "User ID": f"USR_{str(random.randint(1, 50)).zfill(3)}",
            "Date": start_date + timedelta(days=random.randint(0, 365)),
            "Topic": topic,
            "Subtopic": random.choice(topics[topic]),
            "Satisfaction (Raw)": random.randint(1, 5),
            "Response Quality Score": round(random.uniform(0.1, 1.0), 3),
            "Verified": random.choice([True, False]),
            "Source": topic_source_map[topic],
        })

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values("Date", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=60)
def get_export_data():
    """Load from database first, fall back to demo data."""
    db_data = load_from_database()
    if db_data is not None and len(db_data) > 0:
        return db_data, True
    return generate_demo_data(200), False


df, using_db = get_export_data()

with st.sidebar:
    if using_db:
        st.markdown("""
        <div style="display: flex; justify-content: center; margin: 0.5rem 0;">
            <span style="
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.75rem;
                font-family: 'Space Mono', monospace;
                background: rgba(34, 197, 94, 0.15);
                border: 1px solid rgba(34, 197, 94, 0.3);
                color: #4ade80;
            ">
                <span style="
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #4ade80;
                    box-shadow: 0 0 8px #4ade80;
                    animation: pulse 2s infinite;
                "></span>
                DB Connected
            </span>
        </div>
        <style>
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display: flex; justify-content: center; margin: 0.5rem 0;">
            <span style="
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.75rem;
                font-family: 'Space Mono', monospace;
                background: rgba(239, 68, 68, 0.15);
                border: 1px solid rgba(239, 68, 68, 0.3);
                color: #f87171;
            ">
                <span style="
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #f87171;
                "></span>
                DB Demo
            </span>
        </div>
        """, unsafe_allow_html=True)

if len(df) == 0:
    st.warning("No data available for export. Please interact with the chat to generate data, or check the database connection.")
    st.stop()

# --- EXPORT CONFIGURATION ---
st.markdown("### :material/folder_open: Select Data to Export")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### :material/calendar_today: Date Range")
    date_range = st.date_input("Select date range",
                               value=(df["Date"].min().date(),
                                      df["Date"].max().date()),
                               key="export_date_range",
                               label_visibility="collapsed")

with col2:
    st.markdown("#### :material/topic: Topics")
    all_topics = sorted(df["Topic"].unique().tolist())
    selected_topics = st.multiselect("Select topics",
                                     options=all_topics,
                                     default=all_topics,
                                     key="export_topics",
                                     label_visibility="collapsed")

col3, col4 = st.columns(2)

with col3:
    st.markdown("#### :material/source: Sources")
    all_sources = sorted(df["Source"].unique().tolist())
    selected_sources = st.multiselect("Select sources",
                                      options=all_sources,
                                      default=all_sources,
                                      key="export_sources",
                                      label_visibility="collapsed")

with col4:
    st.markdown("#### :material/verified: Verification Status")
    verification_option = st.radio(
        "Select verification status",
        options=["All", "Verified Only", "Unverified Only"],
        horizontal=True,
        key="export_verification",
        label_visibility="collapsed")

# Apply filters
filtered_df = df.copy()

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[(filtered_df["Date"].dt.date >= start_date)
                              & (filtered_df["Date"].dt.date <= end_date)]

if selected_topics:
    filtered_df = filtered_df[filtered_df["Topic"].isin(selected_topics)]

if selected_sources:
    filtered_df = filtered_df[filtered_df["Source"].isin(selected_sources)]

if verification_option == "Verified Only":
    filtered_df = filtered_df[filtered_df["Verified"] == True]
elif verification_option == "Unverified Only":
    filtered_df = filtered_df[filtered_df["Verified"] == False]

st.markdown("---")

# --- DATA PREVIEW ---
st.markdown("### :material/visibility: Preview")

if len(filtered_df) > 0:
    n_topics = filtered_df['Topic'].nunique()
    date_min = filtered_df['Date'].min().strftime('%Y-%m-%d')
    date_max = filtered_df['Date'].max().strftime('%Y-%m-%d')
else:
    n_topics = 0
    date_min = "N/A"
    date_max = "N/A"

st.markdown(f"""
<div style="
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
">
    <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
        <div>
            <span style="color: #94A3B8; font-size: 0.8rem;">Total Records</span>
            <p style="color: #F1F5F9; font-size: 1.5rem; font-weight: 600; margin: 0;">{len(filtered_df)}</p>
        </div>
        <div>
            <span style="color: #94A3B8; font-size: 0.8rem;">Unique Users</span>
            <p style="color: #F1F5F9; font-size: 1.5rem; font-weight: 600; margin: 0;">{filtered_df['User ID'].nunique() if len(filtered_df) > 0 else 0}</p>
        </div>
        <div>
            <span style="color: #94A3B8; font-size: 0.8rem;">Topics</span>
            <p style="color: #F1F5F9; font-size: 1.5rem; font-weight: 600; margin: 0;">{n_topics}</p>
        </div>
        <div>
            <span style="color: #94A3B8; font-size: 0.8rem;">Date Range</span>
            <p style="color: #F1F5F9; font-size: 1rem; font-weight: 500; margin: 0;">
                {date_min} to {date_max}
            </p>
        </div>
    </div>
</div>
""",
            unsafe_allow_html=True)

if len(filtered_df) > 0:
    preview_df = filtered_df.head(10).copy()
    preview_df["Date"] = preview_df["Date"].dt.strftime("%Y-%m-%d")
    preview_df["Verified"] = preview_df["Verified"].map({True: "Yes", False: "No"})
    st.dataframe(preview_df, use_container_width=True, hide_index=True)

    if len(filtered_df) > 10:
        st.caption(f"Showing 10 of {len(filtered_df)} records")
else:
    st.info("No records match your current filters.")

st.markdown("---")

# --- EXPORT FORMATS ---
st.markdown("### :material/download: Download")

col1, col2, col3 = st.columns(3)

export_df = filtered_df.copy()
if len(export_df) > 0:
    export_df["Date"] = export_df["Date"].dt.strftime("%Y-%m-%d")
    export_df["Verified"] = export_df["Verified"].map({True: "Yes", False: "No"})

with col1:
    st.markdown("""
    <div style="
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        margin-bottom: 0.5rem;
    ">
        <p style="font-size: 2rem; margin: 0;">📄</p>
        <p style="color: #F1F5F9; font-weight: 600; margin: 0.5rem 0;">CSV Format</p>
        <p style="color: #94A3B8; font-size: 0.8rem; margin: 0;">Best for data analysis</p>
    </div>
    """,
                unsafe_allow_html=True)

    csv_data = export_df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name=f"qog_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
        key="csv_download")

with col2:
    st.markdown("""
    <div style="
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        margin-bottom: 0.5rem;
    ">
        <p style="font-size: 2rem; margin: 0;">📊</p>
        <p style="color: #F1F5F9; font-weight: 600; margin: 0.5rem 0;">Excel Format</p>
        <p style="color: #94A3B8; font-size: 0.8rem; margin: 0;">Best for reporting</p>
    </div>
    """,
                unsafe_allow_html=True)

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='QoG Data')
    excel_data = excel_buffer.getvalue()

    st.download_button(
        label="Download Excel",
        data=excel_data,
        file_name=f"qog_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="excel_download")

with col3:
    st.markdown("""
    <div style="
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        margin-bottom: 0.5rem;
    ">
        <p style="font-size: 2rem; margin: 0;">🔗</p>
        <p style="color: #F1F5F9; font-weight: 600; margin: 0.5rem 0;">JSON Format</p>
        <p style="color: #94A3B8; font-size: 0.8rem; margin: 0;">Best for integration</p>
    </div>
    """,
                unsafe_allow_html=True)

    json_data = export_df.to_json(orient='records', indent=2)
    st.download_button(
        label="Download JSON",
        data=json_data,
        file_name=f"qog_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True,
        key="json_download")

st.markdown("---")

# --- SUMMARY REPORT ---
st.markdown("### :material/summarize: Summary Report")

with st.expander("Generate Summary Statistics Report"):
    st.markdown("#### Aggregated Statistics")

    if len(filtered_df) > 0:
        mean_sat = f"{filtered_df['Satisfaction (Raw)'].mean():.2f}"
        median_sat = f"{filtered_df['Satisfaction (Raw)'].median():.1f}"
        mean_rqs = f"{filtered_df['Response Quality Score'].mean():.3f}" if filtered_df['Response Quality Score'].notna().any() else "N/A"
        verified_pct = f"{(filtered_df['Verified'].sum() / len(filtered_df) * 100):.1f}%"
        top_topic = filtered_df['Topic'].mode().iloc[0]
        top_source = filtered_df['Source'].mode().iloc[0]
    else:
        mean_sat = median_sat = mean_rqs = verified_pct = "N/A"
        top_topic = top_source = "N/A"

    summary_stats = {
        "Metric": [
            "Total Records", "Unique Users", "Date Range",
            "Mean Satisfaction (Raw)", "Median Satisfaction (Raw)",
            "Mean Quality Score (RQS)", "Verified Records %",
            "Most Common Topic", "Most Common Source"
        ],
        "Value": [
            str(len(filtered_df)),
            str(filtered_df['User ID'].nunique()) if len(filtered_df) > 0 else "0",
            f"{date_min} to {date_max}",
            mean_sat,
            median_sat,
            mean_rqs,
            verified_pct,
            top_topic,
            top_source
        ]
    }

    summary_df = pd.DataFrame(summary_stats)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    summary_csv = summary_df.to_csv(index=False)
    st.download_button(
        label=":material/download: Download Summary Report",
        data=summary_csv,
        file_name=f"qog_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="summary_download")

# Footer
st.markdown("---")
data_label = "live database" if using_db else "demo data"
st.caption(
    f"Export generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Data source: {data_label}"
)
