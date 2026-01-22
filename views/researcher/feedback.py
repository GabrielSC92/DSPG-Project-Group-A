"""
Researcher View - Feedback Page
Displays user feedback submitted through the application.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Try to import database functions
try:
    from utils.database import get_all_feedback, is_database_connected
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Page header
header_col1, header_col2 = st.columns([4, 1])
with header_col2:
    st.image("Utrecht_University_logo_square.png", width=80)


def load_feedback_data() -> pd.DataFrame:
    """Load feedback from the database."""
    if not DB_AVAILABLE or not is_database_connected():
        return None

    feedbacks = get_all_feedback(limit=500)
    if not feedbacks:
        return None

    df = pd.DataFrame(feedbacks)

    # Rename columns for display
    df = df.rename(
        columns={
            'id': 'ID',
            'user_id': 'User ID',
            'user_email': 'User Email',
            'feedback_type': 'Type',
            'message': 'Message',
            'created_at': 'Submitted At'
        })

    return df


# Load data
df = load_feedback_data()

if df is None or len(df) == 0:
    st.info(
        ":material/inbox: No feedback has been submitted yet. Feedback will appear here once users start submitting.",
        icon=":material/feedback:")
else:
    # Summary metrics
    st.markdown("### Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Feedback", len(df))

    with col2:
        bug_count = len(df[df['Type'] == 'Bug Report'])
        st.metric("Bug Reports", bug_count)

    with col3:
        feature_count = len(df[df['Type'] == 'Feature Request'])
        st.metric("Feature Requests", feature_count)

    with col4:
        # Count feedback with user info (non-anonymous)
        identified = len(df[df['User Email'].notna()])
        st.metric("Identified Users", identified)

    st.markdown("---")

    # Filters
    st.markdown("### Filters")
    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        # Filter by type
        all_types = ['All'] + sorted(df['Type'].unique().tolist())
        selected_type = st.selectbox("Feedback Type",
                                     options=all_types,
                                     key="fb_type_filter")

    with filter_col2:
        # Filter by date range
        if 'Submitted At' in df.columns and df['Submitted At'].notna().any():
            min_date = pd.to_datetime(df['Submitted At']).min().date()
            max_date = pd.to_datetime(df['Submitted At']).max().date()
            date_range = st.date_input("Date Range",
                                       value=(min_date, max_date),
                                       key="fb_date_filter")
        else:
            date_range = None

    # Apply filters
    filtered_df = df.copy()

    if selected_type != 'All':
        filtered_df = filtered_df[filtered_df['Type'] == selected_type]

    if date_range and len(date_range) == 2:
        filtered_df['Submitted At'] = pd.to_datetime(
            filtered_df['Submitted At'])
        filtered_df = filtered_df[
            (filtered_df['Submitted At'].dt.date >= date_range[0])
            & (filtered_df['Submitted At'].dt.date <= date_range[1])]

    st.markdown("---")

    # Display feedback
    st.markdown(f"### Feedback Entries ({len(filtered_df)})")

    if len(filtered_df) == 0:
        st.warning("No feedback matches the selected filters.")
    else:
        # Sort by most recent first
        filtered_df = filtered_df.sort_values('Submitted At', ascending=False)

        # Display as expandable cards
        for _, row in filtered_df.iterrows():
            # Format timestamp
            timestamp = row['Submitted At']
            if pd.notna(timestamp):
                if isinstance(timestamp, str):
                    timestamp_str = timestamp
                else:
                    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M")
            else:
                timestamp_str = "Unknown"

            # User info
            user_info = row['User Email'] if pd.notna(
                row['User Email']) else "Anonymous"

            # Type badge color
            type_colors = {
                'Bug Report': '🔴',
                'Feature Request': '🟢',
                'General Feedback': '🔵',
                'Data Quality Issue': '🟠',
                'User Experience': '🟣',
                'Other': '⚪'
            }
            type_icon = type_colors.get(row['Type'], '⚪')

            with st.expander(
                    f"{type_icon} **{row['Type']}** - {timestamp_str} ({user_info})"
            ):
                st.markdown(f"**Message:**")
                st.markdown(f"> {row['Message']}")

                st.markdown("---")

                detail_col1, detail_col2, detail_col3 = st.columns(3)
                with detail_col1:
                    st.caption(f"**ID:** {row['ID']}")
                with detail_col2:
                    st.caption(
                        f"**User ID:** {row['User ID'] if pd.notna(row['User ID']) else 'N/A'}"
                    )
                with detail_col3:
                    st.caption(f"**Submitted:** {timestamp_str}")

        # Option to view as table
        st.markdown("---")
        if st.checkbox("Show as table", key="fb_show_table"):
            # Select columns for table view
            display_cols = [
                'ID', 'Type', 'Message', 'User Email', 'Submitted At'
            ]
            available_cols = [
                c for c in display_cols if c in filtered_df.columns
            ]
            st.dataframe(filtered_df[available_cols],
                         use_container_width=True,
                         hide_index=True)
