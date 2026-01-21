# components/single_metric_card.py
"""
Metric Card Components for the Quality of Government Dashboard.
Provides styled metric cards for displaying summary statistics in researcher views.
"""

import streamlit as st
import streamlit.components.v1 as components


def render_metric_card(label: str,
                       value: str,
                       icon: str = None,
                       color: str = "#3b82f6",
                       help_text: str = None,
                       delta: str = None,
                       delta_color: str = None,
                       delay: float = 0,
                       height: int = 120):
    """
    Render a simple, clean metric card for summary statistics.
    
    Args:
        label: The metric label/title (e.g., "Total Records")
        value: The metric value to display (e.g., "6", "3.7/5", "100.0%")
        icon: Optional icon character or emoji (e.g., "📊", "⭐", "🔗")
        color: Accent color for the card (hex code)
        help_text: Optional tooltip text for additional context
        delta: Optional change indicator (e.g., "+12%", "-5")
        delta_color: Color for delta ("green", "red", or hex code)
        delay: Animation delay in seconds
        height: Height of the card in pixels
    
    Returns:
        Streamlit HTML component
    """

    # Determine delta styling
    delta_html = ""
    if delta:
        delta_bg = "#dcfce7" if delta_color == "green" else "#fee2e2" if delta_color == "red" else "#f3f4f6"
        delta_text = "#16a34a" if delta_color == "green" else "#dc2626" if delta_color == "red" else "#6b7280"
        delta_html = f'''
            <span class="delta-badge" style="background-color: {delta_bg}; color: {delta_text};">
                {delta}
            </span>
        '''

    # Icon HTML
    icon_html = f'<span class="metric-icon">{icon}</span>' if icon else ''

    # Help text tooltip
    tooltip_attr = f'title="{help_text}"' if help_text else ''
    cursor_style = 'cursor: help;' if help_text else ''

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: transparent;
            }}
            
            @keyframes fadeInUp {{
                from {{
                    opacity: 0;
                    transform: translateY(15px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            @keyframes countUp {{
                from {{ opacity: 0.3; }}
                to {{ opacity: 1; }}
            }}
            
            .metric-card {{
                background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%);
                border-radius: 12px;
                padding: 16px 20px;
                border: 1px solid #e5e7eb;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: center;
                position: relative;
                overflow: hidden;
                opacity: 0;
                animation: fadeInUp 0.5s ease-out forwards;
                animation-delay: {delay}s;
                transition: all 0.2s ease;
                {cursor_style}
            }}
            
            .metric-card:hover {{
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
                transform: translateY(-2px);
                border-color: {color}40;
            }}
            
            .metric-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background: {color};
                border-radius: 12px 0 0 12px;
            }}
            
            .metric-header {{
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
            }}
            
            .metric-icon {{
                font-size: 16px;
                opacity: 0.8;
            }}
            
            .metric-label {{
                font-size: 12px;
                font-weight: 500;
                color: #6b7280;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .metric-value-container {{
                display: flex;
                align-items: baseline;
                gap: 10px;
                flex-wrap: wrap;
            }}
            
            .metric-value {{
                font-size: 28px;
                font-weight: 700;
                color: #111827;
                line-height: 1.2;
                animation: countUp 0.8s ease-out forwards;
                animation-delay: {delay + 0.2}s;
            }}
            
            .delta-badge {{
                font-size: 11px;
                font-weight: 600;
                padding: 2px 8px;
                border-radius: 12px;
                white-space: nowrap;
            }}
            
            /* Dark mode support */
            @media (prefers-color-scheme: dark) {{
                .metric-card {{
                    background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
                    border-color: #374151;
                }}
                
                .metric-card:hover {{
                    border-color: {color}60;
                }}
                
                .metric-label {{
                    color: #9ca3af;
                }}
                
                .metric-value {{
                    color: #f9fafb;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="metric-card" {tooltip_attr}>
            <div class="metric-header">
                {icon_html}
                <span class="metric-label">{label}</span>
            </div>
            <div class="metric-value-container">
                <span class="metric-value">{value}</span>
                {delta_html}
            </div>
        </div>
    </body>
    </html>
    """

    return components.html(html, height=height)


def render_metric_row(metrics: list, height: int = 120):
    """
    Render a row of metric cards using Streamlit columns.
    
    Args:
        metrics: List of metric dictionaries with keys:
                 - label (required)
                 - value (required)
                 - icon (optional)
                 - color (optional)
                 - help_text (optional)
                 - delta (optional)
                 - delta_color (optional)
        height: Height of each card in pixels
    
    Example:
        metrics = [
            {"label": "Total Records", "value": "6", "icon": "📊", "color": "#3b82f6"},
            {"label": "Avg. Satisfaction", "value": "3.7/5", "icon": "⭐", "color": "#f59e0b"},
            {"label": "Avg. Correlation", "value": "0.725", "icon": "🔗", "color": "#8b5cf6"},
            {"label": "Verified %", "value": "100.0%", "icon": "✓", "color": "#10b981"},
            {"label": "Unique Users", "value": "1", "icon": "👤", "color": "#6366f1"},
        ]
        render_metric_row(metrics)
    """
    cols = st.columns(len(metrics))

    for i, (col, metric) in enumerate(zip(cols, metrics)):
        with col:
            render_metric_card(
                label=metric.get("label", ""),
                value=metric.get("value", ""),
                icon=metric.get("icon"),
                color=metric.get("color", "#3b82f6"),
                help_text=metric.get("help_text"),
                delta=metric.get("delta"),
                delta_color=metric.get("delta_color"),
                delay=i * 0.1,  # Stagger animations
                height=height)


def render_detailed_metric_card(title: str,
                                subtitle: str,
                                primary_label: str,
                                primary_value: str,
                                progress_label: str = None,
                                progress_value: float = None,
                                width: int = None,
                                height: int = None,
                                color: str = "#3b82f6",
                                delay: float = 0,
                                help_text: str = None,
                                show_progress_bar: bool = True,
                                primary_value_hover: str = None):
    """
    Render a detailed metric card with optional progress bar.
    This is the original complex card design for detailed views.
    
    Args:
        title: Card title
        subtitle: Card subtitle
        primary_label: Label for the primary value
        primary_value: Main value to display
        progress_label: Label for progress bar
        progress_value: Progress percentage (0-100)
        width: Card width in pixels
        height: Card height in pixels
        color: Accent color
        delay: Animation delay
        help_text: Tooltip text
        show_progress_bar: Whether to show progress bar
        primary_value_hover: Full value to show on hover
    """
    import re

    # Format progress value
    progress_value_float = 0
    if show_progress_bar and progress_value is not None:
        try:
            clean_value = re.sub(r'[^0-9,.]+', '', str(progress_value))
            clean_value = clean_value.replace(',', '.')
            progress_value_float = float(clean_value)
            progress_value_float = min(max(progress_value_float, 0), 100)
        except (ValueError, TypeError):
            progress_value_float = 0

    # Tooltip HTML
    tooltip_html = ""
    tooltip_container_class = ""
    if help_text:
        tooltip_html = f'<div class="tooltip-text">{help_text}</div>'
        tooltip_container_class = "tooltip-container"

    # Progress bar HTML
    progress_bar_html = ""
    if show_progress_bar and progress_label and progress_value is not None:
        progress_bar_html = f"""
        <div>
            <div class="flex justify-between items-center mb-1">
                <span class="text-sm font-medium progress-text progress-label-ellipsis">{progress_label}</span>
                <span class="text-sm font-medium progress-text">{progress_value}</span>
            </div>
            <div class="progress-bar-container w-full">
                <div class="progress-bar"></div>
            </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                margin: 0;
                padding: 0;
            }}
            
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            .progress-bar-container {{
                background-color: #e5e7eb;
                border-radius: 0.7rem;
                overflow: hidden;
                height: 12px;
            }}
            
            .progress-bar {{
                background-color: {color};
                height: 100%;
                border-radius: 0.7rem;
                width: 0;
                animation: progressGrow 1.2s ease-out forwards;
                animation-delay: {delay + 0.3}s;
            }}
            
            @keyframes progressGrow {{
                from {{ width: 0; }}
                to {{ width: {progress_value_float}%; }}
            }}
            
            .progress-text {{ color: {color}; }}
            
            .metric-card {{
                border-radius: 1rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                border: 1px solid #e5e7eb;
                background-color: white;
                padding: 1.5rem;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                height: 100%;
                opacity: 0;
                animation: fadeIn 0.6s ease-out forwards;
                animation-delay: {delay}s;
            }}
            
            .title-ellipsis, .subtitle-ellipsis, .progress-label-ellipsis, .primary-value-ellipsis {{
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                position: relative;
            }}
            
            .progress-label-ellipsis {{
                flex: 1;
                margin-right: 8px;
            }}
            
            .tooltip-container {{
                position: relative;
                display: inline-block;
                cursor: help;
            }}
            
            .tooltip-container .tooltip-text {{
                visibility: hidden;
                width: 240px;
                background-color: #333;
                color: #fff;
                text-align: center;
                border-radius: 6px;
                padding: 8px;
                position: absolute;
                z-index: 1;
                bottom: 115%;
                opacity: 0;
                transition: opacity 0.3s;
                font-size: 12px;
            }}
            
            .tooltip-container:hover .tooltip-text {{
                visibility: visible;
                opacity: 1;
            }}
        </style>
    </head>
    <body>
        <div class="metric-card">
            <div>
                <h2 class="text-lg font-semibold text-gray-700 mb-1 title-ellipsis">{title}</h2>
                <p class="text-sm text-gray-500 mb-4 subtitle-ellipsis">{subtitle}</p>
                <div class="mb-4 {tooltip_container_class}">
                    <span class="text-xs text-gray-600 block">{primary_label}</span>
                    <span class="text-3xl font-bold text-gray-800 primary-value-ellipsis">{primary_value}</span>
                    {tooltip_html}
                </div>
            </div>
            {progress_bar_html}
        </div>
    </body>
    </html>
    """

    return components.html(html, width=width, height=height)
