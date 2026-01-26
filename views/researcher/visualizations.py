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

# Page configuration with logo
header_col1, header_col2 = st.columns([4, 1])
with header_col2:
    st.image("Utrecht_University_logo_square.png", width=80)


def generate_demo_data(n_rows: int = 200) -> pd.DataFrame:
    """Generate demo data for visualizations."""

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
        "Date": [
            start_date + timedelta(days=random.randint(0, 365))
            for _ in range(n_rows)
        ],
        "Topic": [random.choice(topics) for _ in range(n_rows)],
        "Satisfaction": [random.randint(1, 10) for _ in range(n_rows)],
        "Quality Score":
        [round(random.uniform(0.5, 1.0), 3) for _ in range(n_rows)],
        "Source": [random.choice(sources) for _ in range(n_rows)],
        "Verified": [random.choice([True, False]) for _ in range(n_rows)]
    }

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


@st.cache_data
def get_visualization_data():
    return generate_demo_data(300)


# Load data
df = get_visualization_data()

# --- VISUALIZATION CONTROLS ---
st.markdown("### :material/tune: Controls")

col1, col2, col3, col4, col5 = st.columns(5)

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

with col5:
    color_scheme = st.selectbox("Color Scheme", ["Dutch Theme", "Rainbow"],
                                key="color_scheme")

# Apply date filter
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = df[(df["Date"].dt.date >= start_date)
                     & (df["Date"].dt.date <= end_date)]
else:
    filtered_df = df

st.markdown("---")

# Define color palettes
dutch_theme_colors = [
    "#FFCD00", "#3B82F6", "#8B5CF6", "#10B981", "#F59E0B", "#EF4444",
    "#06B6D4", "#EC4899"
]

rainbow_colors = [
    "#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082",
    "#9400D3", "#FF1493"
]

# Select color palette based on user choice
colors = rainbow_colors if color_scheme == "Rainbow" else dutch_theme_colors

# --- CHART RENDERING ---
if chart_type == "Time Series":
    st.markdown("### :material/bar_chart: Satisfaction Trends Over Time")

    # Aggregate by week or month
    if group_by == "Month":
        filtered_df["Period"] = filtered_df["Date"].dt.to_period("M").astype(
            str)
    elif group_by == "Week":
        filtered_df["Period"] = filtered_df["Date"].dt.to_period("W").astype(
            str)
    else:
        filtered_df["Period"] = filtered_df["Date"].dt.strftime("%Y-%m-%d")

    # Group data
    if group_by in ["Topic", "Source"]:
        agg_df = filtered_df.groupby(["Period",
                                      group_by])[metric].mean().reset_index()
        fig = px.line(agg_df,
                      x="Period",
                      y=metric,
                      color=group_by,
                      markers=True,
                      color_discrete_sequence=colors)
    else:
        agg_df = filtered_df.groupby("Period")[metric].mean().reset_index()
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
        st.markdown("### :material/bar_chart: Satisfaction Distribution")
        fig_hist = px.histogram(filtered_df,
                                x="Satisfaction",
                                nbins=10,
                                color_discrete_sequence=[colors[0]])
        fig_hist.update_layout(template="plotly_dark",
                               paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)",
                               font=dict(family="DM Sans"),
                               xaxis_title="Satisfaction Score",
                               yaxis_title="Frequency",
                               bargap=0.1)
        fig_hist.update_xaxes(showgrid=True,
                              gridwidth=1,
                              gridcolor='rgba(255,255,255,0.1)')
        fig_hist.update_yaxes(showgrid=True,
                              gridwidth=1,
                              gridcolor='rgba(255,255,255,0.1)')
        st.plotly_chart(fig_hist, use_container_width=True)

    # Source distribution bar chart
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
    st.markdown("### :material/bar_chart: Satisfaction by Topic")

    # Box plot
    fig_box = px.box(filtered_df,
                     x="Topic",
                     y="Satisfaction",
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

    # Grouped bar comparison by source
    st.markdown(
        "### :material/bar_chart: Average Satisfaction by Source & Verification Status"
    )
    comparison_df = filtered_df.groupby(
        ["Source", "Verified"])["Satisfaction"].mean().reset_index()
    comparison_df["Verified"] = comparison_df["Verified"].map({
        True:
        "Verified",
        False:
        "Unverified"
    })

    fig_grouped = px.bar(comparison_df,
                         x="Source",
                         y="Satisfaction",
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
    st.markdown("### :material/grid_on: Correlation Heatmap")

    # Create correlation matrix by topic
    pivot_df = filtered_df.pivot_table(values=["Satisfaction", "Quality Score"],
                                       index="Topic",
                                       aggfunc="mean")

    # Create heatmap
    topics = pivot_df.index.tolist()
    n_topics = len(topics)

    # Generate mock correlation matrix
    np.random.seed(42)
    corr_matrix = np.eye(n_topics)
    for i in range(n_topics):
        for j in range(i + 1, n_topics):
            val = np.random.uniform(0.3, 0.9)
            corr_matrix[i, j] = val
            corr_matrix[j, i] = val

    # Define colorscale based on selected color scheme
    if color_scheme == "Rainbow":
        heatmap_colorscale = [
            [0, "#4B0082"],      # Indigo
            [0.2, "#0000FF"],    # Blue
            [0.4, "#00FF00"],    # Green
            [0.6, "#FFFF00"],    # Yellow
            [0.8, "#FF7F00"],    # Orange
            [1, "#FF0000"]       # Red
        ]
    else:
        heatmap_colorscale = [[0, "#0F172A"], [0.5, "#3B82F6"], [1, "#FFCD00"]]
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=corr_matrix,
        x=topics,
        y=topics,
        colorscale=heatmap_colorscale,
        text=np.round(corr_matrix, 2),
        texttemplate="%{text}",
        textfont={"size": 10},
        hovertemplate=
        "Topic 1: %{x}<br>Topic 2: %{y}<br>Correlation: %{z:.2f}<extra></extra>"
    ))

    fig_heatmap.update_layout(template="plotly_dark",
                              paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(family="DM Sans"),
                              xaxis_tickangle=-45,
                              height=600)

    st.plotly_chart(fig_heatmap, use_container_width=True)

    # Scatter plot: Satisfaction vs Quality Score
    st.markdown("### :material/bar_chart: Satisfaction vs Quality Score")
    fig_scatter = px.scatter(filtered_df,
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

# Footer
st.markdown("---")
st.caption(
    f"Visualizing {len(filtered_df)} records • Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
