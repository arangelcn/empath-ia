"""Semantic chunking utilities for the Knowledge Service."""

import hashlib
import re
from datetime import datetime
from typing import List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..models.knowledge import ChunkQuality, KnowledgeChunk, KnowledgeDocument


class SemanticChunkingService:
    """Create traceable, semantically bounded chunks from normalized text.

    The actual splitting is delegated to LangChain's
    `RecursiveCharacterTextSplitter`. This class adds Empat.IA-specific behavior:
    normalization, source metadata, stable hashes, and cohesion warnings.
    """

    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 160):
        """Configure LangChain's recursive splitter for knowledge documents."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n# ",
                "\n## ",
                "\n### ",
                "\n\n",
                "\n",
                ". ",
                "? ",
                "! ",
                "; ",
                ", ",
                " ",
                "",
            ],
            is_separator_regex=False,
        )

    def chunk_document(
        self,
        document: KnowledgeDocument,
        content: str,
        section: Optional[str] = None,
    ) -> List[KnowledgeChunk]:
        """Split document content and return traceable chunk objects."""
        normalized = self._normalize_text(content)
        parts = self._splitter.split_text(normalized)
        content_hash = self._hash_text(normalized)
        chunks: List[KnowledgeChunk] = []

        for index, part in enumerate(parts, start=1):
            chunk_hash = self._hash_text(part)
            inferred_section = section or self._infer_section(part)
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"{document.document_id}:v{document.document_version}:chunk_{index:05d}",
                    document_id=document.document_id,
                    document_version=document.document_version,
                    source=document.source,
                    source_uri=document.source_uri,
                    title=document.title,
                    section=inferred_section,
                    language=document.language,
                    content=part,
                    content_hash=content_hash,
                    chunk_hash=chunk_hash,
                    ingested_at=datetime.utcnow(),
                    quality=self.validate_cohesion(part),
                )
            )

        return chunks

    def validate_cohesion(self, text: str) -> ChunkQuality:
        """Score chunk cohesion with local heuristics before indexing."""
        warnings: List[str] = []
        stripped = text.strip()

        if len(stripped) < 120:
            warnings.append("chunk_is_short")

        if len(stripped) > self.chunk_size * 1.25:
            warnings.append("chunk_exceeds_target_size")

        if self._has_unbalanced_quotes(stripped):
            warnings.append("possible_cut_inside_quote")

        if not self._ends_on_boundary(stripped):
            warnings.append("chunk_may_end_mid_sentence")

        if self._starts_with_lowercase_continuation(stripped):
            warnings.append("chunk_may_start_mid_sentence")

        score = max(0.0, 1.0 - (0.18 * len(warnings)))
        return ChunkQuality(cohesion_score=round(score, 2), warnings=warnings)

    def _normalize_text(self, text: str) -> str:
        """Normalize whitespace while preserving paragraph boundaries."""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _infer_section(self, text: str) -> Optional[str]:
        """Infer a section label from markdown-style headings when present."""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
        return None

    def _hash_text(self, text: str) -> str:
        """Create a stable SHA-256 hash for audit and deduplication."""
        return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"

    def _has_unbalanced_quotes(self, text: str) -> bool:
        """Detect common quote-boundary problems with a simple local heuristic."""
        return text.count('"') % 2 == 1 or text.count("'") % 2 == 1

    def _ends_on_boundary(self, text: str) -> bool:
        """Return true when the chunk ends at a natural textual boundary."""
        return bool(re.search(r'[\.\?\!:"\')\]]$', text))

    def _starts_with_lowercase_continuation(self, text: str) -> bool:
        """Return true when the chunk likely starts in the middle of a sentence."""
        return bool(text) and text[0].islower()
