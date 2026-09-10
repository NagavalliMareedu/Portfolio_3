import math
import re
from dataclasses import dataclass

from app.models import Citation


@dataclass(frozen=True)
class Document:
    source_id: str
    title: str
    text: str


DOCUMENTS = (
    Document(
        "POL-REFUND-001",
        "Customer refund policy",
        "Standard orders may be refunded within 30 days of delivery. Refunds above $500 "
        "require manager approval. Digital goods are reviewed case by case.",
    ),
    Document(
        "OPS-SHIP-002",
        "Shipping operations guide",
        "Standard shipping takes three to five business days. Expedited shipping takes one "
        "to two business days after fulfillment.",
    ),
    Document(
        "SEC-DATA-003",
        "Data handling standard",
        "Customer data must not be copied into unapproved tools. Access follows least privilege, "
        "and sensitive actions must be logged for audit review.",
    ),
)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class KnowledgeBase:
    """Small offline retriever; swap with a vector store in production."""

    def __init__(self, documents: tuple[Document, ...] = DOCUMENTS) -> None:
        self.documents = documents

    def search(self, query: str, limit: int = 3) -> list[Citation]:
        query_tokens = _tokens(query)
        ranked: list[tuple[float, Document]] = []
        for document in self.documents:
            document_tokens = _tokens(f"{document.title} {document.text}")
            overlap = len(query_tokens & document_tokens)
            score = overlap / math.sqrt(max(len(query_tokens) * len(document_tokens), 1))
            if score > 0:
                ranked.append((score, document))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [
            Citation(
                source_id=document.source_id,
                title=document.title,
                excerpt=document.text,
                score=round(score, 4),
            )
            for score, document in ranked[:limit]
        ]
