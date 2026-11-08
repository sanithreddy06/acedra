import re
import math
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from io import BytesIO


class EmbeddingService:
    """
    High-performance semantic embedding and text extraction service.
    Produces 128-dimensional L2-normalized dense embeddings with deterministic
    semantic hashing and term-frequency weighting. Supports cosine similarity ranking.
    """

    DIMENSION = 128

    @staticmethod
    def extract_text(file_bytes: bytes, file_type: str, file_name: str) -> List[Dict[str, Any]]:
        """
        Extract text content with page/section metadata from PDF, DOCX, TXT, or MD files.
        Returns a list of pages/sections: [{"page_number": int, "text": str, "section": str}].
        """
        file_ext = file_type.lower().strip().replace(".", "")
        if not file_ext and "." in file_name:
            file_ext = file_name.rsplit(".", 1)[1].lower()

        extracted_sections: List[Dict[str, Any]] = []

        if file_ext == "pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(BytesIO(file_bytes))
                for page_idx, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    cleaned = page_text.strip()
                    if cleaned:
                        extracted_sections.append({
                            "page_number": page_idx + 1,
                            "section": f"Page {page_idx + 1}",
                            "text": cleaned,
                        })
            except Exception as e:
                # Fallback to UTF-8 text decoding if PDF parser fails
                text = file_bytes.decode("utf-8", errors="ignore").strip()
                extracted_sections.append({
                    "page_number": 1,
                    "section": "General",
                    "text": text,
                })

        elif file_ext in ["docx", "doc"]:
            try:
                import docx
                doc = docx.Document(BytesIO(file_bytes))
                current_section = "Introduction"
                current_paragraphs: List[str] = []
                page_est = 1

                for para in doc.paragraphs:
                    text = para.text.strip()
                    if not text:
                        continue
                    if para.style.name.startswith("Heading"):
                        if current_paragraphs:
                            extracted_sections.append({
                                "page_number": page_est,
                                "section": current_section,
                                "text": "\n".join(current_paragraphs),
                            })
                            current_paragraphs = []
                            page_est += 1
                        current_section = text
                    else:
                        current_paragraphs.append(text)

                if current_paragraphs:
                    extracted_sections.append({
                        "page_number": page_est,
                        "section": current_section,
                        "text": "\n".join(current_paragraphs),
                    })
            except Exception:
                text = file_bytes.decode("utf-8", errors="ignore").strip()
                extracted_sections.append({
                    "page_number": 1,
                    "section": "General",
                    "text": text,
                })

        else:
            # Markdown / Plain text
            text = file_bytes.decode("utf-8", errors="ignore").strip()
            # Split by markdown headers
            lines = text.split("\n")
            current_section = "General"
            current_chunk: List[str] = []
            page_est = 1

            for line in lines:
                if line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
                    if current_chunk:
                        extracted_sections.append({
                            "page_number": page_est,
                            "section": current_section,
                            "text": "\n".join(current_chunk),
                        })
                        current_chunk = []
                        page_est += 1
                    current_section = line.lstrip("#").strip()
                else:
                    current_chunk.append(line)

            if current_chunk:
                extracted_sections.append({
                    "page_number": page_est,
                    "section": current_section,
                    "text": "\n".join(current_chunk),
                })

        return extracted_sections

    @staticmethod
    def chunk_text(
        sections: List[Dict[str, Any]],
        target_chunk_size: int = 500,
        overlap: int = 80,
    ) -> List[Dict[str, Any]]:
        """
        Split extracted sections into overlapping chunks preserving section headers and page numbers.
        """
        chunks: List[Dict[str, Any]] = []
        chunk_idx = 0

        for sec in sections:
            text = sec["text"]
            section_name = sec.get("section", "Section")
            page_num = sec.get("page_number", 1)

            # Split text by paragraphs first
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

            current_buffer = ""
            for p in paragraphs:
                if len(current_buffer) + len(p) + 2 <= target_chunk_size:
                    current_buffer = f"{current_buffer}\n\n{p}".strip()
                else:
                    if current_buffer:
                        chunks.append({
                            "chunk_index": chunk_idx,
                            "content": current_buffer,
                            "section_heading": section_name,
                            "page_number": page_num,
                            "token_count": len(current_buffer.split()),
                        })
                        chunk_idx += 1
                        # Retain overlap from end of previous buffer
                        overlap_text = current_buffer[-overlap:] if len(current_buffer) > overlap else ""
                        current_buffer = f"{overlap_text}\n\n{p}".strip()
                    else:
                        current_buffer = p

            if current_buffer:
                chunks.append({
                    "chunk_index": chunk_idx,
                    "content": current_buffer,
                    "section_heading": section_name,
                    "page_number": page_num,
                    "token_count": len(current_buffer.split()),
                })
                chunk_idx += 1

        return chunks

    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        """
        Generate a normalized 128-dimensional dense semantic embedding vector.
        Uses positive token frequency hashing with sublinear term scaling
        and L2 Euclidean normalization.
        """
        vector = [0.0] * cls.DIMENSION
        if not text:
            return vector

        # Preprocess text
        tokens = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())
        if not tokens:
            return vector

        # Calculate token frequencies
        term_freqs: Dict[str, int] = {}
        for token in tokens:
            term_freqs[token] = term_freqs.get(token, 0) + 1

        # Also add bigrams for local phrase semantics
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]}_{tokens[i+1]}"
            term_freqs[bigram] = term_freqs.get(bigram, 0) + 1

        # Hash each term into vector dimensions with positive weights
        for term, freq in term_freqs.items():
            weight = 1.0 + math.log(freq)
            h = int(hashlib.md5(term.encode("utf-8")).hexdigest(), 16)
            idx = h % cls.DIMENSION
            vector[idx] += weight

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 1e-9:
            vector = [round(x / norm, 6) for x in vector]

        return vector

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two dense vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))

        if norm1 < 1e-9 or norm2 < 1e-9:
            return 0.0

        return max(0.0, min(1.0, dot_product / (norm1 * norm2)))

    @classmethod
    def rank_chunks(
        cls,
        query: str,
        chunks_with_embeddings: List[Dict[str, Any]],
        top_k: int = 4,
        min_threshold: float = 0.15,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rank a collection of chunks against a query embedding.
        Blends dense vector cosine similarity with lexical keyword overlap.
        Returns list of (chunk_dict, similarity_score) sorted descending.
        """
        query_vec = cls.generate_embedding(query)
        scored: List[Tuple[Dict[str, Any], float]] = []

        # Extract meaningful query keywords (length >= 3, excluding common stopwords)
        stopwords = {"what", "when", "where", "which", "who", "whom", "this", "that", "these", "those", "from", "with", "have", "been", "does", "about"}
        raw_terms = re.findall(r"\b[a-zA-Z0-9]{3,}\b", query.lower())
        query_terms = [t for t in raw_terms if t not in stopwords]

        for item in chunks_with_embeddings:
            emb = item.get("embedding_vector")
            if not emb:
                continue

            sim = cls.cosine_similarity(query_vec, emb)

            # Combined content and section heading text
            content_lower = (item.get("content", "") + " " + item.get("section_heading", "")).lower()
            matching_terms = sum(1 for t in query_terms if t in content_lower)

            if query_terms:
                lexical_ratio = matching_terms / len(query_terms)
                # Weighted blend: 60% vector similarity + 40% lexical keyword overlap
                blended_score = round(0.60 * sim + 0.40 * lexical_ratio, 4)
            else:
                blended_score = round(sim, 4)

            if blended_score >= min_threshold:
                scored.append((item, blended_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
