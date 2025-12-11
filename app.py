import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(page_title="Gemini Chat", page_icon="✨", layout="centered")

# Custom CSS for a beautiful UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Outfit:wght@300;400;500;600&display=swap');
    
    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #12121a;
        --accent: #6366f1;
        --accent-glow: rgba(99, 102, 241, 0.3);
        --text-primary: #e4e4e7;
        --text-muted: #71717a;
        --border: #27272a;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #18181b 50%, #0f0f14 100%);
    }
    
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
        margin-bottom: 1rem;
    }
    
    .main-header h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 2.5rem;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .main-header p {
        font-family: 'Outfit', sans-serif;
        color: var(--text-muted);
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    .stChatMessage {
        background: rgba(18, 18, 26, 0.6) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px);
        font-family: 'Outfit', sans-serif;
    }
    
    .stChatMessage [data-testid="chatAvatarIcon-user"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    }
    
    .stChatMessage [data-testid="chatAvatarIcon-assistant"] {
        background: linear-gradient(135deg, #ec4899, #f43f5e) !important;
    }
    
    .stChatInputContainer {
        border-color: var(--border) !important;
    }
    
    .stChatInputContainer > div {
        background: rgba(18, 18, 26, 0.8) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
    }
    
    .stChatInputContainer textarea {
        font-family: 'Outfit', sans-serif !important;
        color: var(--text-primary) !important;
    }
    
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 1rem;
    }
    
    .status-connected {
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.3);
        color: #4ade80;
    }
    
    .status-disconnected {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #f87171;
    }
    
    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    .dot-green {
        background: #4ade80;
        box-shadow: 0 0 8px #4ade80;
    }
    
    .dot-red {
        background: #f87171;
        box-shadow: 0 0 8px #f87171;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .stButton > button {
        font-family: 'Outfit', sans-serif !important;
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        border: none !important;
        border-radius: 8px !important;
        color: white !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3) !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""",
            unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>✨ Gemini Chat</h1>
    <p>Powered by Google's Gemini AI</p>
</div>
""",
            unsafe_allow_html=True)

# Get API key
api_key = os.getenv("GEMINI_API_KEY")

# Check API key status
if not api_key or api_key == "your_api_key_here":
    st.markdown("""
    <div style="text-align: center;">
        <span class="status-badge status-disconnected">
            <span class="dot dot-red"></span>
            API Key Missing
        </span>
    </div>
    """,
                unsafe_allow_html=True)

    st.warning("⚠️ Please add your Gemini API key to the `.env` file")
    st.code("GEMINI_API_KEY=your_actual_api_key_here", language="bash")
    st.info(
        "Get your free API key at: https://makersuite.google.com/app/apikey")
    st.stop()

# Configure Gemini
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    st.markdown("""
    <div style="text-align: center;">
        <span class="status-badge status-connected">
            <span class="dot dot-green"></span>
            Connected to Gemini
        </span>
    </div>
    """,
                unsafe_allow_html=True)
except Exception as e:
    st.error(f"Failed to configure Gemini: {e}")
    st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Message Gemini..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response from Gemini
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                response_text = response.text
                st.markdown(response_text)

                # Add assistant response to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text
                })
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)

# Sidebar with clear button
with st.sidebar:
    st.markdown("### 🎛️ Controls")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat = model.start_chat(history=[])
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.markdown(f"**Messages:** {len(st.session_state.messages)}")
    st.markdown(f"**Model:** gemini-2.5-flash")
