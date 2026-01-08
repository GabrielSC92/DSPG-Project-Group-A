"""
LLM utilities for the Quality of Dutch Government application.
Handles Gemini API configuration and chat functionality.
"""

import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from typing import Optional, Tuple

# Load environment variables ONCE at module load
load_dotenv()

# System prompt for the QoG assistant
SYSTEM_PROMPT = """You are an AI assistant for the Quality of Dutch Government research platform. 
Your role is to help users understand and analyze qualitative reports on Dutch government performance,
translating them into quantitative indicators.

You have knowledge about:
- Dutch Court of Audit (Algemene Rekenkamer) reports
- Auditdienst Rijk (internal government auditor) reports  
- IOB (Directie Internationaal Onderzoek en Beleidsevaluatie) policy evaluations
- Government quality and performance indicators

When responding:
1. Be helpful, accurate, and professional
2. When discussing metrics, present them clearly (e.g., scores out of 10, percentages)
3. Cite sources when discussing specific reports or findings
4. If you don't have specific information, acknowledge this clearly
5. Focus on Dutch government quality, policy effectiveness, and public administration

Note: This is a research tool. All conversations are ephemeral and not stored in the database yet.
The satisfaction rating the user provides helps improve our system."""

# Get API key once at module load
_API_KEY = os.getenv("GEMINI_API_KEY")
_CONFIGURED = False


def _ensure_configured() -> bool:
    """
    Ensure Gemini is configured exactly once.
    Returns True if configured successfully, False otherwise.
    """
    global _CONFIGURED
    
    if _CONFIGURED:
        return True
    
    if not _API_KEY or _API_KEY == "your_api_key_here":
        return False
    
    try:
        genai.configure(api_key=_API_KEY)
        _CONFIGURED = True
        return True
    except Exception:
        return False


def is_api_configured() -> bool:
    """Check if the Gemini API key is present in environment."""
    return bool(_API_KEY and _API_KEY != "your_api_key_here")


def init_gemini() -> Tuple[bool, Optional[str]]:
    """
    Initialize and configure the Gemini API (only configures once).
    
    Returns:
        Tuple of (success: bool, error_message: str or None)
    """
    if not _API_KEY or _API_KEY == "your_api_key_here":
        return False, "API key not configured"
    
    if _ensure_configured():
        return True, None
    else:
        return False, "Failed to configure Gemini API"


def get_gemini_model():
    """Get or create the Gemini model instance (cached in session state)."""
    # Ensure API is configured first
    if not _ensure_configured():
        return None
        
    if 'gemini_model' not in st.session_state:
        try:
            # Use same model as app.py
            st.session_state.gemini_model = genai.GenerativeModel(
                'gemini-2.5-flash',
                system_instruction=SYSTEM_PROMPT
            )
        except Exception as e:
            st.error(f"Failed to initialize Gemini model: {e}")
            return None
    return st.session_state.gemini_model


def get_chat_session():
    """Get or create the chat session for conversation continuity."""
    model = get_gemini_model()
    if model is None:
        return None
        
    if 'gemini_chat' not in st.session_state:
        st.session_state.gemini_chat = model.start_chat(history=[])
    return st.session_state.gemini_chat


def send_message(prompt: str) -> Tuple[bool, str]:
    """
    Send a message to the Gemini chat and get a response.
    
    Args:
        prompt: The user's message
        
    Returns:
        Tuple of (success: bool, response_text: str or error_message)
    """
    chat = get_chat_session()
    if chat is None:
        return False, "Chat session not initialized. Please check your API configuration."
    
    try:
        response = chat.send_message(prompt)
        return True, response.text
    except Exception as e:
        return False, f"Error getting response: {str(e)}"


def clear_chat_session():
    """Clear the current chat session to start fresh."""
    if 'gemini_chat' in st.session_state:
        del st.session_state.gemini_chat
    
    # Re-create chat with existing model if available
    model = get_gemini_model()
    if model:
        st.session_state.gemini_chat = model.start_chat(history=[])
