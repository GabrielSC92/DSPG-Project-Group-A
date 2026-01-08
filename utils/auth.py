"""
Authentication utilities for the Quality of Dutch Government application.
Handles user authentication, session management, and access level control.
"""

import streamlit as st
from enum import Enum
from typing import Tuple, Optional, Dict, Any
import hashlib
from datetime import datetime

class AccessLevel(Enum):
    """User access levels as defined in the system architecture."""
    END_USER = "end_user"
    RESEARCHER = "researcher"


# Demo users database (in production, this would be replaced with actual DB calls)
# Password hash for 'demo123' using SHA256
DEMO_PASSWORD_HASH = hashlib.sha256("demo123".encode()).hexdigest()

DEMO_USERS = {
    "user@demo.nl": {
        "user_id": "usr_001",
        "email": "user@demo.nl",
        "password_hash": DEMO_PASSWORD_HASH,
        "access_level": AccessLevel.END_USER,
        "created_date": "2024-01-01",
        "satisfaction_baseline": 5.0,
        "interaction_count": 0
    },
    "researcher@demo.nl": {
        "user_id": "usr_002",
        "email": "researcher@demo.nl",
        "password_hash": DEMO_PASSWORD_HASH,
        "access_level": AccessLevel.RESEARCHER,
        "created_date": "2024-01-01",
        "satisfaction_baseline": None,
        "interaction_count": 0
    },
    "admin@qog.nl": {
        "user_id": "usr_003",
        "email": "admin@qog.nl",
        "password_hash": DEMO_PASSWORD_HASH,
        "access_level": AccessLevel.RESEARCHER,
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
        'debug_mode': False
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


def authenticate_user(email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Authenticate a user with email and password.
    
    Args:
        email: User's email address
        password: User's password
        
    Returns:
        Tuple of (success: bool, user_data: dict or None)
    """
    email = email.lower().strip()
    
    # Check if user exists in demo database
    if email not in DEMO_USERS:
        return False, None
    
    user = DEMO_USERS[email]
    
    # Verify password
    if not verify_password(password, user['password_hash']):
        return False, None
    
    # Return user data (excluding password hash)
    user_data = {k: v for k, v in user.items() if k != 'password_hash'}
    return True, user_data


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
        return True, f"Welcome back! Access level: {access_str}"
    
    return False, "Invalid email or password. Please try again."


def logout_user() -> None:
    """Log out the current user and clear session state."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.access_level = None
    st.session_state.chat_history = []
    st.session_state.current_satisfaction = None
    st.session_state.show_feedback_modal = False


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
    """Increment the user's interaction count."""
    user = get_current_user()
    if user and 'interaction_count' in user:
        user['interaction_count'] += 1
        st.session_state.user = user


def get_satisfaction_baseline() -> Optional[float]:
    """Get the user's satisfaction baseline."""
    user = get_current_user()
    return user.get('satisfaction_baseline') if user else None


def update_satisfaction_baseline(new_baseline: float) -> None:
    """Update the user's satisfaction baseline."""
    user = get_current_user()
    if user:
        user['satisfaction_baseline'] = new_baseline
        st.session_state.user = user

