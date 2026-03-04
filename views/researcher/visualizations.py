"""
Researcher View - Visualizations Page
Interactive charts and graphs for analyzing quantitative indicators.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import numpy as np

try:
    from utils.database import get_all_interactions, get_available_topics, is_database_connected
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

header_col1, header_col2 = st.columns([4, 1])
with header_col2:
    st.image("Utrecht_University_logo_square.png", width=80)


def load_from_database() -> pd.DataFrame:
    """Load interaction data from the database for visualizations."""
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
        'interaction_date': 'Date',
        'topic': 'Topic',
        'satisfaction_raw': 'Satisfaction',
        'correlation_index': 'Quality Score',
        'verification_flag': 'Verified_raw'
    })

    df['Date'] = pd.to_datetime(df['Date'])
    df['Verified'] = df['Verified_raw'].apply(lambda x: x == 'V' if x else False)
    df['Source'] = df['Topic'].map(topic_source_map).fillna('Unknown')

    df = df.drop(columns=['Verified_raw', 'interaction_id', 'user_id', 'topic_id', 'summary'], errors='ignore')

    df['Satisfaction'] = pd.to_numeric(df['Satisfaction'], errors='coerce')
    df['Quality Score'] = pd.to_numeric(df['Quality Score'], errors='coerce')

    return df


def generate_demo_data(n_rows: int = 200) -> pd.DataFrame:
    """Generate demo data for visualizations (fallback when DB is unavailable)."""

    topics = {
        "Defence": "Defensie",
        "Climate": "Climate",
        "Finance": "Finance",
        "Healthcare": "Healthcare",
    }

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    data = {
        "Date": [
            start_date + timedelta(days=random.randint(0, 365))
            for _ in range(n_rows)
        ],
        "Topic": [random.choice(list(topics.keys())) for _ in range(n_rows)],
        "Satisfaction": [random.randint(1, 5) for _ in range(n_rows)],
        "Quality Score":
        [round(random.uniform(0.1, 1.0), 3) for _ in range(n_rows)],
        "Verified": [random.choice([True, False]) for _ in range(n_rows)]
    }

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Source"] = df["Topic"].map(topics)
    return df


@st.cache_data(ttl=60)
def get_visualization_data():
    """Load from database first, fall back to demo data."""
    db_data = load_from_database()
    if db_data is not None and len(db_data) > 0:
        return db_data, True
    return generate_demo_data(300), False


df, using_db = get_visualization_data()

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
    st.warning("No data available. Please interact with the chat to generate data, or check the database connection.")
    st.stop()

# --- VISUALIZATION CONTROLS ---
st.markdown("### :material/tune: Controls")

col1, col2, col3, col4 = st.columns(4)

with col1:
    chart_type = st.selectbox(
        "Chart Type",
        ["Time Series", "Distribution", "Comparison", "Correlation"],
        key="chart_type")

with col2:
    metric = st.selectbox("Metric", ["Satisfaction", "Quality Score"],
                          key="metric_select")

with col3:
    date_range = st.date_input("Date Range",
                               value=(df["Date"].min().date(),
                                      df["Date"].max().date()),
                               key="viz_date_range")

with col4:
    group_by = st.selectbox("Group By", ["Topic", "Source", "Month", "Week"],
                            key="group_by")

# Apply date filter
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = df[(df["Date"].dt.date >= start_date)
                     & (df["Date"].dt.date <= end_date)]
else:
    filtered_df = df

st.markdown("---")

colors = [
    "#FFCD00", "#3B82F6", "#8B5CF6", "#10B981", "#F59E0B", "#EF4444",
    "#06B6D4", "#EC4899"
]

# --- CHART RENDERING ---
if chart_type == "Time Series":
    st.markdown(f"### :material/bar_chart: {metric} Trends Over Time")

    ts_df = filtered_df.copy()

    if group_by == "Month":
        ts_df["Period"] = ts_df["Date"].dt.to_period("M").astype(str)
    elif group_by == "Week":
        ts_df["Period"] = ts_df["Date"].dt.to_period("W").astype(str)
    else:
        ts_df["Period"] = ts_df["Date"].dt.strftime("%Y-%m-%d")

    if group_by in ["Topic", "Source"]:
        agg_df = ts_df.groupby(["Period",
                                group_by])[metric].mean().reset_index()
        fig = px.line(agg_df,
                      x="Period",
                      y=metric,
                      color=group_by,
                      markers=True,
                      color_discrete_sequence=colors)
    else:
        agg_df = ts_df.groupby("Period")[metric].mean().reset_index()
        fig = px.line(agg_df,
                      x="Period",
                      y=metric,
                      markers=True,
                      color_discrete_sequence=colors)

    fig.update_layout(template="plotly_dark",
                      paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="DM Sans"),
                      xaxis_title="Period",
                      yaxis_title=metric,
                      legend=dict(orientation="h",
                                  yanchor="bottom",
                                  y=1.02,
                                  xanchor="right",
                                  x=1))
    fig.update_xaxes(showgrid=True,
                     gridwidth=1,
                     gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(showgrid=True,
                     gridwidth=1,
                     gridcolor='rgba(255,255,255,0.1)')

    st.plotly_chart(fig, use_container_width=True)

elif chart_type == "Distribution":
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### :material/bar_chart: Topic Distribution")
        topic_counts = filtered_df["Topic"].value_counts().reset_index()
        topic_counts.columns = ["Topic", "Count"]

        fig_pie = px.pie(topic_counts,
                         values="Count",
                         names="Topic",
                         color_discrete_sequence=colors,
                         hole=0.4)
        fig_pie.update_layout(template="plotly_dark",
                              paper_bgcolor="rgba(0,0,0,0)",
                              font=dict(family="DM Sans"),
                              legend=dict(orientation="h",
                                          yanchor="bottom",
                                          y=-0.3))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown(f"### :material/bar_chart: {metric} Distribution")
        if metric == "Satisfaction":
            hist_nbins = 5
            hist_xlabel = "Satisfaction Score (1-5)"
            hist_dtick = 1
        else:
            hist_nbins = 20
            hist_xlabel = "Quality Score (0-1)"
            hist_dtick = 0.1

        fig_hist = px.histogram(filtered_df,
                                x=metric,
                                nbins=hist_nbins,
                                color_discrete_sequence=[colors[0]])
        fig_hist.update_layout(template="plotly_dark",
                               paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)",
                               font=dict(family="DM Sans"),
                               xaxis_title=hist_xlabel,
                               yaxis_title="Frequency",
                               bargap=0.1)
        fig_hist.update_xaxes(showgrid=True,
                              gridwidth=1,
                              gridcolor='rgba(255,255,255,0.1)',
                              dtick=hist_dtick)
        fig_hist.update_yaxes(showgrid=True,
                              gridwidth=1,
                              gridcolor='rgba(255,255,255,0.1)')
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("### :material/bar_chart: Records by Source")
    source_counts = filtered_df["Source"].value_counts().reset_index()
    source_counts.columns = ["Source", "Count"]

    fig_bar = px.bar(source_counts,
                     x="Source",
                     y="Count",
                     color="Source",
                     color_discrete_sequence=colors)
    fig_bar.update_layout(template="plotly_dark",
                          paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="DM Sans"),
                          showlegend=False)
    fig_bar.update_xaxes(showgrid=False)
    fig_bar.update_yaxes(showgrid=True,
                         gridwidth=1,
                         gridcolor='rgba(255,255,255,0.1)')
    st.plotly_chart(fig_bar, use_container_width=True)

elif chart_type == "Comparison":
    st.markdown(f"### :material/bar_chart: {metric} by Topic")

    fig_box = px.box(filtered_df,
                     x="Topic",
                     y=metric,
                     color="Topic",
                     color_discrete_sequence=colors)
    fig_box.update_layout(template="plotly_dark",
                          paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="DM Sans"),
                          xaxis_title="",
                          showlegend=False,
                          xaxis_tickangle=-45)
    fig_box.update_xaxes(showgrid=False)
    fig_box.update_yaxes(showgrid=True,
                         gridwidth=1,
                         gridcolor='rgba(255,255,255,0.1)')
    st.plotly_chart(fig_box, use_container_width=True)

    st.markdown(
        f"### :material/bar_chart: Average {metric} by Source & Verification Status"
    )
    comparison_df = filtered_df.groupby(
        ["Source", "Verified"])[metric].mean().reset_index()
    comparison_df["Verified"] = comparison_df["Verified"].map({
        True: "Verified",
        False: "Unverified"
    })

    fig_grouped = px.bar(comparison_df,
                         x="Source",
                         y=metric,
                         color="Verified",
                         barmode="group",
                         color_discrete_sequence=[colors[4], colors[5]])
    fig_grouped.update_layout(template="plotly_dark",
                              paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(family="DM Sans"),
                              legend=dict(orientation="h",
                                          yanchor="bottom",
                                          y=1.02,
                                          xanchor="right",
                                          x=1))
    fig_grouped.update_xaxes(showgrid=False)
    fig_grouped.update_yaxes(showgrid=True,
                             gridwidth=1,
                             gridcolor='rgba(255,255,255,0.1)')
    st.plotly_chart(fig_grouped, use_container_width=True)

elif chart_type == "Correlation":
    st.markdown("### :material/grid_on: Topic Average Metrics")

    pivot_df = filtered_df.pivot_table(
        values=["Satisfaction", "Quality Score"],
        index="Topic",
        aggfunc="mean"
    ).dropna()

    if len(pivot_df) >= 2:
        topic_labels = pivot_df.index.tolist()

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns.tolist(),
            y=topic_labels,
            colorscale=[[0, "#0F172A"], [0.5, "#3B82F6"], [1, "#FFCD00"]],
            text=np.round(pivot_df.values, 2),
            texttemplate="%{text}",
            textfont={"size": 12},
            hovertemplate="Topic: %{y}<br>Metric: %{x}<br>Value: %{z:.2f}<extra></extra>"
        ))

        fig_heatmap.update_layout(template="plotly_dark",
                                  paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(family="DM Sans"),
                                  xaxis_title="Metric",
                                  yaxis_title="Topic",
                                  height=max(400, len(topic_labels) * 60))

        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.info("Need at least 2 topics with data to show the heatmap.")

    st.markdown("### :material/bar_chart: Satisfaction vs Quality Score")

    scatter_df = filtered_df.dropna(subset=["Quality Score", "Satisfaction"])
    if len(scatter_df) > 0:
        fig_scatter = px.scatter(scatter_df,
                                 x="Quality Score",
                                 y="Satisfaction",
                                 color="Topic",
                                 size="Satisfaction",
                                 color_discrete_sequence=colors,
                                 opacity=0.7)
        fig_scatter.update_layout(template="plotly_dark",
                                  paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(family="DM Sans"),
                                  legend=dict(orientation="h",
                                              yanchor="bottom",
                                              y=-0.3))
        fig_scatter.update_xaxes(showgrid=True,
                                 gridwidth=1,
                                 gridcolor='rgba(255,255,255,0.1)')
        fig_scatter.update_yaxes(showgrid=True,
                                 gridwidth=1,
                                 gridcolor='rgba(255,255,255,0.1)')
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No records with both Satisfaction and Quality Score available for scatter plot.")

# Footer
st.markdown("---")
data_label = "live database" if using_db else "demo data"
st.caption(
    f"Visualizing {len(filtered_df)} records from {data_label} • Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
