from typing import List, Dict, Any
from sqlalchemy import text
from utils.database import get_engine

def retrieve_chunks(query: str, k: int = 6, source_folder: str | None = None, document_ids: List[int] | None = None) -> List[Dict[str, Any]]:

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


def retrieve_summaries(query: str, k: int = 5, source_folder: str | None = None) -> List[Dict[str, Any]]:
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
        conditions.append(f"(LOWER(d.summary) LIKE :t{i} OR LOWER(d.file_name) LIKE :t{i})")
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
        blocks.append(f"[DOC {i}] {src}\n{doc.get('summary', 'No summary available')}")
    return "\n\n".join(blocks)


def format_sources_list(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return ""
    lines = []
    for i, ch in enumerate(chunks, start=1):
        lines.append(f"- [SOURCE {i}] {ch.get('source_folder','?')}/{ch.get('file_name','?')} (chunk {ch.get('chunk_index','?')})")
    return "\n".join(lines)
