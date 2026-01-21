"""
Quality of Dutch Government - DSPG Project Group A
Main Streamlit Application with Authentication
"""

import streamlit as st
import re
import uuid
from utils.auth import (init_session_state, login_user, logout_user,
                        get_current_user, is_authenticated, get_access_level,
                        AccessLevel)
from components.feedback_modal import render_feedback_modal

# Try to import database functions for registration
try:
    from utils.database import create_user, get_user_by_email, is_database_connected, check_email_exists
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Quality of Dutch Government",
                   page_icon="🏛️",
                   layout="wide",
                   initial_sidebar_state="collapsed")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
    
    :root {
        --uu-yellow: #FFCD00;
        --uu-yellow-dark: #E6B800;
        --dutch-blue: #1E3A8A;
        --dutch-blue-light: #3B82F6;
        --bg-dark: #0F172A;
        --bg-card: #1E293B;
        --text-primary: #F1F5F9;
        --text-secondary: #94A3B8;
        --success: #10B981;
        --warning: #F59E0B;
        --error: #EF4444;
        --border: #334155;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
    }
    
    /* Login Container */
    .login-container {
        max-width: 420px;
        margin: 4rem auto;
        padding: 2.5rem;
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.98));
        border: 1px solid var(--border);
        border-radius: 20px;
        box-shadow: 
            0 25px 50px -12px rgba(0, 0, 0, 0.5),
            0 0 0 1px rgba(255, 205, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-header h1 {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0.75rem 0 0.5rem 0;
        letter-spacing: -0.025em;
    }
    
    .login-header p {
        font-family: 'DM Sans', sans-serif;
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin: 0;
    }
    
    .login-logo {
        font-size: 3.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        font-family: 'DM Sans', sans-serif !important;
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        padding: 0.75rem 1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--uu-yellow) !important;
        box-shadow: 0 0 0 2px rgba(255, 205, 0, 0.2) !important;
    }
    
    /* Button styling */
    .stButton > button {
        font-family: 'DM Sans', sans-serif !important;
        width: 100%;
        background: linear-gradient(135deg, var(--uu-yellow) 0%, var(--uu-yellow-dark) 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        color: #1E293B !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -5px rgba(255, 205, 0, 0.4) !important;
    }
    
    /* Error message styling */
    .error-message {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-top: 1rem;
        color: #FCA5A5;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.875rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Success badge */
    .access-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-family: 'Space Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-researcher {
        background: rgba(139, 92, 246, 0.2);
        border: 1px solid rgba(139, 92, 246, 0.4);
        color: #C4B5FD;
    }
    
    .badge-enduser {
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #6EE7B7;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
        border-right: 1px solid var(--border);
    }
    
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        font-family: 'DM Sans', sans-serif;
        color: var(--text-primary);
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Page header */
    .page-header {
        padding: 1rem 0 2rem 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 2rem;
    }
    
    .page-header h1 {
        font-family: 'DM Sans', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
    }
    
    .page-header p {
        font-family: 'DM Sans', sans-serif;
        color: var(--text-secondary);
        margin: 0.5rem 0 0 0;
    }
    
    /* Card component */
    .metric-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.25rem;
        backdrop-filter: blur(10px);
    }
    
    .metric-card h4 {
        font-family: 'DM Sans', sans-serif;
        color: var(--text-secondary);
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0 0 0.5rem 0;
    }
    
    .metric-card .value {
        font-family: 'Space Mono', monospace;
        color: var(--text-primary);
        font-size: 1.75rem;
        font-weight: 700;
    }
</style>
""",
            unsafe_allow_html=True)


def generate_user_id() -> str:
    """Generate a unique user ID for new registrations."""
    return f"USR_{uuid.uuid4().hex[:6].upper()}"


def validate_email(email: str) -> bool:
    """Basic email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Returns (is_valid, error_message)
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter"
    return True, ""


@st.dialog("📝 Create Account", width="small")
def render_signup_dialog():
    """Render the sign-up dialog for new end-users."""

    st.markdown("""
    <p style="color: #94A3B8; font-size: 0.9rem; margin-bottom: 1rem;">
        Create an account to track your interactions and provide feedback 
        on Dutch government performance.
    </p>
    """,
                unsafe_allow_html=True)

    # Check database availability
    if not DB_AVAILABLE or not is_database_connected():
        st.error(
            "Registration is currently unavailable. Please try again later.")
        if st.button("Close", use_container_width=True):
            st.rerun()
        return

    # Registration form
    with st.form("signup_form", clear_on_submit=False):
        email = st.text_input("Email Address",
                              placeholder="your.email@example.com",
                              key="signup_email")

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Min 6 characters, include letters and numbers",
            key="signup_password")

        confirm_password = st.text_input("Confirm Password",
                                         type="password",
                                         placeholder="Re-enter your password",
                                         key="signup_confirm")

        # Terms acknowledgment
        agree_terms = st.checkbox(
            "I understand this is a research project and my feedback will be used for academic purposes",
            key="signup_terms")

        col1, col2 = st.columns(2)
        with col1:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
        with col2:
            submit = st.form_submit_button("Create Account",
                                           use_container_width=True,
                                           type="primary")

        if cancel:
            st.rerun()

        if submit:
            # Validation
            errors = []

            if not email:
                errors.append("Email is required")
            elif not validate_email(email):
                errors.append("Please enter a valid email address")

            if not password:
                errors.append("Password is required")
            else:
                pwd_valid, pwd_error = validate_password(password)
                if not pwd_valid:
                    errors.append(pwd_error)

            if password != confirm_password:
                errors.append("Passwords do not match")

            if not agree_terms:
                errors.append("Please acknowledge the research terms")

            # Check if email already exists
            if email and validate_email(email):
                if check_email_exists(email):
                    errors.append("An account with this email already exists")

            if errors:
                for error in errors:
                    st.error(f"⚠️ {error}")
            else:
                # Create the user (End-User only, 'U' access level)
                user_id = generate_user_id()
                success, message = create_user(
                    user_id=user_id,
                    email=email,
                    access_level=
                    'U',  # End-User only - researchers are added manually
                    password=password)

                if success:
                    st.success(
                        "✅ Account created successfully! You can now log in.")
                    # Note: Don't auto-login, let them use the login form
                else:
                    st.error(f"❌ Registration failed: {message}")

    # Info note
    st.markdown("""
    <div style="
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 8px;
        padding: 0.75rem;
        margin-top: 1rem;
    ">
        <p style="color: #94A3B8; font-size: 0.8rem; margin: 0;">
            🔬 <strong>Researcher access?</strong> Contact your administrator to be added manually.
        </p>
    </div>
    """,
                unsafe_allow_html=True)


def render_login_page():
    """Render the login page with authentication form."""

    # Logo at top right
    logo_col1, logo_col2 = st.columns([4, 1])
    with logo_col2:
        st.image("uu_white_text_banner.png")

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div class="login-container">
            <div class="login-header">
                <div class="login-logo">🏛️</div>
                <h1>Quality of Dutch Government</h1>
                <p>Institute for Government Quality Research</p>
            </div>
        </div>
        """,
                    unsafe_allow_html=True)

        # Login form
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email",
                                  placeholder="Enter your email address",
                                  key="login_email")

            password = st.text_input("Password",
                                     type="password",
                                     placeholder="Enter your password",
                                     key="login_password")

            submit_button = st.form_submit_button("Sign In",
                                                  use_container_width=True)

            if submit_button:
                if email and password:
                    success, message = login_user(email, password)
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.markdown(f"""
                        <div class="error-message">
                            ⚠️ {message}
                        </div>
                        """,
                                    unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="error-message">
                        ⚠️ Please enter both email and password
                    </div>
                    """,
                                unsafe_allow_html=True)

        # Sign Up button (material blue style)
        st.markdown("""
        <style>
            /* Style the Sign Up button with Material Blue */
            button[kind="secondary"][data-testid="baseButton-secondary"] {
                background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%) !important;
                color: white !important;
                border: none !important;
            }
            button[kind="secondary"][data-testid="baseButton-secondary"]:hover {
                background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%) !important;
                box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4) !important;
            }
        </style>
        """,
                    unsafe_allow_html=True)

        if st.button("Sign Up", use_container_width=True, key="signup_btn"):
            render_signup_dialog()

        # Demo credentials hint
        st.markdown("---")
        with st.expander("🔑 Demo Credentials"):
            st.markdown("""
            **End-User Account:**
            - Email: `user@demo.nl`
            - Password: `demo123`
            
            **Researcher Account:**
            - Email: `researcher@demo.nl`
            - Password: `demo123`
            """)


def render_sidebar():
    """Render the sidebar based on user access level."""
    user = get_current_user()
    access_level = get_access_level()

    with st.sidebar:
        # User info
        st.markdown(f"""
        <div style="padding: 1rem 0; border-bottom: 1px solid #334155; margin-bottom: 1rem;">
            <p style="color: #94A3B8; font-size: 0.8rem; margin: 0;">Logged in as</p>
            <p style="color: #F1F5F9; font-weight: 600; margin: 0.25rem 0;">{user['email']}</p>
            <span class="access-badge {'badge-researcher' if access_level == AccessLevel.RESEARCHER else 'badge-enduser'}">
                {'🔬 Researcher' if access_level == AccessLevel.RESEARCHER else '👤 End User'}
            </span>
        </div>
        """,
                    unsafe_allow_html=True)

        # Logout button
        if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
            logout_user()
            st.rerun()

        st.markdown("---")

        # Feedback button (available to all users)
        if st.button("💬 Send Feedback",
                     use_container_width=True,
                     key="feedback_btn"):
            st.session_state.show_feedback_modal = True


def main():
    """Main application entry point."""

    # Initialize session state
    init_session_state()

    # Check authentication
    if not is_authenticated():
        render_login_page()
        st.stop()

    # User is authenticated - render sidebar
    render_sidebar()

    # Render feedback modal if triggered
    if st.session_state.get('show_feedback_modal', False):
        render_feedback_modal()

    # Get access level and render appropriate view
    access_level = get_access_level()

    if access_level == AccessLevel.RESEARCHER:
        # Researcher multi-page navigation
        data_table = st.Page("views/researcher/data_table.py",
                             title="Data Table",
                             icon="📊",
                             default=True)
        visualizations = st.Page("views/researcher/visualizations.py",
                                 title="Visualizations",
                                 icon="📈")
        export = st.Page("views/researcher/export.py",
                         title="Export",
                         icon="💾")

        nav = st.navigation(
            {
                "📊 Analysis": [data_table, visualizations],
                "📁 Data": [export]
            },
            expanded=True)
        nav.run()

    else:
        # End-User view - single page chat interface
        from views.end_user import render_end_user_view
        render_end_user_view()


if __name__ == "__main__":
    main()
