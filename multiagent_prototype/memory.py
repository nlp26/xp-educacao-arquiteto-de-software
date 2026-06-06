"""
Memória híbrida do sistema multiagente.

Duas camadas:
- Working memory: dict de sessão, descartado ao fim da execução
- Long-term memory: Chroma (vector store) para recuperação semântica

Referência: ADR #002.
"""
import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from observability import get_tracer


CHROMA_PERSIST_DIR = Path(__file__).parent / ".chroma"
COLLECTION_NAME = "multiagent_memory"


class WorkingMemory:
    """Memória de sessão."""

    def __init__(self):
        self.turns: list[dict[str, Any]] = []

    def append(self, role: str, content: str, metadata: dict | None = None):
        self.turns.append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
        })

    def recent(self, n: int = 5) -> list[dict[str, Any]]:
        return self.turns[-n:]

    def as_context(self, n: int = 3) -> str:
        """Renderiza turnos recentes como contexto."""
        if not self.turns:
            return ""
        recent_turns = self.turns[-n:]
        lines = []
        for t in recent_turns:
            lines.append(f"[{t['role']}] {t['content']}")
        return "\n".join(lines)


class LongTermMemory:
    """Memória persistente em Chroma."""

    def __init__(self):
        self._client: chromadb.PersistentClient | None = None
        self._collection = None

    def _ensure(self):
        if self._client is None:
            CHROMA_PERSIST_DIR.mkdir(exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(CHROMA_PERSIST_DIR),
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
            )

    def store(self, text: str, metadata: dict | None = None) -> str:
        tracer = get_tracer("memory")
        with tracer.start_as_current_span("memory.long_term.store") as span:
            self._ensure()
            doc_id = f"turn_{self._collection.count() + 1}"
            self._collection.add(
                documents=[text],
                metadatas=[metadata or {"source": "session"}],
                ids=[doc_id],
            )
            span.set_attribute("memory.doc_id", doc_id)
            span.set_attribute("memory.text_chars", len(text))
            return doc_id

    def search(self, query: str, k: int = 3) -> list[str]:
        tracer = get_tracer("memory")
        with tracer.start_as_current_span("memory.long_term.search") as span:
            self._ensure()
            span.set_attribute("memory.query", query[:100])
            span.set_attribute("memory.k", k)

            if self._collection.count() == 0:
                span.set_attribute("memory.results_count", 0)
                return []

            results = self._collection.query(query_texts=[query], n_results=k)
            docs = results.get("documents", [[]])[0]
            span.set_attribute("memory.results_count", len(docs))
            return docs


class HybridMemory:
    """Composição das duas camadas (ADR #002)."""

    def __init__(self):
        self.working = WorkingMemory()
        self.long_term = LongTermMemory()

    def record_turn(self, user_input: str, agent_output: str):
        self.working.append("user", user_input)
        self.working.append("assistant", agent_output)
        # Persiste o par pergunta-resposta no vector store
        self.long_term.store(
            text=f"P: {user_input}\nR: {agent_output}",
            metadata={"type": "qa_pair"},
        )

    def context_for(self, query: str) -> str:
        """Combina working memory e recuperação semântica."""
        working_ctx = self.working.as_context(n=3)
        retrieved = self.long_term.search(query, k=2)

        parts = []
        if working_ctx:
            parts.append(f"[Conversa atual]\n{working_ctx}")
        if retrieved:
            parts.append("[Turnos relevantes anteriores]\n" + "\n---\n".join(retrieved))
        return "\n\n".join(parts) if parts else "(sem contexto prévio)"
