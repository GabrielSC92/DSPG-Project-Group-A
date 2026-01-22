#!/usr/bin/env python3
"""
Ingest PDF audits/reports into the database as RAG documents + chunks.

Folder structure (recommended):
data/raw/<category>/<pdf files>.pdf

Example:
data/raw/defensie/report1.pdf  -> source_folder = "defensie"
data/raw/financien/report2.pdf -> source_folder = "financien"

Usage:
  python scripts/ingest_audits.py
  python scripts/ingest_audits.py --root data/raw --chunk-size 1500 --overlap 250
"""

import argparse
import os
from pathlib import Path
from datetime import datetime

# Make sure imports from project root work
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.database import get_session  # uses DATABASE_URL / DB_PATH from .env
from utils.llm import summarize_text, generate_topic_label, generate_subtopics_batch  # Import LLM functions

# Import your models and functions (must exist in utils/database.py)
from utils.database import (RagDocument, RagChunk, Topic, SubTopic,
                            upsert_topic, update_topic_counts,
                            get_or_create_subtopic, get_topic_id_by_folder,
                            update_subtopic_counts)  # noqa: F401


def extract_text_from_pdf(pdf_path: Path) -> tuple[str, list[tuple[int, int]]]:
    """
    Extract text from a PDF.
    Returns:
      (full_text, page_spans)
    page_spans: list of (page_start, page_end) per chunk if you later want it;
                for now we return empty spans and fill None.
    """
    # Try PyMuPDF first (usually best extraction)
    try:
        import fitz  # pymupdf
        doc = fitz.open(str(pdf_path))
        pages = []
        for i in range(len(doc)):
            page_text = doc.load_page(i).get_text("text") or ""
            pages.append(page_text)
        doc.close()
        full_text = "\n".join(pages)
        return full_text, []
    except Exception:
        pass

    # Fallback: pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        pages = []
        for p in reader.pages:
            pages.append(p.extract_text() or "")
        full_text = "\n".join(pages)
        return full_text, []
    except Exception as e:
        raise RuntimeError(
            f"Could not extract text from PDF {pdf_path.name}. "
            f"Install one of: pymupdf OR pypdf. Original error: {e}")


def normalize_whitespace(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split())


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Simple character-based chunking with overlap.
    Works well as a first iteration.
    """
    text = normalize_whitespace(text)
    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(0, end - overlap)

    return chunks


def upsert_document(session,
                    doc_key: str,
                    source_folder: str,
                    file_name: str,
                    file_path: str,
                    summary: str | None = None) -> int:
    """
    Create document row if missing, otherwise update basic metadata and summary.
    Returns RagDocument.id
    """
    doc = session.query(RagDocument).filter(
        RagDocument.doc_key == doc_key).one_or_none()
    if doc is None:
        doc = RagDocument(doc_key=doc_key,
                          source_folder=source_folder,
                          file_name=file_name,
                          file_path=file_path,
                          summary=summary)
        session.add(doc)
        session.flush()  # get doc.id
    else:
        # keep it updated if file moved/renamed or summary changed
        doc.source_folder = source_folder
        doc.file_name = file_name
        doc.file_path = file_path
        if summary:
            doc.summary = summary
        session.flush()

    return doc.id


def replace_chunks_for_document(session,
                                document_id: int,
                                chunks: list[str],
                                subtopic_ids: list[int] = None) -> int:
    """
    Delete existing chunks for a doc and insert the new ones.
    Optionally links chunks to subtopics.
    
    Args:
        session: Database session
        document_id: Document ID
        chunks: List of chunk texts
        subtopic_ids: Optional list of subtopic IDs (same length as chunks)
        
    Returns:
        Number of inserted chunks.
    """
    # delete existing
    session.query(RagChunk).filter(
        RagChunk.document_id == document_id).delete()

    # insert new
    for idx, ch in enumerate(chunks):
        subtopic_id = subtopic_ids[idx] if subtopic_ids and idx < len(
            subtopic_ids) else None
        session.add(
            RagChunk(document_id=document_id,
                     chunk_index=idx,
                     subtopic_id=subtopic_id,
                     page_start=None,
                     page_end=None,
                     chunk_text=ch))

    return len(chunks)


def get_source_folder(root: Path, pdf_path: Path) -> str:
    """
    Determine source_folder from folder structure.
    If pdf is in data/raw/<folder>/<file>.pdf => source_folder=<folder>
    If deeper, we take the first folder under root.
    """
    rel = pdf_path.relative_to(root)
    parts = rel.parts
    if len(parts) >= 2:
        return parts[0]
    return root.name  # fallback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root",
                        type=str,
                        default="data/raw",
                        help="Root folder containing categorized PDF folders")
    parser.add_argument("--chunk-size",
                        type=int,
                        default=1500,
                        help="Chunk size in characters")
    parser.add_argument("--overlap",
                        type=int,
                        default=250,
                        help="Overlap in characters")
    parser.add_argument("--limit",
                        type=int,
                        default=0,
                        help="Limit number of PDFs processed (0 = no limit)")
    parser.add_argument(
        "--force",
        action="store_true",
        help=
        "Force re-processing of existing documents (default: skip existing)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Root folder not found: {root}")

    pdfs = sorted(root.rglob("*.pdf"))
    if args.limit and args.limit > 0:
        pdfs = pdfs[:args.limit]

    if not pdfs:
        print(f"[!] No PDFs found under: {root}")
        return

    session = get_session()
    if session is None:
        raise RuntimeError(
            "Database session could not be created. Check DATABASE_URL / DB_PATH in .env"
        )

    processed = 0
    total_chunks = 0
    failed = 0
    skipped = 0

    print(f"[*] Ingest starting: {len(pdfs)} PDF(s) from {root}")
    print(f"[*] Chunking: size={args.chunk_size}, overlap={args.overlap}")
    print(f"[*] Skip existing: {not args.force} (use --force to re-process)")
    print(f"[*] Summaries will be generated during ingestion\n")

    try:
        for pdf_path in pdfs:
            try:
                source_folder = get_source_folder(root, pdf_path)
                file_name = pdf_path.name
                file_path = str(pdf_path)

                # stable key so re-runs update same doc
                doc_key = f"{source_folder}/{file_name}"

                # Skip if document already exists (unless --force is used)
                if not args.force:
                    existing = session.query(RagDocument).filter(
                        RagDocument.doc_key == doc_key).first()
                    if existing:
                        print(f"[SKIP] Already exists: {doc_key}")
                        skipped += 1
                        continue

                text, _ = extract_text_from_pdf(pdf_path)
                chunks = chunk_text(text, args.chunk_size, args.overlap)

                if not chunks:
                    print(f"[!] Skipping (no text): {doc_key}")
                    continue

                # Generate summary from full text
                print(f"[*] Summarizing {file_name}...", end=" ", flush=True)
                summary_ok, summary = summarize_text(text)
                if summary_ok:
                    print("✓")
                else:
                    print(f"✗ ({summary})")
                    summary = None

                doc_id = upsert_document(session,
                                         doc_key,
                                         source_folder,
                                         file_name,
                                         file_path,
                                         summary=summary)
                inserted = replace_chunks_for_document(session, doc_id, chunks)

                session.commit()

                processed += 1
                total_chunks += inserted
                print(f"[OK] {doc_key} -> {inserted} chunks")

            except Exception as e:
                session.rollback()
                failed += 1
                print(f"[X] Failed {pdf_path.name}: {e}")

    finally:
        session.close()

    print("\n=== Ingest summary ===")
    print(f"Processed PDFs : {processed}")
    print(f"Skipped PDFs   : {skipped}")
    print(f"Failed PDFs    : {failed}")
    print(f"Total chunks   : {total_chunks}")
    print("======================\n")

    # Generate topics after ingestion (creates its own session)
    print("[*] Generating topics from ingested documents...")
    generate_topics_from_documents(root)


def generate_topics_from_documents(root: Path, session=None) -> None:
    """
    Generate English topic labels for each unique source folder based on sample chunks.
    
    This function:
    1. Finds unique source folders from ingested documents
    2. Samples chunks from each folder
    3. Uses LLM to generate an English topic label
    4. Stores topics in the database
    """
    if session is None:
        session = get_session()
        if session is None:
            print("[X] Could not create database session for topic generation")
            return

    try:
        # Get unique source folders with their document counts
        from sqlalchemy import func
        folder_counts = session.query(
            RagDocument.source_folder,
            func.count(RagDocument.id).label('count')).group_by(
                RagDocument.source_folder).all()

        if not folder_counts:
            print("[!] No documents found for topic generation")
            return

        print(f"[*] Found {len(folder_counts)} unique source folder(s)")

        topic_labels = {
        }  # Store folder -> label mapping for subtopic generation

        for source_folder, doc_count in folder_counts:
            # Get sample chunks from this folder for context
            sample_chunks = session.query(RagChunk.chunk_text).join(
                RagDocument, RagChunk.document_id == RagDocument.id).filter(
                    RagDocument.source_folder == source_folder).limit(3).all()

            # Combine sample chunks for context
            sample_text = " ".join([c[0][:500] for c in sample_chunks
                                    ]) if sample_chunks else ""

            # Generate English topic label using LLM
            print(f"[*] Generating topic label for '{source_folder}'...",
                  end=" ",
                  flush=True)
            success, label = generate_topic_label(source_folder, sample_text)

            if success:
                print(f"✓ -> '{label}'")
                # Store topic in database
                save_ok, msg = upsert_topic(source_folder, label, doc_count)
                if not save_ok:
                    print(f"    [!] Failed to save topic: {msg}")
                topic_labels[source_folder] = label
            else:
                # Fallback: capitalize the folder name
                fallback_label = source_folder.replace("_", " ").replace(
                    "-", " ").title()
                print(f"✗ (using fallback: '{fallback_label}')")
                upsert_topic(source_folder, fallback_label, doc_count)
                topic_labels[source_folder] = fallback_label

        # Update document counts for all topics
        update_topic_counts()
        print(f"[OK] Topics generated and saved to database")

        # Close this session before generating subtopics
        session.close()

        # Now generate subtopics for all chunks
        print("\n[*] Generating sub-topics for chunks...")
        generate_subtopics_for_chunks(topic_labels)

    except Exception as e:
        print(f"[X] Error generating topics: {e}")
        if session:
            session.close()


def generate_subtopics_for_chunks(topic_labels: dict) -> None:
    """
    Generate sub-topic labels at the DOCUMENT level (not per-chunk).
    Each document gets one subtopic derived from its summary.
    All chunks from that document share the same subtopic.
    
    This is much faster and creates meaningful groupings:
    - ~24 documents = ~24 subtopics (instead of ~1700 per-chunk subtopics)
    - Agent reads ~24 labels instead of 1000+
    
    Args:
        topic_labels: Dict mapping source_folder -> English topic label
    """
    from utils.llm import generate_subtopic_from_summary

    session = get_session()
    if session is None:
        print("[X] Could not create database session for subtopic generation")
        return

    try:
        # Process each topic
        for source_folder, topic_label in topic_labels.items():
            # Get topic ID
            topic = session.query(Topic).filter(
                Topic.source_folder == source_folder.lower()).one_or_none()

            if not topic:
                print(f"[!] Topic not found for folder: {source_folder}")
                continue

            topic_id = topic.id

            # Get all documents for this topic
            documents = session.query(RagDocument).filter(
                RagDocument.source_folder == source_folder).all()

            if not documents:
                print(f"[*] No documents for '{topic_label}'")
                continue

            print(
                f"[*] Checking sub-topics for {len(documents)} documents in '{topic_label}'..."
            )

            processed = 0
            skipped = 0
            for doc_num, doc in enumerate(documents, 1):
                # Check if this document's chunks already have subtopics assigned
                existing_subtopic = session.query(RagChunk.subtopic_id).filter(
                    RagChunk.document_id == doc.id,
                    RagChunk.subtopic_id.isnot(None)).first()

                if existing_subtopic:
                    skipped += 1
                    continue  # Skip - document already has subtopics assigned

                print(f"    [{doc_num}/{len(documents)}] {doc.file_name}...",
                      end=" ",
                      flush=True)

                # Generate subtopic from document summary (or filename if no summary)
                if doc.summary:
                    success, subtopic_label = generate_subtopic_from_summary(
                        doc.summary, topic_label)
                else:
                    # Fallback: use cleaned filename
                    subtopic_label = doc.file_name.replace('+', ' ').replace(
                        '.pdf', '').replace('_', ' ')
                    subtopic_label = subtopic_label[:80].title()
                    success = True

                if not success:
                    subtopic_label = f"{topic_label} - {doc.file_name[:30]}"

                print(f"-> '{subtopic_label}'")

                # Create/get subtopic
                subtopic_id = get_or_create_subtopic(session, topic_id,
                                                     subtopic_label)

                # Update ALL chunks from this document to use this subtopic
                session.query(RagChunk).filter(
                    RagChunk.document_id == doc.id).update(
                        {RagChunk.subtopic_id: subtopic_id})

                session.commit()
                processed += 1

            if skipped > 0:
                print(
                    f"    ✓ {topic_label}: {processed} new, {skipped} skipped (already tagged)"
                )
            else:
                print(f"    ✓ {topic_label}: {processed} documents tagged")

        # Update subtopic counts
        update_subtopic_counts()
        print("[OK] Sub-topics generated and linked to chunks")

    except Exception as e:
        session.rollback()
        print(f"[X] Error generating subtopics: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    main()
