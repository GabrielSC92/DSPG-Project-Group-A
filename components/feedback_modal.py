"""
Feedback Modal Component
Provides a feedback pop-up modal for users to send feedback to developers.
"""

import streamlit as st
from datetime import datetime
from utils.auth import get_current_user, get_user_id


def render_feedback_modal() -> None:
    """Render the feedback modal dialog."""
    
    @st.dialog("💬 Send Feedback to Developers", width="large")
    def feedback_dialog():
        user = get_current_user()
        
        st.markdown("""
        <style>
            .feedback-intro {
                background: linear-gradient(135deg, rgba(255, 107, 53, 0.1), rgba(59, 130, 246, 0.1));
                border: 1px solid rgba(255, 107, 53, 0.2);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1.5rem;
            }
            .feedback-intro p {
                color: #94A3B8;
                margin: 0;
                font-size: 0.9rem;
            }
        </style>
        <div class="feedback-intro">
            <p>Your feedback helps us improve the Quality of Dutch Government research platform. 
            Please share your thoughts, suggestions, or report any issues you've encountered.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Feedback category
        feedback_type = st.selectbox(
            "Feedback Type",
            options=[
                "General Feedback",
                "Bug Report",
                "Feature Request",
                "Data Quality Issue",
                "User Experience",
                "Other"
            ],
            key="feedback_type"
        )
        
        # Feedback text
        feedback_text = st.text_area(
            "Your Feedback",
            placeholder="Please describe your feedback in detail...",
            height=200,
            max_chars=2000,
            key="feedback_text"
        )
        
        # Character count
        char_count = len(feedback_text) if feedback_text else 0
        st.caption(f"{char_count}/2000 characters")
        
        # Priority (for bug reports)
        if feedback_type == "Bug Report":
            priority = st.select_slider(
                "Priority Level",
                options=["Low", "Medium", "High", "Critical"],
                value="Medium",
                key="feedback_priority"
            )
        else:
            priority = "N/A"
        
        # Allow anonymous
        include_user_info = st.checkbox(
            "Include my user information (helps with follow-up)",
            value=True,
            key="include_user_info"
        )
        
        st.markdown("---")
        
        # Action buttons
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("Cancel", use_container_width=True, key="cancel_feedback"):
                st.session_state.show_feedback_modal = False
                st.rerun()
        
        with col1:
            if st.button("📤 Submit Feedback", type="primary", use_container_width=True, key="submit_feedback"):
                if feedback_text and len(feedback_text.strip()) >= 10:
                    # Prepare feedback data
                    feedback_data = {
                        "timestamp": datetime.now().isoformat(),
                        "type": feedback_type,
                        "message": feedback_text,
                        "priority": priority,
                        "user_id": get_user_id() if include_user_info else "anonymous",
                        "user_email": user.get("email") if include_user_info and user else "anonymous"
                    }
                    
                    # In production, this would send to backend
                    # For now, we'll just show success and log
                    print(f"FEEDBACK SUBMITTED: {feedback_data}")
                    
                    st.success("✅ Thank you! Your feedback has been submitted successfully.")
                    
                    
                    # Close modal after brief delay
                    st.session_state.show_feedback_modal = False
                    st.rerun()
                    
                else:
                    st.error("⚠️ Please provide at least 10 characters of feedback.")
    
    # Trigger the dialog
    feedback_dialog()


def render_feedback_button(location: str = "sidebar") -> None:
    """
    Render a feedback button that triggers the modal.
    
    Args:
        location: Where to render the button ("sidebar" or "main")
    """
    button_container = st.sidebar if location == "sidebar" else st
    
    if button_container.button("💬 Send Feedback", use_container_width=True, key=f"feedback_btn_{location}"):
        st.session_state.show_feedback_modal = True
        st.rerun()

