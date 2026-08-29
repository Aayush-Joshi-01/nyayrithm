from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.llm.base import LLMMessage, LLMProvider, LLMResponse
from app.models.agent import AgentDefinition
from app.rag.citation import parse_citations, build_citation_dict
from app.vector_db.base import SearchResult


@dataclass
class SpawnRequest:
    role: str
    name: str
    persona: dict[str, Any]
    reason: str
    llm_provider: str | None = None
    llm_model: str | None = None
    initial_instruction: str = ""


@dataclass
class TurnContext:
    simulation_id: UUID
    case_id: UUID
    turn_number: int
    mode: str
    recent_turns: list[dict[str, Any]]  # last N turns from all agents
    case_metadata: dict[str, Any]  # country, jurisdiction, etc.
    active_agent_ids: list[str]
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerceivedContext:
    query: str  # RAG retrieval query derived from context
    relevant_turns: list[dict[str, Any]]
    case_context: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    content: str
    citations: list[dict[str, Any]]
    token_count: int
    latency_ms: int
    reasoning_trace: dict[str, Any] = field(default_factory=dict)


@dataclass
class TurnResult:
    response: AgentResponse
    spawns: list[SpawnRequest]


class BaseAgent(ABC):
    """
    Abstract base for all Nyayrithm agents.
    Subclasses define role-specific system_prompt_template and override
    perceive/maybe_spawn for role-specific behavior.
    """

    def __init__(
        self,
        definition: AgentDefinition,
        llm: LLMProvider,
        memory,  # AgentMemory protocol — imported at runtime to avoid cycles
    ) -> None:
        self.definition = definition
        self.llm = llm
        self.memory = memory

    @property
    def role(self) -> str:
        return self.definition.role

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    @abstractmethod
    def system_prompt_template(self) -> str:
        """
        Jinja2-style template filled with case + persona context.
        Subclasses must implement this.
        """
        ...

    def build_system_prompt(self, case_meta: dict[str, Any]) -> str:
        country = case_meta.get("country", "Unknown")
        jurisdiction = case_meta.get("jurisdiction", "Unknown")
        legal_system = case_meta.get("legal_system", "common_law")
        case_title = case_meta.get("title", "Untitled Case")
        prior_statements = self.memory.prior_statements_summary()

        return self.system_prompt_template.format(
            name=self.name,
            country=country,
            jurisdiction=jurisdiction,
            legal_system=legal_system,
            case_title=case_title,
            prior_statements=prior_statements or "(No prior statements in this session)",
            persona=self.definition.persona,
            knowledge_scope=self.definition.knowledge_scope,
        )

    async def perceive(self, context: TurnContext) -> PerceivedContext:
        """Filter context to what this agent is allowed to know and derive a RAG query."""
        relevant_turns = context.recent_turns[-10:]  # last 10 turns

        # Build a retrieval query from the most recent conversation
        recent_text = " ".join(t.get("content", "")[:200] for t in relevant_turns[-3:])
        query = f"{self.role} perspective: {recent_text}" if recent_text else self.role

        case_context = (
            f"Case: {context.case_metadata.get('title', 'Unknown')} | "
            f"Country: {context.case_metadata.get('country', 'Unknown')} | "
            f"Jurisdiction: {context.case_metadata.get('jurisdiction', 'Unknown')} | "
            f"Mode: {context.mode} | Turn: {context.turn_number}"
        )

        return PerceivedContext(
            query=query,
            relevant_turns=relevant_turns,
            case_context=case_context,
            extra={"case_metadata": context.case_metadata},
        )

    async def retrieve(
        self,
        query: str,
        case_id: UUID,
        vector_store,
    ) -> list[SearchResult]:
        from app.rag.retriever import EvidenceRetriever
        retriever = EvidenceRetriever(vector_store)
        return await retriever.retrieve_for_agent(
            role=self.role,
            query=query,
            case_id=case_id,
            top_k=5,
        )

    def _build_rag_context(self, results: list[SearchResult]) -> str:
        if not results:
            return ""
        parts = []
        for r in results:
            ev_id = r.chunk.metadata.get("evidence_id", "unknown")
            idx = r.chunk.metadata.get("chunk_index", 0)
            parts.append(f"[EVIDENCE:{ev_id}:{idx}] {r.chunk.text[:600]}")
        return "\n\n".join(parts)

    async def respond(
        self,
        perceived: PerceivedContext,
        retrieved: list[SearchResult],
        stream_callback=None,  # optional async callable(token: str)
    ) -> AgentResponse:
        case_meta = dict(perceived.extra.get("case_metadata") or {})
        case_meta.setdefault("title", "Untitled Case")
        system_prompt = self.build_system_prompt(case_meta)

        history = self.memory.as_messages()
        rag_context = self._build_rag_context(retrieved)

        user_content = (
            f"Context: {perceived.case_context}\n\n"
            + (f"Relevant Evidence:\n{rag_context}\n\n" if rag_context else "")
            + "Recent proceedings:\n"
            + "\n".join(
                f"{t.get('agent_name', 'Unknown')} ({t.get('role', '?')}): {t.get('content', '')[:400]}"
                for t in perceived.relevant_turns
            )
            + f"\n\nNow it is your turn as {self.name} ({self.role}). "
              "Stay fully in character. Reference evidence using [EVIDENCE:uuid:index] markers. "
              "You may express uncertainty, hesitation, or challenge prior statements. "
              "Respond naturally as a real person in this role would."
        )

        messages = [
            LLMMessage(role="system", content=system_prompt),
            *history,
            LLMMessage(role="user", content=user_content),
        ]

        start = time.perf_counter()
        if stream_callback:
            full_content = ""
            async for token in self.llm.stream(messages):
                full_content += token
                await stream_callback(token)
            response_content = full_content
            token_count = len(response_content.split())
        else:
            llm_response: LLMResponse = await self.llm.complete(messages)
            response_content = llm_response.content
            token_count = llm_response.output_tokens

        elapsed = int((time.perf_counter() - start) * 1000)

        # Parse citations
        parsed = parse_citations(response_content)
        citations = []
        for p in parsed:
            matching = next(
                (r for r in retrieved if r.chunk.metadata.get("evidence_id") == p.evidence_id),
                None,
            )
            if matching:
                citations.append(build_citation_dict(
                    citation=p,
                    chunk_text=matching.chunk.text,
                    evidence_title=matching.chunk.metadata.get("title", p.evidence_id),
                    score=matching.score,
                    modality=matching.chunk.modality,
                ))

        return AgentResponse(
            content=response_content,
            citations=citations,
            token_count=token_count,
            latency_ms=elapsed,
        )

    async def maybe_spawn(self, response: AgentResponse) -> list[SpawnRequest]:
        """
        Override in subclasses to produce spawn requests based on the response.
        Default: no spawning.
        """
        return []

    async def run_turn(
        self,
        context: TurnContext,
        vector_store=None,
        stream_callback=None,
    ) -> TurnResult:
        perceived = await self.perceive(context)
        retrieved = await self.retrieve(perceived.query, context.case_id, vector_store) if vector_store else []
        response = await self.respond(perceived, retrieved, stream_callback=stream_callback)
        spawns = await self.maybe_spawn(response)
        self.memory.record(perceived, response)
        return TurnResult(response=response, spawns=spawns)
