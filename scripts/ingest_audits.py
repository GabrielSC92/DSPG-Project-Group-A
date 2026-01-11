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

# Import your models (must exist in utils/database.py)
from utils.database import RagDocument, RagChunk  # noqa: F401


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
            f"Install one of: pymupdf OR pypdf. Original error: {e}"
        )


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


def upsert_document(session, doc_key: str, source_folder: str, file_name: str, file_path: str) -> int:
    """
    Create document row if missing, otherwise update basic metadata.
    Returns RagDocument.id
    """
    doc = session.query(RagDocument).filter(RagDocument.doc_key == doc_key).one_or_none()
    if doc is None:
        doc = RagDocument(
            doc_key=doc_key,
            source_folder=source_folder,
            file_name=file_name,
            file_path=file_path
        )
        session.add(doc)
        session.flush()  # get doc.id
    else:
        # keep it updated if file moved/renamed
        doc.source_folder = source_folder
        doc.file_name = file_name
        doc.file_path = file_path
        session.flush()

    return doc.id


def replace_chunks_for_document(session, document_id: int, chunks: list[str]) -> int:
    """
    Delete existing chunks for a doc and insert the new ones.
    Returns number of inserted chunks.
    """
    # delete existing
    session.query(RagChunk).filter(RagChunk.document_id == document_id).delete()

    # insert new
    for idx, ch in enumerate(chunks):
        session.add(RagChunk(
            document_id=document_id,
            chunk_index=idx,
            page_start=None,
            page_end=None,
            chunk_text=ch
        ))

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
    parser.add_argument("--root", type=str, default="data/raw", help="Root folder containing categorized PDF folders")
    parser.add_argument("--chunk-size", type=int, default=1500, help="Chunk size in characters")
    parser.add_argument("--overlap", type=int, default=250, help="Overlap in characters")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of PDFs processed (0 = no limit)")
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
        raise RuntimeError("Database session could not be created. Check DATABASE_URL / DB_PATH in .env")

    processed = 0
    total_chunks = 0
    failed = 0

    print(f"[*] Ingest starting: {len(pdfs)} PDF(s) from {root}")
    print(f"[*] Chunking: size={args.chunk_size}, overlap={args.overlap}")

    try:
        for pdf_path in pdfs:
            try:
                source_folder = get_source_folder(root, pdf_path)
                file_name = pdf_path.name
                file_path = str(pdf_path)

                # stable key so re-runs update same doc
                doc_key = f"{source_folder}/{file_name}"

                text, _ = extract_text_from_pdf(pdf_path)
                chunks = chunk_text(text, args.chunk_size, args.overlap)

                if not chunks:
                    print(f"[!] Skipping (no text): {doc_key}")
                    continue

                doc_id = upsert_document(session, doc_key, source_folder, file_name, file_path)
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
    print(f"Failed PDFs    : {failed}")
    print(f"Total chunks   : {total_chunks}")
    print("======================\n")


if __name__ == "__main__":
    main()
