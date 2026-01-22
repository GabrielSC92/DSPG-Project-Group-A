"""
LLM utilities for the Quality of Dutch Government application.

Uses Ollama for local LLM inference - no rate limits, runs locally.

Configure via .env:
    OLLAMA_MODEL=llama3.2
    OLLAMA_BASE_URL=http://localhost:11434
"""

import streamlit as st
from dotenv import load_dotenv
import os
import json
import re
import requests
from typing import Optional, Tuple, List, Dict, Any

from utils.rag import retrieve_chunks, format_context, format_sources_list, retrieve_summaries, format_summaries, retrieve_chunks_by_subtopics

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

# Ollama settings
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

AGENT_SYSTEM_PROMPT = """You are a retrieval agent for a Dutch Government research platform.

TASK: Analyze the user query and filter by sub-topics. Return ONLY a valid JSON object with:
- "valid": true if query is about Dutch government (else false)
- "reason": explanation if invalid
- "search_terms": list of 2-5 search terms extracted from query
- "relevant_subtopic_ids": list of sub-topic IDs from AVAILABLE SUB-TOPICS that match the query

IMPORTANT: Look at each sub-topic label. Select sub-topics that are relevant to the user's question.

Example response:
{
    "valid": true,
    "reason": "",
    "search_terms": ["submarine", "procurement"],
    "relevant_subtopic_ids": [1, 3, 5]
}

Example if no subtopics match:
{
    "valid": true,
    "reason": "",
    "search_terms": ["education", "reform"],
    "relevant_subtopic_ids": []
}"""

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


def _ollama_generate(prompt: str,
                     system: str = "",
                     timeout: int = 120) -> Tuple[bool, str]:
    """Generate response using Ollama."""
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_ctx": 16384,  # Context window (increased from 4096)
            }
        }

        if system:
            payload["system"] = system

        r = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=timeout  # Configurable timeout
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
                "num_ctx": 16384,  # Context window (increased from 4096)
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
# UNIFIED API
# =============================================================================


def _call_agent(prompt: str,
                subtopics: List[Dict[str, Any]] | None = None,
                topic_filter: str | None = None) -> Dict[str, Any]:
    """
    Call agent to validate query and extract search terms.
    Uses sub-topics for efficient filtering (much smaller context than full summaries).
    
    Args:
        prompt: User query
        subtopics: Optional list of subtopics for filtering (from get_all_subtopics_with_topics)
        topic_filter: Optional topic label to pre-filter subtopics
    """
    default = {
        "valid": True,
        "reason": "",
        "search_terms": _extract_keywords_local(prompt),
        "relevant_subtopic_ids": []
    }

    # Build compact subtopics list for agent
    subtopics_text = ""
    if subtopics:
        # Filter by topic if specified
        if topic_filter and topic_filter != "All topics":
            subtopics = [
                st for st in subtopics if st.get('topic') == topic_filter
            ]

        subtopics_text = "\nAVAILABLE SUB-TOPICS:\n"
        for st in subtopics[:50]:  # Limit to 50 subtopics (still very compact)
            subtopics_text += f"- ID {st['subtopic_id']}: [{st['topic']}] {st['subtopic']} ({st['chunk_count']} chunks)\n"

    agent_prompt = f"""{AGENT_SYSTEM_PROMPT}

{subtopics_text}

User query: {prompt}"""

    success, response = _ollama_generate(
        agent_prompt, timeout=120)  # Shorter timeout - less context

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
                                         default["search_terms"]),
                "relevant_subtopic_ids": data.get("relevant_subtopic_ids", [])
            }
    except:
        pass

    return default


def _call_llm(prompt: str, context: str) -> Tuple[bool, str]:
    """
    Call LLM to generate response.
    Uses Ollama with chat history support.
    """
    full_prompt = f"""CONTEXT:
{context if context else "No relevant documents found."}

USER QUESTION:
{prompt}

Answer based on the context above. Cite sources as [SOURCE 1], [SOURCE 2], etc."""

    # Use chat endpoint with history
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


def summarize_text(text: str, max_length: int = 300) -> Tuple[bool, str]:
    """
    Generate a summary of the given text using Ollama.
    
    Args:
        text: The text to summarize (e.g., full PDF content)
        max_length: Target length for summary in words
        
    Returns:
        Tuple of (success: bool, summary: str)
    """
    if not text or len(text.strip()) == 0:
        return False, "Empty text provided"

    # Truncate to avoid token limits and timeout issues
    # Using 2000 chars covers most executive summaries while keeping inference fast
    truncated_text = text[:2000] if len(text) > 2000 else text

    summary_prompt = f"""Provide a concise summary of the following government audit/policy document in approximately {max_length} words.
Focus on key findings, recommendations, and main topics.
Be objective and professional.

DOCUMENT:
{truncated_text}

SUMMARY:"""

    success, response = _ollama_generate(summary_prompt)

    if success:
        # Clean up response
        summary = response.strip()
        return True, summary
    else:
        return False, response


def generate_topic_label(source_folder: str,
                         sample_text: str = "") -> Tuple[bool, str]:
    """
    Generate an English topic label for a document category based on folder name and sample content.
    
    Args:
        source_folder: The folder name (e.g., "defensie", "financien")
        sample_text: Optional sample text from documents in this folder
        
    Returns:
        Tuple of (success: bool, english_label: str)
    """
    # Common Dutch to English mappings (fallback)
    KNOWN_MAPPINGS = {
        'defensie': 'Defence',
        'financien': 'Finance',
        'onderwijs': 'Education',
        'gezondheid': 'Health',
        'justitie': 'Justice',
        'buitenlandse': 'Foreign Affairs',
        'binnenlandse': 'Domestic Affairs',
        'rekenkamer': 'Audit Office',
        'infrastructuur': 'Infrastructure',
        'sociale_zaken': 'Social Affairs',
        'economische_zaken': 'Economic Affairs',
        'milieu': 'Environment',
        'landbouw': 'Agriculture',
        'veiligheid': 'Security',
    }

    # Check if we have a known mapping
    folder_lower = source_folder.lower().strip()
    if folder_lower in KNOWN_MAPPINGS:
        return True, KNOWN_MAPPINGS[folder_lower]

    # Use LLM to generate label
    prompt = f"""You are helping categorize Dutch government audit documents.

Given the folder name "{source_folder}" and the following sample text from documents in this folder:
{sample_text[:800] if sample_text else "(no sample text available)"}

Generate a short English topic label (1-3 words) that best describes this category of government documents.
The label should be professional and suitable for a dropdown menu.

Respond with ONLY the English label, nothing else.
Example labels: "Defence", "Finance", "Education", "Foreign Affairs", "Health", "Infrastructure"

LABEL:"""

    success, response = _ollama_generate(prompt, timeout=60)

    if success:
        # Clean up response - take first line, strip quotes and extra whitespace
        label = response.strip().split('\n')[0].strip('"\'').strip()
        # Capitalize properly
        label = label.title()
        # Limit length
        if len(label) > 50:
            label = label[:50]
        return True, label
    else:
        # Fallback: capitalize folder name
        fallback = source_folder.replace("_", " ").replace("-", " ").title()
        return False, fallback


def generate_subtopic_from_summary(summary: str,
                                   topic_label: str) -> Tuple[bool, str]:
    """
    Generate a sub-topic label from a document summary.
    Used for per-document subtopic assignment (all chunks from same doc get same subtopic).
    
    Args:
        summary: The document summary
        topic_label: The parent topic label (e.g., "Defence")
        
    Returns:
        Tuple of (success: bool, subtopic_label: str)
    """
    # Truncate summary to avoid token limits
    truncated = summary[:500] if len(summary) > 500 else summary

    prompt = f"""Based on this document summary, provide a short sub-topic label (3-6 words) in English.

Parent topic: {topic_label}

Document summary:
{truncated}

The sub-topic should capture the main focus of this specific document.
Examples: "Submarine Procurement Review", "Military Budget Audit 2023", "Border Security Assessment"

Respond with ONLY the sub-topic label, nothing else.

SUB-TOPIC:"""

    success, response = _ollama_generate(prompt, timeout=60)

    if success:
        # Clean up response
        label = response.strip().split('\n')[0].strip('"\'').strip()
        # Remove any preamble
        if ':' in label and len(label.split(':')[0]) < 20:
            label = label.split(':', 1)[-1].strip()
        label = label.title()
        if len(label) > 80:
            label = label[:80]
        if len(label) < 3:
            return False, f"{topic_label} - General"
        return True, label
    else:
        return False, f"{topic_label} - General"


def generate_subtopic_label(chunk_text: str,
                            topic_label: str) -> Tuple[bool, str]:
    """
    Generate an English sub-topic label for a chunk based on its content.
    
    Args:
        chunk_text: The chunk text content
        topic_label: The parent topic label (e.g., "Defence")
        
    Returns:
        Tuple of (success: bool, subtopic_label: str)
    """
    # Truncate chunk to avoid token limits
    truncated_chunk = chunk_text[:1000] if len(
        chunk_text) > 1000 else chunk_text

    prompt = f"""You are categorizing Dutch government audit document chunks.

The parent topic is: {topic_label}

Based on this text chunk, identify the specific sub-topic it covers:
---
{truncated_chunk}
---

Generate a short English sub-topic label (2-5 words) that describes the specific theme.
The sub-topic should be more specific than the parent topic "{topic_label}".

Good examples for Defence: "Submarine Procurement", "Military Budget", "Border Security", "Cybersecurity", "Personnel Training"
Good examples for Finance: "Tax Collection", "Government Debt", "Budget Allocation", "Financial Reporting"

Respond with ONLY the sub-topic label, nothing else.

SUB-TOPIC:"""

    success, response = _ollama_generate(prompt, timeout=60)

    if success:
        # Clean up response
        label = response.strip().split('\n')[0].strip('"\'').strip()
        label = label.title()
        # Limit length
        if len(label) > 100:
            label = label[:100]
        return True, label
    else:
        # Fallback: use generic label
        return False, f"{topic_label} - General"


def generate_subtopics_batch(chunks: List[str], topic_label: str) -> List[str]:
    """
    Generate sub-topic labels for multiple chunks efficiently.
    Groups similar chunks and generates labels in batches.
    
    Args:
        chunks: List of chunk texts
        topic_label: The parent topic label
        
    Returns:
        List of subtopic labels (same order as input chunks)
    """
    # For efficiency, process chunks in a single prompt asking for multiple labels
    # Limit to reasonable batch size
    MAX_CHUNKS = 10
    chunks_to_process = chunks[:MAX_CHUNKS] if len(
        chunks) > MAX_CHUNKS else chunks

    # Build the prompt with numbered chunks
    chunks_text = ""
    for i, chunk in enumerate(chunks_to_process, 1):
        truncated = chunk[:300] if len(chunk) > 300 else chunk
        chunks_text += f"\n[CHUNK {i}]\n{truncated}\n"

    prompt = f"""You are categorizing Dutch government audit document chunks.

The parent topic is: {topic_label}

Below are {len(chunks_to_process)} text chunks. For each chunk, identify a specific sub-topic (2-5 words in English).

{chunks_text}

Respond with exactly {len(chunks_to_process)} lines, one sub-topic per line, in order:
1. <sub-topic for chunk 1>
2. <sub-topic for chunk 2>
...

Example output format:
1. Submarine Procurement
2. Military Budget Oversight
3. Border Security Measures

SUB-TOPICS:"""

    success, response = _ollama_generate(prompt, timeout=120)

    labels = []
    if success:
        lines = response.strip().split('\n')
        for line in lines:
            cleaned = line.strip()

            # Skip empty lines
            if not cleaned:
                continue

            # Skip preamble lines (lines that look like introductions, not labels)
            skip_keywords = [
                'here are', 'sub-topic', 'subtopic', 'chunk', 'following',
                'below', 'output', 'result', 'answer', ':'
            ]
            is_preamble = any(kw in cleaned.lower() for kw in skip_keywords)
            if is_preamble and not any(
                    cleaned.startswith(f"{i}.") or cleaned.startswith(f"{i})")
                    for i in range(1, 11)):
                continue

            # Remove numbering like "1.", "1:", "1)", etc.
            import re
            numbered_match = re.match(r'^(\d+)[.\):\-]\s*(.+)$', cleaned)
            if numbered_match:
                cleaned = numbered_match.group(2).strip()

            # Skip if still looks like preamble after removing number
            if any(kw in cleaned.lower() for kw in
                   ['here are', 'sub-topic', 'subtopic', 'following']):
                continue

            # Clean up quotes and whitespace
            cleaned = cleaned.strip('"\'').strip()

            # Only accept reasonable length labels (2-100 chars, not too long)
            if cleaned and 2 <= len(cleaned) <= 100:
                labels.append(cleaned.title())

            # Stop once we have enough labels
            if len(labels) >= len(chunks_to_process):
                break

    # Pad with fallback if we don't have enough labels
    while len(labels) < len(chunks_to_process):
        labels.append(f"{topic_label} - General")

    # For remaining chunks beyond MAX_CHUNKS, use generic label
    while len(labels) < len(chunks):
        labels.append(f"{topic_label} - General")

    return labels


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


def _topic_to_folder(topic_label: str) -> Optional[str]:
    """
    Map a topic label (e.g., 'Defence', 'Sustainability') back to its source folder.
    Used for fallback keyword search when Agent doesn't find matching subtopics.
    """
    try:
        from utils.database import get_engine
        engine = get_engine()
        if engine is None:
            return None
        
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT source_folder FROM topics WHERE label_en = :label"),
                {"label": topic_label}
            ).fetchone()
            
            if result:
                return result[0]
    except Exception:
        pass
    
    # Fallback: convert label to likely folder name
    return topic_label.lower().replace(' ', '_')


# =============================================================================
# PUBLIC API
# =============================================================================


def is_api_configured() -> bool:
    """Check if Ollama is available."""
    return _ollama_available()


def is_llm_configured() -> bool:
    """Check if LLM is configured."""
    return _ollama_available()


def is_agent_configured() -> bool:
    """Check if Agent is configured."""
    return _ollama_available()


def init_llm() -> Tuple[bool, Optional[str]]:
    """Initialize the LLM backend (Ollama)."""
    if _ollama_available():
        return True, None
    return False, f"Ollama not running at {OLLAMA_BASE_URL}. Run: ollama serve"


def get_backend_info() -> Dict[str, str]:
    """Get info about the current backend."""
    return {
        "backend":
        "Ollama (Local)",
        "model":
        OLLAMA_MODEL,
        "status":
        ":material/check_circle: Running"
        if _ollama_available() else ":material/cancel: Not running"
    }


def send_message(
        prompt: str,
        topic: Optional[str] = None,
        subtopic: Optional[str] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Main pipeline - uses Ollama for local LLM inference.
    
    Retrieval hierarchy (drill-down):
    1. User selected specific subtopic → retrieve from that subtopic directly
    2. Agent finds matching subtopics → use those
    3. User selected topic (but no subtopic) → keyword search within topic
    4. Nothing matched → show info message
    
    Args:
        prompt: User's question
        topic: Selected topic label (e.g., "Sustainability", "Defence")
        subtopic: Selected subtopic label (e.g., "Climate Policy Impact Analysis")
    
    Returns:
        (success, response_text, metadata)
    """
    # STEP 1: Get available subtopics for agent/lookup
    try:
        from utils.database import get_all_subtopics_with_topics
        subtopics = get_all_subtopics_with_topics()
    except Exception:
        subtopics = []

    # Extract search terms locally (used for ranking within retrieved chunks)
    search_terms = _extract_keywords_local(prompt)
    
    matched_subtopic_labels = []
    chunks = []
    relevant_subtopic_ids = []

    # STEP 2: HIERARCHY - Try each level in order
    
    # Level 1: User selected a specific subtopic → use it directly (skip Agent)
    if subtopic:
        # Look up subtopic ID from label
        subtopic_id = None
        for st in subtopics:
            if st.get('subtopic') == subtopic:
                subtopic_id = st.get('subtopic_id')
                break
        
        if subtopic_id:
            relevant_subtopic_ids = [subtopic_id]
            chunks = retrieve_chunks_by_subtopics(" ".join(search_terms),
                                                  subtopic_ids=relevant_subtopic_ids,
                                                  k=12)
            matched_subtopic_labels = [subtopic]
    
    # Level 2: No subtopic selected or no chunks found → try Agent matching
    if not chunks:
        agent_result = _call_agent(prompt, subtopics, topic_filter=topic)

        if not agent_result["valid"]:
            return False, (
                f"I cannot help with this query. {agent_result['reason']}\n\n"
                "I can help with:\n"
                "- Dutch government audit reports\n"
                "- Ministry performance and budgets\n"
                "- Policy evaluations"), None

        relevant_subtopic_ids = agent_result.get("relevant_subtopic_ids", [])
        search_terms = agent_result.get("search_terms", search_terms)

        if relevant_subtopic_ids:
            # Agent found matching subtopics
            for st in subtopics:
                if st.get('subtopic_id') in relevant_subtopic_ids:
                    matched_subtopic_labels.append(st.get('subtopic', 'Unknown'))

            chunks = retrieve_chunks_by_subtopics(" ".join(search_terms),
                                                  subtopic_ids=relevant_subtopic_ids,
                                                  k=12)
    
    # Level 3: Still no chunks, but user selected a topic → keyword search within topic
    if not chunks and topic and topic != "All topics":
        chunks = retrieve_chunks(" ".join(search_terms),
                                 k=12,
                                 source_folder=_topic_to_folder(topic))
        matched_subtopic_labels = [f"{topic} (keyword search)"]
    
    # Level 4: Nothing worked → show helpful message
    if not chunks:
        return False, (
            "No relevant content found for your query.\n\n"
            "Please try:\n"
            "- Selecting a specific topic or sub-topic from the dropdowns\n"
            "- Rephrasing your question with different keywords"), None

    # Build context from filtered chunks only
    context = format_context(chunks) if chunks else ""

    # STEP 4: LLM - generate response
    success, response = _call_llm(prompt, context)

    if not success:
        return False, response, None

    # Add sources
    if chunks:
        response += "\n\n**Sources:**\n" + format_sources_list(chunks)

    metadata = {
        "backend": "ollama",
        "topic": topic,
        "search_terms": search_terms,
        "num_chunks": len(chunks),
        "subtopics_used": len(relevant_subtopic_ids),
        "matched_subtopics": matched_subtopic_labels  # For summary
    }

    return True, response, metadata


# =============================================================================
# SYNTHESIS & STORAGE
# =============================================================================


def synthesize_and_store(
        user_prompt: str,
        llm_response: str,
        satisfaction: float,
        user_id: str,
        topic: Optional[str] = None,
        matched_subtopics: List[str] = None) -> Tuple[bool, str]:
    """
    Store interaction with local processing (no API calls).
    
    Args:
        user_prompt: The user's original question
        llm_response: The LLM's response
        satisfaction: User satisfaction score (1-5)
        user_id: The user's ID
        topic: Optional topic label selected by the user (e.g., "Defence")
        matched_subtopics: List of subtopic labels that matched the query
    """
    try:
        from utils.database import save_interaction, is_database_connected, get_topic_id_by_label

        if not is_database_connected():
            return False, "Database not connected"

        # Look up topic_id from topic label
        topic_id = None
        if topic and topic != "All topics":
            topic_id = get_topic_id_by_label(topic)

        # Create summary from matched subtopics (preferred) or fallback
        if matched_subtopics:
            # Use matched subtopic labels as summary (limit to first 3)
            subtopics_str = ", ".join(matched_subtopics[:3])
            if len(matched_subtopics) > 3:
                subtopics_str += f" (+{len(matched_subtopics) - 3} more)"
            summary = subtopics_str
        else:
            # Fallback: query didn't match any subtopics
            summary = "General query"

        correlation = _compute_correlation(user_prompt, llm_response)
        flag = 'V' if correlation >= 0.3 else 'U'

        return save_interaction(user_id=user_id,
                                satisfaction_raw=satisfaction,
                                summary=summary,
                                topic_id=topic_id,
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
    """
    Compute Response Quality Score (RQS) locally.
    
    This is a heuristic score (0.0-1.0) measuring response quality based on:
    - Source citations: +0.05 per [SOURCE] citation (max 0.30)
    - Response length: +0.15 if >500 chars, +0.10 more if >1000 chars
    - Lexical overlap: +0.03 per shared word between prompt and response (max 0.30)
    - Penalty: -0.20 if "no relevant" found (indicates failed retrieval)
    
    A score >= 0.30 marks the response as "Verified" (V).
    """
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
    """Clear chat session."""
    if 'ollama_history' in st.session_state:
        del st.session_state['ollama_history']


def get_chat_session():
    """Get current chat session."""
    return st.session_state.get('ollama_history', [])


# Alias
run_synthesis_and_store = synthesize_and_store
