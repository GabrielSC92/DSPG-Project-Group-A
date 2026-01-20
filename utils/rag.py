from typing import List, Dict, Any
from sqlalchemy import text
from utils.database import get_engine

def retrieve_chunks(query: str, k: int = 6, source_folder: str | None = None) -> List[Dict[str, Any]]:

    """
    Retrieve top-k chunks from rag_chunks using naive keyword matching (LIKE).
    Returns dicts with chunk_text + metadata.
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

def format_sources_list(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return ""
    lines = []
    for i, ch in enumerate(chunks, start=1):
        lines.append(f"- [SOURCE {i}] {ch.get('source_folder','?')}/{ch.get('file_name','?')} (chunk {ch.get('chunk_index','?')})")
    return "\n".join(lines)
