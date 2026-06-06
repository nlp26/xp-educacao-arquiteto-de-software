"""
Orquestrador baseado em LangGraph.

Define o grafo de estado que coordena os três agentes (Roteador, Executor,
Validador), a memoria hibrida e a observabilidade. Cada nó é uma função
sobre AgentState. Fluxo: START > router > executor > validator > END.
"""
from typing import TypedDict

from langgraph.graph import StateGraph, END, START

from observability import get_tracer, setup_observability
from memory import HybridMemory
from agents import router, executor, validator


# ── Estado compartilhado entre os nós do grafo ─────────────────────────────

class AgentState(TypedDict, total=False):
    user_input: str
    context: str
    route: str
    answer: str
    tool_used: str | None
    tool_result: str | None
    validation: dict
    final_answer: str


# ── Singleton da memória (vive durante toda a sessão) ──────────────────────

_memory: HybridMemory | None = None


def get_memory() -> HybridMemory:
    global _memory
    if _memory is None:
        _memory = HybridMemory()
    return _memory


# ── Nós do grafo ───────────────────────────────────────────────────────────

def node_router(state: AgentState) -> dict:
    tracer = get_tracer("orchestrator")
    with tracer.start_as_current_span("orchestrator.node.router") as span:
        memory = get_memory()
        context = memory.context_for(state["user_input"])
        decision = router.route(state["user_input"], context=context)
        span.set_attribute("orchestrator.route", decision)
        return {"context": context, "route": decision}


def node_executor(state: AgentState) -> dict:
    tracer = get_tracer("orchestrator")
    with tracer.start_as_current_span("orchestrator.node.executor") as span:
        result = executor.execute(
            user_input=state["user_input"],
            route=state["route"],
            context=state.get("context", ""),
        )
        span.set_attribute("orchestrator.tool_used", result.get("tool_used") or "none")
        return result


def node_validator(state: AgentState) -> dict:
    tracer = get_tracer("orchestrator")
    with tracer.start_as_current_span("orchestrator.node.validator") as span:
        verdict = validator.validate(
            user_input=state["user_input"],
            agent_output=state["answer"],
        )
        span.set_attribute("orchestrator.validation", verdict["valid"])

        # Quando invalida, mantem a resposta com nota do validador anexada.
        # Iteracao futura pode adicionar logica de reentrega ao executor.
        if verdict["valid"]:
            final = state["answer"]
        else:
            final = (
                f"{state['answer']}\n\n"
                f"[Nota do validador: {verdict['reason']}]"
            )

        # Persiste o turno na memória
        memory = get_memory()
        memory.record_turn(state["user_input"], final)

        return {"validation": verdict, "final_answer": final}


# ── Construção do grafo ────────────────────────────────────────────────────

def build_graph():
    """Constrói e compila o grafo de estado LangGraph."""
    setup_observability()

    graph = StateGraph(AgentState)
    graph.add_node("router", node_router)
    graph.add_node("executor", node_executor)
    graph.add_node("validator", node_validator)

    graph.add_edge(START, "router")
    graph.add_edge("router", "executor")
    graph.add_edge("executor", "validator")
    graph.add_edge("validator", END)

    return graph.compile()


# ── API de alto nível ──────────────────────────────────────────────────────

_compiled_graph = None


def run(user_input: str) -> dict:
    """Executa um turno completo. Retorna o estado final."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()

    tracer = get_tracer("orchestrator")
    with tracer.start_as_current_span("orchestrator.run") as span:
        span.set_attribute("session.user_input", user_input[:200])
        result = _compiled_graph.invoke({"user_input": user_input})
        span.set_attribute("session.tool_used", result.get("tool_used") or "none")
        span.set_attribute("session.validation_ok", result.get("validation", {}).get("valid", False))
        return result
