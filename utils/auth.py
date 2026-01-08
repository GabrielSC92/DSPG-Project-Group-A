"""
Authentication utilities for the Quality of Dutch Government application.
Handles user authentication, session management, and access level control.
"""

import streamlit as st
from enum import Enum
from typing import Tuple, Optional, Dict, Any
import hashlib
from datetime import datetime

# Try to import database functions
try:
    from utils.database import (
        authenticate_user_db, 
        get_user_by_email, 
        is_database_connected,
        update_user_interaction_count as db_update_interaction_count,
        update_user_satisfaction_baseline as db_update_satisfaction_baseline
    )
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


class AccessLevel(Enum):
    """User access levels as defined in the system architecture."""
    END_USER = "end_user"
    RESEARCHER = "researcher"


# Fallback demo users (used if database is not available)
DEMO_PASSWORD_HASH = hashlib.sha256("demo123".encode()).hexdigest()

DEMO_USERS = {
    "user@demo.nl": {
        "user_id": "USR_001",
        "email": "user@demo.nl",
        "password_hash": DEMO_PASSWORD_HASH,
        "access_level": "U",
        "created_date": "2024-01-01",
        "satisfaction_baseline": 5.0,
        "interaction_count": 0
    },
    "researcher@demo.nl": {
        "user_id": "USR_002",
        "email": "researcher@demo.nl",
        "password_hash": DEMO_PASSWORD_HASH,
        "access_level": "R",
        "created_date": "2024-01-01",
        "satisfaction_baseline": None,
        "interaction_count": 0
    },
    "admin@qog.nl": {
        "user_id": "USR_003",
        "email": "admin@qog.nl",
        "password_hash": DEMO_PASSWORD_HASH,
        "access_level": "R",
        "created_date": "2024-01-01",
        "satisfaction_baseline": None,
        "interaction_count": 0
    }
}


def init_session_state() -> None:
    """Initialize all required session state variables."""
    defaults = {
        'authenticated': False,
        'user': None,
        'access_level': None,
        'login_attempts': 0,
        'show_feedback_modal': False,
        'chat_history': [],
        'current_satisfaction': None,
        'debug_mode': False,
        'using_database': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == password_hash


def _convert_access_level(access_level_str: str) -> AccessLevel:
    """Convert database access level string to AccessLevel enum."""
    if access_level_str == 'R':
        return AccessLevel.RESEARCHER
    return AccessLevel.END_USER


def authenticate_user(email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Authenticate a user with email and password.
    Tries database first, falls back to demo users.
    
    Args:
        email: User's email address
        password: User's password
        
    Returns:
        Tuple of (success: bool, user_data: dict or None)
    """
    email = email.lower().strip()
    
    # Try database authentication first
    if DB_AVAILABLE and is_database_connected():
        success, user_data = authenticate_user_db(email, password)
        if success and user_data:
            # Convert access_level string to enum
            user_data['access_level'] = _convert_access_level(user_data.get('access_level', 'U'))
            st.session_state.using_database = True
            return True, user_data
    
    # Fallback to demo users
    if email in DEMO_USERS:
        user = DEMO_USERS[email]
        if verify_password(password, user['password_hash']):
            user_data = {k: v for k, v in user.items() if k != 'password_hash'}
            user_data['access_level'] = _convert_access_level(user_data.get('access_level', 'U'))
            st.session_state.using_database = False
            return True, user_data
    
    return False, None


def login_user(email: str, password: str) -> Tuple[bool, str]:
    """
    Attempt to log in a user.
    
    Args:
        email: User's email address
        password: User's password
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Track login attempts
    st.session_state.login_attempts += 1
    
    # Check for too many attempts
    if st.session_state.login_attempts > 5:
        return False, "Too many login attempts. Please try again later."
    
    # Authenticate
    success, user_data = authenticate_user(email, password)
    
    if success and user_data:
        st.session_state.authenticated = True
        st.session_state.user = user_data
        st.session_state.access_level = user_data['access_level']
        st.session_state.login_attempts = 0
        
        # Log successful login
        access_str = "Researcher" if user_data['access_level'] == AccessLevel.RESEARCHER else "End User"
        db_status = "(DB)" if st.session_state.using_database else "(Demo)"
        return True, f"Welcome! Access level: {access_str} {db_status}"
    
    return False, "Invalid email or password. Please try again."


def logout_user() -> None:
    """Log out the current user and clear session state."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.access_level = None
    st.session_state.chat_history = []
    st.session_state.current_satisfaction = None
    st.session_state.show_feedback_modal = False
    st.session_state.using_database = False


def is_authenticated() -> bool:
    """Check if a user is currently authenticated."""
    return st.session_state.get('authenticated', False)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the currently logged-in user's data."""
    return st.session_state.get('user', None)


def get_access_level() -> Optional[AccessLevel]:
    """Get the current user's access level."""
    return st.session_state.get('access_level', None)


def is_researcher() -> bool:
    """Check if the current user has researcher access."""
    return get_access_level() == AccessLevel.RESEARCHER


def is_end_user() -> bool:
    """Check if the current user has end-user access."""
    return get_access_level() == AccessLevel.END_USER


def get_user_id() -> Optional[str]:
    """Get the current user's ID."""
    user = get_current_user()
    return user.get('user_id') if user else None


def update_interaction_count() -> None:
    """Increment the user's interaction count (in session and optionally DB)."""
    user = get_current_user()
    if user and 'interaction_count' in user:
        user['interaction_count'] = (user['interaction_count'] or 0) + 1
        st.session_state.user = user
        
        # Also update in database if connected
        if st.session_state.get('using_database') and DB_AVAILABLE:
            db_update_interaction_count(user['user_id'])


def get_satisfaction_baseline() -> Optional[float]:
    """Get the user's satisfaction baseline."""
    user = get_current_user()
    return user.get('satisfaction_baseline') if user else None


def update_satisfaction_baseline(new_baseline: float) -> None:
    """Update the user's satisfaction baseline (in session and optionally DB)."""
    user = get_current_user()
    if user:
        user['satisfaction_baseline'] = new_baseline
        st.session_state.user = user
        
        # Also update in database if connected
        if st.session_state.get('using_database') and DB_AVAILABLE:
            db_update_satisfaction_baseline(user['user_id'], new_baseline)


def is_using_database() -> bool:
    """Check if current session is using database authentication."""
    return st.session_state.get('using_database', False)