"""
End-Users View for the Quality of Dutch Government application.
Provides a chat interface for users to interact with the LLM system
and rate their satisfaction with responses.
"""

import streamlit as st
from utils.auth import get_current_user, update_interaction_count, get_user_id, is_using_database
from utils.llm import (init_gemini, send_message, clear_chat_session,
                       is_api_configured, is_llm_configured,
                       is_agent_configured, run_synthesis_and_store,
                       get_backend_info)

# Try to import database functions
try:
    from utils.database import save_interaction, is_database_connected
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


def render_api_status() -> bool:
    """
    Render the API connection status and return whether it's configured.
    Shows status for both Agent and LLM APIs.
    
    Returns:
        bool: True if both APIs are configured and ready, False otherwise
    """
    agent_ok = is_agent_configured()
    llm_ok = is_llm_configured()

    # Both APIs configured
    if agent_ok and llm_ok:
        success, _ = init_gemini()
        if success:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1rem; display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                <span style="
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 0.75rem;
                    font-family: 'Space Mono', monospace;
                    background: rgba(139, 92, 246, 0.15);
                    border: 1px solid rgba(139, 92, 246, 0.3);
                    color: #a78bfa;
                ">
                    <span style="
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background: #a78bfa;
                        box-shadow: 0 0 8px #a78bfa;
                        animation: pulse 2s infinite;
                    "></span>
                    Agent Ready
                </span>
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
                    LLM Ready
                </span>
            </div>
            <style>
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            </style>
            """,
                        unsafe_allow_html=True)
            return True

    # Show partial status
    status_items = [('Agent', agent_ok), ('LLM', llm_ok)]

    badges = []
    for name, configured in status_items:
        if configured:
            badge = f'<span style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-family: \'Space Mono\', monospace; background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.3); color: #4ade80;"><span style="width: 8px; height: 8px; border-radius: 50%; background: #4ade80;"></span>{name} ✓</span>'
        else:
            badge = f'<span style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-family: \'Space Mono\', monospace; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171;"><span style="width: 8px; height: 8px; border-radius: 50%; background: #f87171;"></span>{name} ✗</span>'
        badges.append(badge)

    badges_html = " ".join(badges)
    st.markdown(
        f'<div style="text-align: center; margin-bottom: 1rem; display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">{badges_html}</div>',
        unsafe_allow_html=True)

    backend_info = get_backend_info()
    if "Ollama" in backend_info['backend']:
        st.warning("⚠️ Ollama is not running")
        st.code("""# Start Ollama server:
ollama serve

# In another terminal, pull a model:
ollama pull llama3.2""",
                language="bash")
        st.info("Make sure Ollama is installed: https://ollama.ai/download")
    else:
        st.warning("⚠️ Please add your Gemini API keys to the `.env` file")
        st.code("""GEMINI_API_KEY_LLM=your_llm_api_key_here
GEMINI_API_KEY_AGENT=your_agent_api_key_here

# Or use Ollama (local, no rate limits):
LLM_BACKEND=ollama
OLLAMA_MODEL=llama3.2""",
                language="bash")
        st.info(
            "Get Gemini API keys at: https://makersuite.google.com/app/apikey")
    return False


def render_satisfaction_prompt(message_index: int) -> None:
    """Render the satisfaction rating prompt using a 5-point Likert scale."""
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, rgba(255, 107, 53, 0.1), rgba(30, 58, 138, 0.1));
            border: 1px solid rgba(255, 107, 53, 0.3);
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin: 1rem 0;
        ">
            <p style="color: #F1F5F9; font-size: 0.95rem; font-weight: 500; margin: 0 0 0.5rem 0;">
                🏛️ Rate Government Performance
            </p>
            <p style="color: #94A3B8; font-size: 0.85rem; margin: 0;">
                Based on the information above, how satisfied are you with the Dutch government's performance on this topic?
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_mid, col_right = st.columns([1, 8, 1])

    with col_left:
        st.caption("😞")

    with col_mid:
        LIKERT_OPTIONS = [
            "Very dissatisfied",
            "Dissatisfied",
            "Neutral",
            "Satisfied",
            "Very satisfied",
        ]

        likert_value = st.radio(
            "How satisfied are you with the Dutch government's performance on this topic?",
            LIKERT_OPTIONS,
            index=2,  # Neutral default
            key=f"satisfaction_{message_index}",
            horizontal=True,
            label_visibility="collapsed",
        )

        LIKERT_TO_SCORE = {
            "Very dissatisfied": 1,
            "Dissatisfied": 2,
            "Neutral": 3,
            "Satisfied": 4,
            "Very satisfied": 5,
        }

        satisfaction = LIKERT_TO_SCORE[likert_value]

    with col_right:
        st.caption("😊")

    col1, col2 = st.columns([1, 4])

    with col1:
        if st.button("Submit",
                     key=f"submit_rating_{message_index}",
                     type="primary"):
            st.session_state.current_satisfaction = satisfaction
            st.session_state.current_satisfaction_label = likert_value
            st.session_state.awaiting_rating = False
            st.session_state.last_rated_index = message_index

            # Run Synthesis API Pipeline and save to DB Quant
            saved_to_db = False
            save_error = None

            if not DB_AVAILABLE:
                save_error = "Database module not available"
            elif not is_database_connected():
                save_error = "Database not connected"
            else:
                user_id = get_user_id()
                if not user_id:
                    save_error = "User ID not found"
                elif len(st.session_state.chat_history) < 2:
                    save_error = "No chat history to save"
                else:
                    # Get the last user prompt and LLM response for synthesis
                    user_prompt = st.session_state.chat_history[-2].get(
                        'content', '')
                    llm_response = st.session_state.chat_history[-1].get(
                        'content', '')

                    # Call Synthesis API → Correlation → Verification → DB Store
                    # Note: Raw chat content is NOT stored, only synthesized summary
                    success, result = run_synthesis_and_store(
                        user_prompt=user_prompt,
                        llm_response=llm_response,
                        satisfaction=float(satisfaction),
                        user_id=user_id)
                    saved_to_db = success
                    if not success:
                        save_error = result

            if saved_to_db:
                st.toast(
                    "Thank you! Your rating has been recorded and verified.",
                    icon="✅")
            else:
                st.toast(f"Rating noted locally. {save_error or ''}",
                         icon="🏛️")
    with col2:
        st.caption("Your rating helps build indicators of government quality.")


def render_chat_messages() -> None:
    """Render the chat message history."""
    for i, message in enumerate(st.session_state.chat_history):
        role = message["role"]
        content = message["content"]

        with st.chat_message(role, avatar="🧑‍💻" if role == "user" else "🏛️"):
            st.markdown(content)


def render_end_user_view() -> None:
    """Render the complete End-User view with chat interface."""
    user = get_current_user()

    # Page header
    st.markdown("""
    <div class="page-header">
        <h1>🏛️ Quality of Dutch Government</h1>
        <p>Ask questions about Dutch government quality and performance indicators</p>
    </div>
    """,
                unsafe_allow_html=True)

    # Check API status
    api_ready = render_api_status()

    # Initialize chat-specific session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'awaiting_rating' not in st.session_state:
        st.session_state.awaiting_rating = False
    if 'last_rated_index' not in st.session_state:
        st.session_state.last_rated_index = -1
    if 'processed_message_count' not in st.session_state:
        st.session_state.processed_message_count = 0

    # Welcome message for new users
    if len(st.session_state.chat_history) == 0:
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            text-align: center;
        ">
            <h3 style="color: #F1F5F9; margin: 0 0 1rem 0; font-family: 'DM Sans', sans-serif;">
                Welcome to the Government Quality Research Portal
            </h3>
            <p style="color: #94A3B8; margin: 0; font-size: 0.95rem; line-height: 1.6;">
                This system helps translate qualitative reports on Dutch government performance 
                into quantitative indicators. Ask questions about government quality metrics, 
                audit reports, or policy evaluations.
            </p>
        </div>
        
        <div style="
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        ">
            <div style="
                background: rgba(255, 107, 53, 0.1);
                border: 1px solid rgba(255, 107, 53, 0.2);
                border-radius: 12px;
                padding: 1rem;
            ">
                <p style="color: #FF6B35; font-size: 1.25rem; margin: 0;">📊</p>
                <p style="color: #F1F5F9; font-weight: 500; font-size: 0.9rem; margin: 0.5rem 0 0.25rem 0;">
                    Quality Indicators
                </p>
                <p style="color: #64748B; font-size: 0.8rem; margin: 0;">
                    Ask about government performance metrics
                </p>
            </div>
            <div style="
                background: rgba(59, 130, 246, 0.1);
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 12px;
                padding: 1rem;
            ">
                <p style="color: #3B82F6; font-size: 1.25rem; margin: 0;">📋</p>
                <p style="color: #F1F5F9; font-weight: 500; font-size: 0.9rem; margin: 0.5rem 0 0.25rem 0;">
                    Audit Reports
                </p>
                <p style="color: #64748B; font-size: 0.8rem; margin: 0;">
                    Explore Court of Audit findings
                </p>
            </div>
            <div style="
                background: rgba(139, 92, 246, 0.1);
                border: 1px solid rgba(139, 92, 246, 0.2);
                border-radius: 12px;
                padding: 1rem;
            ">
                <p style="color: #8B5CF6; font-size: 1.25rem; margin: 0;">🔍</p>
                <p style="color: #F1F5F9; font-weight: 500; font-size: 0.9rem; margin: 0.5rem 0 0.25rem 0;">
                    Policy Analysis
                </p>
                <p style="color: #64748B; font-size: 0.8rem; margin: 0;">
                    Get insights from IOB evaluations
                </p>
            </div>
        </div>
        """,
                    unsafe_allow_html=True)

        # Ephemeral notice
        st.info(
            "💡 **Note**: Conversations are currently ephemeral. Your satisfaction ratings help build quantitative indicators of Dutch government performance.",
            icon="ℹ️")

    # Render existing chat messages
    render_chat_messages()

    # Show satisfaction prompt if awaiting rating (after messages are rendered)
    if st.session_state.awaiting_rating and len(
            st.session_state.chat_history) > 0:
        current_index = len(st.session_state.chat_history)
        if current_index > st.session_state.last_rated_index:
            render_satisfaction_prompt(current_index)

    # Chat input (only enabled if API is ready)
    if api_ready:
        if prompt := st.chat_input(
                "Ask about Dutch government quality and performance...",
                key="user_chat_input"):
            # GUARD: Check if we've already processed this message
            # We track by comparing chat_history length with processed count
            # Each complete interaction adds 2 messages (user + assistant)
            current_history_len = len(st.session_state.chat_history)
            expected_len = st.session_state.processed_message_count * 2

            # Only process if history length matches what we expect
            # (i.e., we haven't already added messages for this prompt)
            if current_history_len == expected_len:
                # Add user message to history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": prompt
                })

                # Display user message
                with st.chat_message("user", avatar="🧑‍💻"):
                    st.markdown(prompt)

                # Get response from Agent → LLM pipeline
                with st.chat_message("assistant", avatar="🏛️"):
                    with st.spinner("Agent analyzing query..."):
                        # send_message returns (success, response, synthesis_data)
                        success, response, synthesis_data = send_message(
                            prompt)

                        # Store synthesis data for later use when user submits satisfaction
                        if synthesis_data:
                            st.session_state.last_synthesis_data = synthesis_data

                        if success:
                            st.markdown(response)
                            # Add assistant message to history
                            st.session_state.chat_history.append({
                                "role":
                                "assistant",
                                "content":
                                response
                            })
                        else:
                            # Failed check - show the failure message (still from LLM)
                            st.warning(response)
                            st.session_state.chat_history.append({
                                "role":
                                "assistant",
                                "content":
                                response
                            })

                # Update processed count AFTER adding both messages
                st.session_state.processed_message_count += 1

                # Update interaction count
                update_interaction_count()

                # Set flag for satisfaction rating
                st.session_state.awaiting_rating = True

    else:
        st.chat_input("Chat disabled - configure API key first",
                      disabled=True,
                      key="user_chat_input_disabled")

    # Stats in sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📊 Session Stats")
        st.metric("Messages", len(st.session_state.chat_history))

        if st.session_state.get('current_satisfaction'):
            st.metric("Gov. Satisfaction",
                      f"{st.session_state.current_satisfaction}/5")

        # Model info
        st.markdown("---")
        st.markdown("### 🤖 Backend")
        backend_info = get_backend_info()
        st.caption(f"**{backend_info['backend']}**")
        st.caption(f"Model: `{backend_info['model']}`")
        st.caption(f"Status: {backend_info['status']}")

        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.awaiting_rating = False
            st.session_state.current_satisfaction = None
            st.session_state.last_rated_index = -1
            st.session_state.processed_message_count = 0
            st.session_state.last_synthesis_data = None
            clear_chat_session()
            st.rerun()
