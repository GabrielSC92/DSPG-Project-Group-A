"""
Researcher View - Export Page
Export data and visualizations in various formats.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import io

# Page configuration with logo
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.markdown("""
    <div class="page-header">
        <h1>Export Data</h1>
        <p>Download quantitative indicators and reports in various formats</p>
    </div>
    """,
                unsafe_allow_html=True)
with header_col2:
    st.image("Utrecht_University_logo_square.png", width=80)


def generate_demo_data(n_rows: int = 200) -> pd.DataFrame:
    """Generate demo data for export."""

    topics = [
        "Financial Management", "Policy Effectiveness",
        "Administrative Efficiency", "Service Delivery",
        "Transparency & Accountability", "Human Resources",
        "Digital Transformation", "Citizen Engagement"
    ]

    sources = ["Court of Audit", "Auditdienst Rijk", "IOB"]

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    data = {
        "ID": [f"QRY_{str(i).zfill(5)}" for i in range(1, n_rows + 1)],
        "User ID":
        [f"USR_{str(random.randint(1, 50)).zfill(3)}" for _ in range(n_rows)],
        "Date": [
            start_date + timedelta(days=random.randint(0, 365))
            for _ in range(n_rows)
        ],
        "Topic Summary": [random.choice(topics) for _ in range(n_rows)],
        "Satisfaction (Raw)": [random.randint(1, 10) for _ in range(n_rows)],
        "Satisfaction (Normalized)":
        [round(random.uniform(0, 1), 3) for _ in range(n_rows)],
        "Response Quality Score":
        [round(random.uniform(0.5, 1.0), 3) for _ in range(n_rows)],
        "Verified": [random.choice([True, False]) for _ in range(n_rows)],
        "Source": [random.choice(sources) for _ in range(n_rows)]
    }

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values("Date", ascending=False).reset_index(drop=True)


@st.cache_data
def get_export_data():
    return generate_demo_data(200)


# Load data
df = get_export_data()

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
    all_topics = df["Topic Summary"].unique().tolist()
    selected_topics = st.multiselect("Select topics",
                                     options=all_topics,
                                     default=all_topics,
                                     key="export_topics",
                                     label_visibility="collapsed")

col3, col4 = st.columns(2)

with col3:
    st.markdown("#### :material/source: Sources")
    all_sources = df["Source"].unique().tolist()
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

# Apply filters to create export dataset
filtered_df = df.copy()

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[(filtered_df["Date"].dt.date >= start_date)
                              & (filtered_df["Date"].dt.date <= end_date)]

if selected_topics:
    filtered_df = filtered_df[filtered_df["Topic Summary"].isin(
        selected_topics)]

if selected_sources:
    filtered_df = filtered_df[filtered_df["Source"].isin(selected_sources)]

if verification_option == "Verified Only":
    filtered_df = filtered_df[filtered_df["Verified"] == True]
elif verification_option == "Unverified Only":
    filtered_df = filtered_df[filtered_df["Verified"] == False]

st.markdown("---")

# --- DATA PREVIEW ---
st.markdown("### :material/visibility: Preview")

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
            <p style="color: #F1F5F9; font-size: 1.5rem; font-weight: 600; margin: 0;">{filtered_df['User ID'].nunique()}</p>
        </div>
        <div>
            <span style="color: #94A3B8; font-size: 0.8rem;">Topics</span>
            <p style="color: #F1F5F9; font-size: 1.5rem; font-weight: 600; margin: 0;">{filtered_df['Topic Summary'].nunique()}</p>
        </div>
        <div>
            <span style="color: #94A3B8; font-size: 0.8rem;">Date Range</span>
            <p style="color: #F1F5F9; font-size: 1rem; font-weight: 500; margin: 0;">
                {filtered_df['Date'].min().strftime('%Y-%m-%d')} to {filtered_df['Date'].max().strftime('%Y-%m-%d')}
            </p>
        </div>
    </div>
</div>
""",
            unsafe_allow_html=True)

# Show preview
preview_df = filtered_df.head(10).copy()
preview_df["Date"] = preview_df["Date"].dt.strftime("%Y-%m-%d")
st.dataframe(preview_df, use_container_width=True, hide_index=True)

if len(filtered_df) > 10:
    st.caption(f"Showing 10 of {len(filtered_df)} records")

st.markdown("---")

# --- EXPORT FORMATS ---
st.markdown("### :material/download: Download")

col1, col2, col3 = st.columns(3)

# Prepare export data
export_df = filtered_df.copy()
export_df["Date"] = export_df["Date"].dt.strftime("%Y-%m-%d")

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

    # Create Excel file in memory
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

    summary_stats = {
        "Metric": [
            "Total Records", "Unique Users", "Date Range",
            "Mean Satisfaction (Raw)", "Median Satisfaction (Raw)",
            "Mean Quality Score (RQS)", "Verified Records %",
            "Most Common Topic", "Most Common Source"
        ],
        "Value": [
            str(len(filtered_df)),
            str(filtered_df['User ID'].nunique()),
            f"{filtered_df['Date'].min().strftime('%Y-%m-%d')} to {filtered_df['Date'].max().strftime('%Y-%m-%d')}",
            f"{filtered_df['Satisfaction (Raw)'].mean():.2f}",
            f"{filtered_df['Satisfaction (Raw)'].median():.1f}",
            f"{filtered_df['Response Quality Score'].mean():.3f}",
            f"{(filtered_df['Verified'].sum() / len(filtered_df) * 100):.1f}%",
            filtered_df['Topic Summary'].mode().iloc[0] if len(filtered_df) > 0
            else "N/A", filtered_df['Source'].mode().iloc[0]
            if len(filtered_df) > 0 else "N/A"
        ]
    }

    summary_df = pd.DataFrame(summary_stats)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # Download summary
    summary_csv = summary_df.to_csv(index=False)
    st.download_button(
        label=":material/download: Download Summary Report",
        data=summary_csv,
        file_name=f"qog_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="summary_download")

# Footer
st.markdown("---")
st.caption(
    f"Export generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Data freshness: Demo data"
)
