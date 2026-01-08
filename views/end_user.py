"""
End-User View for the Quality of Dutch Government application.
Provides a chat interface for users to interact with the LLM system
and rate their satisfaction with responses.
"""

import streamlit as st
from utils.auth import get_current_user, update_interaction_count, get_user_id, is_using_database
from utils.llm import init_gemini, send_message, clear_chat_session, is_api_configured

# Try to import database functions
try:
    from utils.database import save_interaction, is_database_connected
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


def render_api_status() -> bool:
    """
    Render the API connection status and return whether it's configured.
    
    Returns:
        bool: True if API is configured and ready, False otherwise
    """
    # Only check if API key exists - don't re-initialize
    if is_api_configured():
        # Ensure it's initialized (this is idempotent now)
        success, _ = init_gemini()
        if success:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1rem;">
                <span style="
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 0.8rem;
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
                    Connected to Gemini
                </span>
            </div>
            <style>
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            </style>
            """, unsafe_allow_html=True)
            return True
    
    # Not configured
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem;">
        <span style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
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
                box-shadow: 0 0 8px #f87171;
            "></span>
            API Not Configured
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    st.warning("⚠️ Please add your Gemini API key to the `.env` file")
    st.code("GEMINI_API_KEY=your_actual_api_key_here", language="bash")
    st.info("Get your free API key at: https://makersuite.google.com/app/apikey")
    return False


def render_satisfaction_prompt(message_index: int) -> None:
    """Render the satisfaction rating prompt to capture citizen sentiment about government performance."""
    st.markdown("""
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
    """, unsafe_allow_html=True)
    
    col_left, col_mid, col_right = st.columns([1, 8, 1])
    with col_left:
        st.caption("😞")
    with col_mid:
        satisfaction = st.slider(
            "Rate government performance",
            min_value=0,
            max_value=10,
            value=5,
            key=f"satisfaction_{message_index}",
            label_visibility="collapsed",
            help="0 = Very dissatisfied, 10 = Very satisfied with government performance"
        )
    with col_right:
        st.caption("😊")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Submit", key=f"submit_rating_{message_index}", type="primary"):
            st.session_state.current_satisfaction = satisfaction
            st.session_state.awaiting_rating = False
            st.session_state.last_rated_index = message_index
            
            # Save to database if available
            saved_to_db = False
            if DB_AVAILABLE and is_database_connected():
                user_id = get_user_id()
                if user_id:
                    # Get the topic summary from the last assistant message
                    topic_summary = ""
                    if len(st.session_state.chat_history) >= 2:
                        # Get the user's question as context
                        user_msg = st.session_state.chat_history[-2].get('content', '')[:200]
                        assistant_msg = st.session_state.chat_history[-1].get('content', '')[:500]
                        topic_summary = f"Q: {user_msg}\nA: {assistant_msg}"
                    
                    success, result = save_interaction(
                        user_id=user_id,
                        satisfaction_raw=float(satisfaction),
                        summary=topic_summary,
                        correlation_index=None,  # Set by RAG system later
                        verification_flag='U'    # Unverified without RAG
                    )
                    saved_to_db = success
            
            if saved_to_db:
                st.toast("Thank you! Your rating has been recorded.", icon="✅")
            else:
                st.toast("Thank you for your feedback on government performance!", icon="🏛️")
            st.rerun()
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
    """, unsafe_allow_html=True)
    
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
        """, unsafe_allow_html=True)
        
        # Ephemeral notice
        st.info("💡 **Note**: Conversations are currently ephemeral. Your satisfaction ratings help build quantitative indicators of Dutch government performance.", icon="ℹ️")
    
    # Render existing chat messages
    render_chat_messages()
    
    # Show satisfaction prompt if awaiting rating (after messages are rendered)
    if st.session_state.awaiting_rating and len(st.session_state.chat_history) > 0:
        current_index = len(st.session_state.chat_history)
        if current_index > st.session_state.last_rated_index:
            render_satisfaction_prompt(current_index)
    
    # Chat input (only enabled if API is ready)
    if api_ready:
        if prompt := st.chat_input("Ask about Dutch government quality and performance...", key="user_chat_input"):
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
                
                # Get response from Gemini (SINGLE API call, protected by guard)
                with st.chat_message("assistant", avatar="🏛️"):
                    with st.spinner("Analyzing your query..."):
                        success, response = send_message(prompt)
                        
                        if success:
                            st.markdown(response)
                            # Add assistant message to history
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": response
                            })
                        else:
                            error_msg = f"❌ {response}"
                            st.error(error_msg)
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": error_msg
                            })
                
                # Update processed count AFTER adding both messages
                st.session_state.processed_message_count += 1
                
                # Update interaction count
                update_interaction_count()
                
                # Set flag for satisfaction rating
                st.session_state.awaiting_rating = True
                
                # Now safe to rerun - the guard will prevent re-processing
                st.rerun()
    else:
        st.chat_input("Chat disabled - configure API key first", disabled=True, key="user_chat_input_disabled")
    
    # Stats in sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📊 Session Stats")
        st.metric("Messages", len(st.session_state.chat_history))
        
        if st.session_state.get('current_satisfaction'):
            st.metric("Gov. Satisfaction", f"{st.session_state.current_satisfaction}/10")
        
        # Model info
        st.markdown("---")
        st.markdown("### 🤖 Model")
        st.caption("Gemini 2.5 Flash")
        st.caption("⚡ 5 RPM / 20 RPD limit")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.awaiting_rating = False
            st.session_state.current_satisfaction = None
            st.session_state.last_rated_index = -1
            st.session_state.processed_message_count = 0
            clear_chat_session()
            st.rerun()
