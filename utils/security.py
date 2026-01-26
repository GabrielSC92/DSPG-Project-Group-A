"""
Security utilities and configurations for the Quality of Dutch Government application.
Implements various security best practices and OWASP recommendations.
"""

import streamlit as st
from typing import Dict, Any
import re
import html


def add_security_headers():
    """
    Add security headers to the Streamlit application.
    These headers help protect against various web vulnerabilities:
    - XSS (Cross-Site Scripting)
    - Clickjacking
    - MIME-type sniffing
    - Information disclosure
    """
    # Note: Streamlit doesn't provide direct control over HTTP headers
    # In production, these should be set at the web server level (nginx, Apache)
    # or through a reverse proxy
    
    security_headers = {
        # Prevent clickjacking attacks
        'X-Frame-Options': 'DENY',
        
        # Prevent MIME-type sniffing
        'X-Content-Type-Options': 'nosniff',
        
        # Enable XSS protection in browsers
        'X-XSS-Protection': '1; mode=block',
        
        # Control referrer information
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        
        # Content Security Policy (CSP)
        # Note: This is a basic policy and should be adjusted based on actual needs
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:;"
        ),
        
        # Permissions Policy (formerly Feature-Policy)
        'Permissions-Policy': (
            'geolocation=(), microphone=(), camera=(), payment=()'
        ),
    }
    
    # Add a note in the UI about security headers
    # (actual headers need to be set at deployment level)
    return security_headers


def sanitize_input(user_input: str, allow_html: bool = False) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.
    
    Args:
        user_input: Raw user input string
        allow_html: If True, allows safe HTML tags. Default False.
        
    Returns:
        Sanitized string safe for display/storage
    """
    if not isinstance(user_input, str):
        return str(user_input)
    
    # Remove null bytes
    sanitized = user_input.replace('\x00', '')
    
    if not allow_html:
        # Escape HTML special characters
        sanitized = html.escape(sanitized)
    else:
        # If HTML is allowed, only allow safe tags (whitelist approach)
        # This is a basic implementation - consider using bleach library for production
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
        # For now, escape everything for safety
        sanitized = html.escape(sanitized)
    
    return sanitized


def validate_email_format(email: str) -> bool:
    """
    Validate email format using regex.
    This is more comprehensive than the simple validation in streamlit_app.py
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    # RFC 5322 compliant email regex (simplified)
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}$'
    
    if not email or len(email) > 254:  # RFC 5321
        return False
    
    if not re.match(pattern, email):
        return False
    
    # Additional checks
    local, domain = email.rsplit('@', 1)
    
    # Local part shouldn't exceed 64 characters
    if len(local) > 64:
        return False
    
    # Domain part shouldn't exceed 255 characters
    if len(domain) > 255:
        return False
    
    return True


def log_security_event(event_type: str, details: Dict[str, Any]) -> None:
    """
    Log security-related events for monitoring and audit purposes.
    In production, this should integrate with a proper logging system.
    
    Args:
        event_type: Type of security event (e.g., 'failed_login', 'account_lockout')
        details: Dictionary with event details (user_id, ip, timestamp, etc.)
    """
    import datetime
    
    # For now, log to session state
    # In production, this should write to a secure log file or monitoring service
    if 'security_logs' not in st.session_state:
        st.session_state.security_logs = []
    
    log_entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'event_type': event_type,
        'details': details
    }
    
    st.session_state.security_logs.append(log_entry)
    
    # Keep only last 100 entries to avoid memory issues
    if len(st.session_state.security_logs) > 100:
        st.session_state.security_logs = st.session_state.security_logs[-100:]


def check_password_strength(password: str) -> Dict[str, Any]:
    """
    Comprehensive password strength checker.
    Returns detailed information about password strength.
    
    Args:
        password: Password to check
        
    Returns:
        Dictionary with strength score and feedback
    """
    score = 0
    feedback = []
    
    # Length check
    length = len(password)
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if length >= 16:
        score += 1
    else:
        feedback.append("Use 12+ characters for better security")
    
    # Character variety
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    variety_count = sum([has_lower, has_upper, has_digit, has_special])
    score += variety_count
    
    if not has_upper:
        feedback.append("Add uppercase letters")
    if not has_digit:
        feedback.append("Add numbers")
    if not has_special:
        feedback.append("Add special characters (!@#$%^&*)")
    
    # Check for common patterns
    common_passwords = ['password', '123456', 'qwerty', 'admin', 'welcome']
    if password.lower() in common_passwords:
        score = 0
        feedback = ["This is a commonly used password. Please choose a unique password."]
    
    # Determine strength level
    if score >= 6:
        strength = "Strong"
    elif score >= 4:
        strength = "Medium"
    else:
        strength = "Weak"
    
    return {
        'score': score,
        'strength': strength,
        'feedback': feedback,
        'is_acceptable': score >= 4
    }


def prevent_sql_injection(query_param: str) -> str:
    """
    Helper to prevent SQL injection by validating/sanitizing parameters.
    Note: This should NOT be used as replacement for parameterized queries!
    Always use SQLAlchemy's parameterized queries.
    
    This is just an additional safety check for string parameters.
    
    Args:
        query_param: Query parameter to validate
        
    Returns:
        Sanitized parameter
    """
    # Remove dangerous SQL keywords and characters
    dangerous_patterns = [
        r';\s*DROP',
        r';\s*DELETE',
        r';\s*UPDATE',
        r';\s*INSERT',
        r'--',
        r'/\*',
        r'\*/',
        r'xp_',
        r'sp_',
        r'EXEC\s*\(',
        r'EXECUTE\s*\(',
    ]
    
    sanitized = query_param
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    return sanitized


def get_deployment_recommendations() -> Dict[str, str]:
    """
    Return security recommendations for production deployment.
    These should be implemented at the infrastructure/deployment level.
    
    Returns:
        Dictionary of security recommendations
    """
    return {
        "HTTPS": "Always use HTTPS in production. Enable TLS 1.3 or TLS 1.2 minimum.",
        "Reverse Proxy": "Deploy behind nginx/Apache with security headers configured.",
        "Database": "Use strong database credentials. Never use default passwords.",
        "Environment Variables": "Store secrets in environment variables, never in code.",
        "Session Management": "Configure secure session cookies (HttpOnly, Secure, SameSite).",
        "Rate Limiting": "Implement rate limiting at reverse proxy or application level.",
        "Monitoring": "Set up security monitoring and alerting for suspicious activities.",
        "Backups": "Regular encrypted backups of database with tested restore procedures.",
        "Updates": "Keep all dependencies updated. Monitor for security advisories.",
        "Access Control": "Principle of least privilege for database and system access.",
        "Firewall": "Configure firewall to allow only necessary ports.",
        "DDoS Protection": "Use CDN/WAF like Cloudflare for DDoS protection.",
        "Log Management": "Centralized logging with log rotation and secure storage.",
        "Secrets Management": "Use secrets management tools (HashiCorp Vault, AWS Secrets Manager).",
    }
