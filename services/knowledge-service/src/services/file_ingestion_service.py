"""File extraction and local storage helpers for Knowledge uploads."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

from pypdf import PdfReader

from ..models.knowledge import DocumentContentType


@dataclass
class ExtractedUpload:
    """Normalized upload payload ready for chunking and indexing."""

    content: str
    content_type: DocumentContentType
    original_filename: str
    stored_path: str
    stored_uri: str
    byte_size: int


class KnowledgeFileIngestionService:
    """Persist uploaded files locally and extract normalized text from them."""

    def __init__(self, storage_dir: Optional[str] = None):
        """Configure the base directory used for uploaded knowledge files."""
        self.storage_dir = Path(storage_dir or os.getenv("KNOWLEDGE_STORAGE_DIR", "/knowledge_data"))
        self.uploads_dir = self.storage_dir / "uploads"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def extract_upload(
        self,
        document_id: str,
        filename: str,
        content_type: Optional[str],
        file_bytes: bytes,
    ) -> ExtractedUpload:
        """Store one uploaded file and return the extracted normalized text."""
        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        detected_type = self._detect_content_type(filename=filename, content_type=content_type)
        stored_path = self._store_file(document_id=document_id, filename=filename, file_bytes=file_bytes)
        extracted_text = self._extract_text(detected_type=detected_type, file_bytes=file_bytes)

        if not extracted_text.strip():
            raise ValueError("The uploaded file did not produce readable text.")

        stored_uri = f"private://knowledge/uploads/{document_id}/{Path(stored_path).name}"
        return ExtractedUpload(
            content=extracted_text,
            content_type=detected_type,
            original_filename=filename,
            stored_path=str(stored_path),
            stored_uri=stored_uri,
            byte_size=len(file_bytes),
        )

    def _store_file(self, document_id: str, filename: str, file_bytes: bytes) -> Path:
        """Persist one uploaded file in the service storage directory."""
        document_dir = self.uploads_dir / document_id
        document_dir.mkdir(parents=True, exist_ok=True)

        safe_name = Path(filename or "uploaded_document").name.replace(" ", "_")
        stamped_name = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}_{safe_name}"
        stored_path = document_dir / stamped_name
        stored_path.write_bytes(file_bytes)
        return stored_path

    def _detect_content_type(self, filename: str, content_type: Optional[str]) -> DocumentContentType:
        """Infer the supported content type from MIME type or filename suffix."""
        suffix = Path(filename or "").suffix.lower()
        mime = (content_type or "").lower()

        if suffix == ".pdf" or mime == "application/pdf":
            return DocumentContentType.PDF
        if suffix in {".md", ".markdown"} or "markdown" in mime:
            return DocumentContentType.MARKDOWN
        if suffix in {".txt", ".text"} or mime.startswith("text/plain"):
            return DocumentContentType.TXT

        raise ValueError("Unsupported file type. Supported formats: pdf, txt, md.")

    def _extract_text(self, detected_type: DocumentContentType, file_bytes: bytes) -> str:
        """Extract readable text from one supported file type."""
        if detected_type == DocumentContentType.PDF:
            reader = PdfReader(BytesIO(file_bytes))
            return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()

        return file_bytes.decode("utf-8")
