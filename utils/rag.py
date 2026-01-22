from typing import List, Dict, Any
from sqlalchemy import text
from utils.database import get_engine


def retrieve_chunks(
        query: str,
        k: int = 6,
        source_folder: str | None = None,
        document_ids: List[int] | None = None) -> List[Dict[str, Any]]:
    """
    Retrieve top-k chunks from rag_chunks using naive keyword matching (LIKE).
    Returns dicts with chunk_text + metadata.
    
    Args:
        query: Search query
        k: Number of chunks to retrieve
        source_folder: Optional category filter
        document_ids: Optional list of document IDs to restrict search to (for smart filtering)
    """
    engine = get_engine()
    if engine is None:
        return []

    tokens = [t.strip().lower() for t in query.split() if len(t.strip()) >= 3]
    if not tokens:
        return []

    conditions = []
    params: Dict[str, Any] = {}

    # limit tokens to keep query sane
    for i, tok in enumerate(tokens[:10]):
        conditions.append(f"LOWER(c.chunk_text) LIKE :t{i}")
        params[f"t{i}"] = f"%{tok}%"

    where_clause = " OR ".join(conditions)

    #topic filter te reduce
    topic_filter_sql = ""
    if source_folder and source_folder != "All topics":
        topic_filter_sql = " AND d.source_folder = :source_folder"
        params["source_folder"] = source_folder

    # Document ID filter for smart filtering
    doc_filter_sql = ""
    if document_ids:
        doc_filter_sql = f" AND d.id IN ({','.join([':doc_id_' + str(i) for i in range(len(document_ids))])})"
        for i, doc_id in enumerate(document_ids):
            params[f"doc_id_{i}"] = doc_id

    sql = f"""
    SELECT
        c.chunk_text AS chunk_text,
        c.chunk_index AS chunk_index,
        d.source_folder AS source_folder,
        d.file_name AS file_name,
        d.doc_key AS doc_key
    FROM rag_chunks c
    JOIN rag_documents d ON d.id = c.document_id
    WHERE {where_clause}
    {topic_filter_sql}
    {doc_filter_sql}
    LIMIT :k
    """

    params["k"] = k

    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()

    return [dict(r) for r in rows]


def retrieve_summaries(
        query: str,
        k: int = 5,
        source_folder: str | None = None) -> List[Dict[str, Any]]:
    """
    Retrieve top-k document summaries using keyword matching.
    Useful for agent to understand which documents are relevant before retrieving chunks.
    
    Returns dicts with summary + document metadata.
    """
    engine = get_engine()
    if engine is None:
        return []

    tokens = [t.strip().lower() for t in query.split() if len(t.strip()) >= 3]
    if not tokens:
        return []

    conditions = []
    params: Dict[str, Any] = {}

    # Match tokens against both summary and document metadata
    for i, tok in enumerate(tokens[:10]):
        conditions.append(
            f"(LOWER(d.summary) LIKE :t{i} OR LOWER(d.file_name) LIKE :t{i})")
        params[f"t{i}"] = f"%{tok}%"

    where_clause = " OR ".join(conditions)

    # Filter by category if specified
    topic_filter_sql = ""
    if source_folder and source_folder != "All topics":
        topic_filter_sql = " AND d.source_folder = :source_folder"
        params["source_folder"] = source_folder

    # Only return documents with summaries
    sql = f"""
    SELECT DISTINCT
        d.id AS document_id,
        d.summary AS summary,
        d.source_folder AS source_folder,
        d.file_name AS file_name,
        d.doc_key AS doc_key
    FROM rag_documents d
    WHERE d.summary IS NOT NULL
    AND ({where_clause})
    {topic_filter_sql}
    LIMIT :k
    """

    params["k"] = k

    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()

    return [dict(r) for r in rows]


def format_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Format retrieved chunks into a context block that the LLM can cite.
    """
    if not chunks:
        return ""

    blocks = []
    for i, ch in enumerate(chunks, start=1):
        src = f"{ch.get('source_folder','?')}/{ch.get('file_name','?')} (chunk {ch.get('chunk_index','?')})"
        blocks.append(f"[SOURCE {i}] {src}\n{ch['chunk_text']}")
    return "\n\n".join(blocks)


def format_summaries(summaries: List[Dict[str, Any]]) -> str:
    """
    Format retrieved summaries into a context block for agent overview.
    Helps agent understand which documents are most relevant before detailed retrieval.
    """
    if not summaries:
        return ""

    blocks = []
    for i, doc in enumerate(summaries, start=1):
        src = f"{doc.get('source_folder','?')}/{doc.get('file_name','?')}"
        blocks.append(
            f"[DOC {i}] {src}\n{doc.get('summary', 'No summary available')}")
    return "\n\n".join(blocks)


def format_sources_list(chunks: List[Dict[str, Any]]) -> str:
    """
    Format sources into a consolidated list, grouping chunks from the same document.
    
    Example output:
    - [SOURCES 1-5] defensie/rapport.pdf (chunks 0-4)
    - [SOURCE 6] defensie/other.pdf (chunk 2)
    - [SOURCES 7, 9-11] defensie/another.pdf (chunks 1, 5-7)
    """
    if not chunks:
        return ""

    # Group chunks by file path (source_folder/file_name)
    # Track: file_path -> [(source_number, chunk_index), ...]
    file_groups: Dict[str, List[tuple]] = {}

    for i, ch in enumerate(chunks, start=1):
        file_path = f"{ch.get('source_folder', '?')}/{ch.get('file_name', '?')}"
        chunk_idx = ch.get('chunk_index', '?')

        if file_path not in file_groups:
            file_groups[file_path] = []
        file_groups[file_path].append((i, chunk_idx))

    def format_number_range(numbers: List[int]) -> str:
        """Format a list of numbers into ranges (e.g., [1, 2, 3, 5, 7, 8] -> '1-3, 5, 7-8')."""
        if not numbers:
            return ""

        # Sort and handle non-numeric values
        try:
            sorted_nums = sorted([int(n) for n in numbers])
        except (ValueError, TypeError):
            # If conversion fails, just join with commas
            return ", ".join(str(n) for n in numbers)

        ranges = []
        start = sorted_nums[0]
        end = start

        for num in sorted_nums[1:]:
            if num == end + 1:
                end = num
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = num
                end = num

        # Add the last range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")

        return ", ".join(ranges)

    lines = []
    for file_path, source_chunks in file_groups.items():
        source_numbers = [sc[0] for sc in source_chunks]
        chunk_indices = [sc[1] for sc in source_chunks]

        # Format source numbers
        if len(source_numbers) == 1:
            source_label = f"[SOURCE {source_numbers[0]}]"
        else:
            source_range = format_number_range(source_numbers)
            source_label = f"[SOURCES {source_range}]"

        # Format chunk indices
        if len(chunk_indices) == 1:
            chunk_label = f"chunk {chunk_indices[0]}"
        else:
            chunk_range = format_number_range(chunk_indices)
            chunk_label = f"chunks {chunk_range}"

        lines.append(f"- {source_label} {file_path} ({chunk_label})")

    return "\n".join(lines)


def retrieve_chunks_by_subtopics(query: str,
                                 subtopic_ids: List[int],
                                 k: int = 12) -> List[Dict[str, Any]]:
    """
    Retrieve chunks filtered by subtopic IDs with keyword-based ranking.
    This is the primary retrieval method when the Agent has selected relevant subtopics.
    
    Ranking strategy (simple but effective):
    1. Count keyword matches (more matches = higher priority)
    2. Prefer earlier chunks (chunk_index 0-2 often contain summaries/intros)
    3. Limit to k chunks maximum
    
    Args:
        query: Search query for keyword ranking
        subtopic_ids: List of subtopic IDs to retrieve chunks from
        k: Number of chunks to retrieve (default 12, max enforced)
        
    Returns:
        List of chunk dicts with metadata, ranked by relevance
    """
    engine = get_engine()
    if engine is None:
        return []

    if not subtopic_ids:
        return []

    # Enforce maximum chunk limit to prevent context overflow
    k = min(k, 15)

    params: Dict[str, Any] = {}

    # Build subtopic ID filter
    subtopic_placeholders = ','.join(
        [f':st_id_{i}' for i in range(len(subtopic_ids))])
    for i, st_id in enumerate(subtopic_ids):
        params[f"st_id_{i}"] = st_id

    # Extract keywords for ranking
    tokens = [t.strip().lower() for t in query.split() if len(t.strip()) >= 3]

    if tokens:
        # Build keyword match scoring - count how many keywords match
        # Each matching keyword adds 1 to the score
        keyword_scores = []
        for i, tok in enumerate(tokens[:8]):  # Use up to 8 keywords
            keyword_scores.append(
                f"CASE WHEN LOWER(c.chunk_text) LIKE :t{i} THEN 1 ELSE 0 END")
            params[f"t{i}"] = f"%{tok}%"

        # Sum all keyword matches for a relevance score
        keyword_score_sql = " + ".join(keyword_scores)

        # Retrieve chunks with ranking:
        # 1. keyword_score DESC (more keyword matches = better)
        # 2. chunk_index ASC (earlier chunks often more relevant - intros, summaries)
        sql = f"""
        SELECT
            c.chunk_text AS chunk_text,
            c.chunk_index AS chunk_index,
            c.subtopic_id AS subtopic_id,
            d.source_folder AS source_folder,
            d.file_name AS file_name,
            d.doc_key AS doc_key,
            st.label_en AS subtopic_label,
            ({keyword_score_sql}) AS keyword_score
        FROM rag_chunks c
        JOIN rag_documents d ON d.id = c.document_id
        LEFT JOIN subtopics st ON st.id = c.subtopic_id
        WHERE c.subtopic_id IN ({subtopic_placeholders})
        ORDER BY keyword_score DESC, c.chunk_index ASC
        LIMIT :k
        """
    else:
        # No keywords - prefer earlier chunks (often contain summaries)
        sql = f"""
        SELECT
            c.chunk_text AS chunk_text,
            c.chunk_index AS chunk_index,
            c.subtopic_id AS subtopic_id,
            d.source_folder AS source_folder,
            d.file_name AS file_name,
            d.doc_key AS doc_key,
            st.label_en AS subtopic_label
        FROM rag_chunks c
        JOIN rag_documents d ON d.id = c.document_id
        LEFT JOIN subtopics st ON st.id = c.subtopic_id
        WHERE c.subtopic_id IN ({subtopic_placeholders})
        ORDER BY c.chunk_index ASC
        LIMIT :k
        """

    params["k"] = k

    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()

    return [dict(r) for r in rows]
