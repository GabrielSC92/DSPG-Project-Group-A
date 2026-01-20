"""
LLM utilities for the Quality of Dutch Government application.

Supports multiple backends:
- Gemini (cloud): Free tier with rate limits
- Ollama (local): No rate limits, runs locally

Configure via .env:
    LLM_BACKEND=ollama|gemini  (default: gemini)
    
For Ollama:
    OLLAMA_MODEL=llama3.2
    OLLAMA_BASE_URL=http://localhost:11434
    
For Gemini:
    GEMINI_API_KEY_LLM=your_key
    GEMINI_API_KEY_AGENT=your_key
"""

import streamlit as st
from dotenv import load_dotenv
import os
import json
import re
import requests
from typing import Optional, Tuple, List, Dict, Any

from utils.rag import retrieve_chunks, format_context, format_sources_list

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

LLM_BACKEND = os.getenv("LLM_BACKEND",
                        "gemini").lower()  # "gemini" or "ollama"

# Ollama settings
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Gemini settings
GEMINI_API_KEY_LLM = os.getenv("GEMINI_API_KEY_LLM")
GEMINI_API_KEY_AGENT = os.getenv("GEMINI_API_KEY_AGENT")

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

AGENT_SYSTEM_PROMPT = """You are a retrieval agent for a Dutch Government research platform.

Analyze the user query and respond with ONLY a JSON object:
{
    "valid": true/false,
    "reason": "brief reason if invalid",
    "search_terms": ["term1", "term2", "term3"]
}

Invalid: unrelated to Dutch government, harmful, too vague.
Valid: Dutch government audits, policy, ministries, performance."""

LLM_SYSTEM_PROMPT = """You are an AI assistant for the Quality of Dutch Government research platform.
Help users understand Dutch government audit reports and performance indicators.

Rules:
1. Use ONLY the CONTEXT provided to answer
2. Cite sources as [SOURCE 1], [SOURCE 2], etc.
3. If context lacks the answer, say so clearly
4. Be concise and professional"""

# =============================================================================
# OLLAMA BACKEND
# =============================================================================


def _ollama_available() -> bool:
    """Check if Ollama is running."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return r.status_code == 200
    except:
        return False


def _ollama_generate(prompt: str, system: str = "") -> Tuple[bool, str]:
    """Generate response using Ollama."""
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_ctx": 4096,  # Context window
            }
        }

        if system:
            payload["system"] = system

        r = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120  # Local models can be slow
        )

        if r.status_code == 200:
            return True, r.json().get("response", "")
        else:
            return False, f"Ollama error: {r.status_code}"

    except requests.exceptions.ConnectionError:
        return False, "Ollama not running. Start with: ollama serve"
    except Exception as e:
        return False, f"Ollama error: {str(e)}"


def _ollama_chat(messages: List[Dict], system: str = "") -> Tuple[bool, str]:
    """Chat completion using Ollama (maintains conversation)."""
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_ctx": 4096,
            }
        }

        # Add system message at the start
        if system:
            payload["messages"] = [{
                "role": "system",
                "content": system
            }] + messages

        r = requests.post(f"{OLLAMA_BASE_URL}/api/chat",
                          json=payload,
                          timeout=120)

        if r.status_code == 200:
            return True, r.json().get("message", {}).get("content", "")
        else:
            return False, f"Ollama error: {r.status_code}"

    except requests.exceptions.ConnectionError:
        return False, "Ollama not running. Start with: ollama serve"
    except Exception as e:
        return False, f"Ollama error: {str(e)}"


# =============================================================================
# GEMINI BACKEND
# =============================================================================


def _gemini_available() -> bool:
    """Check if Gemini API keys are configured."""
    return bool(GEMINI_API_KEY_LLM
                and GEMINI_API_KEY_LLM != "your_api_key_here")


def _gemini_generate(prompt: str,
                     system: str = "",
                     use_agent_key: bool = False) -> Tuple[bool, str]:
    """Generate response using Gemini."""
    try:
        import google.generativeai as genai

        api_key = GEMINI_API_KEY_AGENT if use_agent_key else GEMINI_API_KEY_LLM
        if not api_key:
            return False, "Gemini API key not configured"

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')

        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = model.generate_content(full_prompt)

        return True, response.text

    except Exception as e:
        return False, f"Gemini error: {str(e)}"


def _gemini_chat(prompt: str, system: str = "") -> Tuple[bool, str]:
    """Chat using Gemini with session state."""
    try:
        import google.generativeai as genai

        if not GEMINI_API_KEY_LLM:
            return False, "Gemini API key not configured"

        genai.configure(api_key=GEMINI_API_KEY_LLM)

        if 'gemini_model' not in st.session_state:
            st.session_state.gemini_model = genai.GenerativeModel(
                'gemini-2.0-flash', system_instruction=system)

        if 'gemini_chat' not in st.session_state:
            st.session_state.gemini_chat = st.session_state.gemini_model.start_chat(
                history=[])

        response = st.session_state.gemini_chat.send_message(prompt)
        return True, response.text

    except Exception as e:
        return False, f"Gemini error: {str(e)}"


# =============================================================================
# UNIFIED API (switches based on backend)
# =============================================================================


def _call_agent(prompt: str) -> Dict[str, Any]:
    """
    Call agent to validate query and extract search terms.
    Uses configured backend (Ollama or Gemini).
    """
    default = {
        "valid": True,
        "reason": "",
        "search_terms": _extract_keywords_local(prompt)
    }

    agent_prompt = f"""{AGENT_SYSTEM_PROMPT}

User query: {prompt}"""

    if LLM_BACKEND == "ollama":
        success, response = _ollama_generate(agent_prompt)
    else:
        success, response = _gemini_generate(agent_prompt, use_agent_key=True)

    if not success:
        return default

    # Parse JSON response
    try:
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return {
                "valid": data.get("valid", True),
                "reason": data.get("reason", ""),
                "search_terms": data.get("search_terms",
                                         default["search_terms"])
            }
    except:
        pass

    return default


def _call_llm(prompt: str, context: str) -> Tuple[bool, str]:
    """
    Call LLM to generate response.
    Uses configured backend with chat history support.
    """
    full_prompt = f"""CONTEXT:
{context if context else "No relevant documents found."}

USER QUESTION:
{prompt}

Answer based on the context above. Cite sources as [SOURCE 1], [SOURCE 2], etc."""

    if LLM_BACKEND == "ollama":
        # For Ollama, use chat endpoint with history
        if 'ollama_history' not in st.session_state:
            st.session_state.ollama_history = []

        # Add user message
        st.session_state.ollama_history.append({
            "role": "user",
            "content": full_prompt
        })

        success, response = _ollama_chat(st.session_state.ollama_history,
                                         system=LLM_SYSTEM_PROMPT)

        if success:
            # Add assistant response to history
            st.session_state.ollama_history.append({
                "role": "assistant",
                "content": response
            })

        return success, response
    else:
        return _gemini_chat(full_prompt, system=LLM_SYSTEM_PROMPT)


def _extract_keywords_local(prompt: str) -> List[str]:
    """Local keyword extraction (no API call)."""
    dutch_terms = {
        'ministerie', 'minister', 'defensie', 'financien', 'onderwijs',
        'gezondheid', 'justitie', 'buitenlandse', 'binnenlandse', 'rekenkamer',
        'audit', 'rapport', 'beleid', 'begroting', 'uitgaven', 'evaluatie',
        'onderzoek', 'kwaliteit', 'overheid'
    }

    words = re.findall(r'\b\w+\b', prompt.lower())
    keywords = []

    for word in words:
        if len(word) >= 3:
            if word in dutch_terms:
                keywords.insert(0, word)
            elif word not in [
                    'the', 'and', 'for', 'het', 'een', 'van', 'wat', 'hoe'
            ]:
                keywords.append(word)

    return keywords[:10]


# =============================================================================
# PUBLIC API
# =============================================================================


def is_api_configured() -> bool:
    """Check if the configured backend is available."""
    if LLM_BACKEND == "ollama":
        return _ollama_available()
    else:
        return _gemini_available() and bool(GEMINI_API_KEY_AGENT)


def is_llm_configured() -> bool:
    """Check if LLM is configured."""
    if LLM_BACKEND == "ollama":
        return _ollama_available()
    return _gemini_available()


def is_agent_configured() -> bool:
    """Check if Agent is configured."""
    if LLM_BACKEND == "ollama":
        return _ollama_available()
    return bool(GEMINI_API_KEY_AGENT
                and GEMINI_API_KEY_AGENT != "your_api_key_here")


def init_gemini() -> Tuple[bool, Optional[str]]:
    """Initialize the LLM backend."""
    if LLM_BACKEND == "ollama":
        if _ollama_available():
            return True, None
        return False, f"Ollama not running at {OLLAMA_BASE_URL}. Run: ollama serve"
    else:
        if not _gemini_available():
            return False, "GEMINI_API_KEY_LLM not configured"
        if not GEMINI_API_KEY_AGENT:
            return False, "GEMINI_API_KEY_AGENT not configured"
        return True, None


def get_backend_info() -> Dict[str, str]:
    """Get info about the current backend."""
    if LLM_BACKEND == "ollama":
        return {
            "backend": "Ollama (Local)",
            "model": OLLAMA_MODEL,
            "status": "✅ Running" if _ollama_available() else "❌ Not running"
        }
    else:
        return {
            "backend": "Gemini (Cloud)",
            "model": "gemini-2.0-flash",
            "status":
            "✅ Configured" if _gemini_available() else "❌ Not configured"
        }


def send_message(prompt: str, topic: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Main pipeline - works with both Ollama and Gemini.
    
    Returns:
        (success, response_text, metadata)
    """
    # STEP 1: Agent - validate and extract search terms
    agent_result = _call_agent(prompt)

    if not agent_result["valid"]:
        return False, (
            f"I cannot help with this query. {agent_result['reason']}\n\n"
            "I can help with:\n"
            "- Dutch government audit reports\n"
            "- Ministry performance and budgets\n"
            "- Policy evaluations"), None

    # STEP 2: Retrieve from database (local, no API)
    search_terms = agent_result["search_terms"]
    chunks = retrieve_chunks(" ".join(search_terms), k=6, source_folder=topic)


    if not chunks:
        chunks = retrieve_chunks(prompt, k=6, source_folder=topic)

    context = format_context(chunks)

    # STEP 3: LLM - generate response
    success, response = _call_llm(prompt, context)

    if not success:
        return False, response, None

    # Add sources
    if chunks:
        response += "\n\n**Sources:**\n" + format_sources_list(chunks)

    metadata = {
        "backend": LLM_BACKEND,
        "topic": topic,
        "search_terms": search_terms,
        "num_chunks": len(chunks)
    }

    return True, response, metadata


# =============================================================================
# SYNTHESIS & STORAGE
# =============================================================================


def synthesize_and_store(user_prompt: str, llm_response: str,
                         satisfaction: float,
                         user_id: str) -> Tuple[bool, str]:
    """Store interaction with local processing (no API calls)."""
    try:
        from utils.database import save_interaction, is_database_connected

        if not is_database_connected():
            return False, "Database not connected"

        # Local summary (no API)
        topic = _create_local_summary(llm_response)
        correlation = _compute_correlation(user_prompt, llm_response)
        flag = 'V' if correlation >= 0.3 else 'U'

        return save_interaction(user_id=user_id,
                                satisfaction_raw=satisfaction,
                                summary=topic,
                                correlation_index=correlation,
                                verification_flag=flag)

    except Exception as e:
        return False, str(e)


def _create_local_summary(response: str) -> str:
    """Create topic summary locally."""
    sentences = response.split('.')
    if sentences:
        return f"Query about: {sentences[0].strip()[:200]}"
    return "Government audit inquiry"


def _compute_correlation(prompt: str, response: str) -> float:
    """Compute correlation score locally."""
    score = 0.0

    if "[SOURCE" in response:
        score += min(0.3, response.count("[SOURCE") * 0.05)

    if len(response) > 500:
        score += 0.15
    if len(response) > 1000:
        score += 0.1

    prompt_words = set(prompt.lower().split())
    response_words = set(response.lower().split())
    score += min(0.3, len(prompt_words & response_words) * 0.03)

    if "no relevant" in response.lower():
        score -= 0.2

    return max(0.0, min(1.0, score))


# =============================================================================
# UTILITIES
# =============================================================================


def clear_chat_session():
    """Clear chat session for both backends."""
    keys_to_clear = ['gemini_model', 'gemini_chat', 'ollama_history']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def get_chat_session():
    """Get current chat session."""
    if LLM_BACKEND == "ollama":
        return st.session_state.get('ollama_history', [])
    return st.session_state.get('gemini_chat')


def get_gemini_model():
    """Backward compatibility."""
    return st.session_state.get('gemini_model')


# Alias
run_synthesis_and_store = synthesize_and_store
