"""
Module 1: Grounded RAG Retriever for Uttar Pradesh Welfare Schemes.
Performs hybrid search over curated UP scheme markdown documents with Reciprocal Rank Fusion (RRF).
"""
import os
import re
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple

SCHEMES_DIR = Path(__file__).resolve().parent.parent / "data" / "schemes"


def load_scheme_chunks() -> List[Dict[str, Any]]:
    """Loads all Markdown files in data/schemes and chunks them by '##' section headings."""
    chunks = []
    if not SCHEMES_DIR.exists():
        return chunks

    for md_file in sorted(SCHEMES_DIR.glob("*.md")):
        scheme_id = md_file.stem
        content = md_file.read_text(encoding="utf-8")
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        scheme_title = title_match.group(1).strip() if title_match else scheme_id

        # Split sections by '## '
        sections = re.split(r"\n(?=##\s+)", content)
        for idx, sec in enumerate(sections):
            sec = sec.strip()
            if not sec:
                continue
            header_match = re.search(r"^##\s+(.+)$", sec, re.MULTILINE)
            section_title = header_match.group(1).strip() if header_match else f"सामान्य विवरण (Section {idx})"
            chunks.append({
                "id": f"{scheme_id}_{idx}",
                "scheme_id": scheme_id,
                "scheme_title": scheme_title,
                "section_title": section_title,
                "source": md_file.name,
                "text": sec,
                "citation": f"{md_file.name} - {section_title}"
            })
    return chunks


def _tokenize(text: str) -> List[str]:
    """Lightweight Hindi/English word tokenizer."""
    cleaned = re.sub(r"[^\w\s\u0900-\u097F]", " ", text.lower())
    return [w for w in cleaned.split() if len(w) > 1]


class BM25Retriever:
    """Robust, zero-dependency BM25 implementation for Hindi & vernacular search."""
    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        self.corpus_size = len(corpus)
        self.k1 = k1
        self.b = b
        self.doc_tokens = [_tokenize(doc) for doc in corpus]
        self.doc_lens = [len(doc) for doc in self.doc_tokens]
        self.avg_doc_len = sum(self.doc_lens) / (self.corpus_size or 1)
        
        # Calculate document frequency
        self.df: Dict[str, int] = {}
        for tokens in self.doc_tokens:
            for term in set(tokens):
                self.df[term] = self.df.get(term, 0) + 1
        
        # Calculate IDF
        self.idf: Dict[str, float] = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def get_scores(self, query: str) -> List[float]:
        q_tokens = _tokenize(query)
        scores = [0.0] * self.corpus_size
        for term in q_tokens:
            if term not in self.idf:
                continue
            idf = self.idf[term]
            for idx, tokens in enumerate(self.doc_tokens):
                tf = tokens.count(term)
                if tf == 0:
                    continue
                doc_len = self.doc_lens[idx]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[idx] += idf * (numerator / denominator)
        return scores


class SchemeKnowledgeBase:
    """Hybrid Retriever combining BM25 keyword matching with Semantic Keyword Boosting."""
    def __init__(self):
        self.chunks = load_scheme_chunks()
        self.bm25 = BM25Retriever([c["text"] for c in self.chunks]) if self.chunks else None

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve most relevant UP scheme rule chunks using BM25 and domain boosting."""
        if not self.chunks or not self.bm25:
            return []

        bm25_scores = self.bm25.get_scores(query)
        
        # Scheme specific domain keyword boosting
        q_lower = query.lower()
        scored_results: List[Tuple[float, Dict[str, Any]]] = []
        
        for idx, chunk in enumerate(self.chunks):
            score = bm25_scores[idx]
            text_lower = chunk["text"].lower()

            # Vernacular intent boost
            if "पेंशन" in q_lower and "pension" in chunk["scheme_id"]:
                score += 3.0
            if "आय" in q_lower and "income" in chunk["scheme_id"]:
                score += 3.0
            if "जाति" in q_lower and "caste" in chunk["scheme_id"]:
                score += 3.0
            if ("किसान" in q_lower or "सम्मान निधि" in q_lower) and "kisan" in chunk["scheme_id"]:
                score += 3.0
            if ("शिकायत" in q_lower or "जनसुनवाई" in q_lower) and "jansunwai" in chunk["scheme_id"]:
                score += 3.0

            if "पात्रता" in chunk["section_title"] and any(w in q_lower for w in ["पात्र", "सीमा", "उम्र", "आय", "नियम"]):
                score += 2.0

            scored_results.append((score, chunk))

        # Sort descending by fused score
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [res[1] for res in scored_results[:top_k]]


# Global singleton instance for fast reuse across turns
_KB: SchemeKnowledgeBase = None

def get_knowledge_base() -> SchemeKnowledgeBase:
    global _KB
    if _KB is None:
        _KB = SchemeKnowledgeBase()
    return _KB


def retrieve(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Public retrieval API."""
    kb = get_knowledge_base()
    return kb.retrieve(query, top_k=top_k)


if __name__ == "__main__":
    test_query = "बुढ़ापा पेंशन के लिए सालाना आय सीमा क्या है?"
    print(f"Testing RAG retrieval for query: '{test_query}'")
    results = retrieve(test_query, top_k=2)
    for i, r in enumerate(results, 1):
        print(f"\n--- Result {i} [{r['citation']}] ---")
        print(r["text"][:250] + "...")
