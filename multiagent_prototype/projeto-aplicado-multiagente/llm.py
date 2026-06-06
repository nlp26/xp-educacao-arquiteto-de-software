"""
Wrapper sobre Ollama com Qwen2.5:7b.

Centraliza a configuração do modelo e instrumenta as chamadas com spans.
Singleton para evitar reconexões repetidas.
"""
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from observability import get_tracer


MODEL_NAME = "qwen2.5:7b"
TEMPERATURE = 0.1  # baixa, para respostas determinísticas em tarefas analíticas

_llm: ChatOllama | None = None


def get_llm() -> ChatOllama:
    """Singleton para evitar reconexões repetidas com o Ollama."""
    global _llm
    if _llm is None:
        _llm = ChatOllama(model=MODEL_NAME, temperature=TEMPERATURE)
    return _llm


def invoke_llm(prompt: str, system: str | None = None) -> str:
    """
    Invoca o LLM com instrumentação. Cada chamada vira um span filho
    do agente que a originou, conforme ADR #003.
    """
    tracer = get_tracer("llm")
    with tracer.start_as_current_span("llm.invoke") as span:
        span.set_attribute("llm.model", MODEL_NAME)
        span.set_attribute("llm.temperature", TEMPERATURE)
        span.set_attribute("llm.prompt_chars", len(prompt))

        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        response = get_llm().invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)

        span.set_attribute("llm.response_chars", len(content))
        return content.strip()
