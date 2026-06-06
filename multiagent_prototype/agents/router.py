"""
Agente Roteador.

Classifica a intenção da pergunta em uma das três rotas:
calculator, web_search ou knowledge.
"""
from observability import get_tracer
from llm import invoke_llm


VALID_ROUTES = {"calculator", "web_search", "knowledge"}


SYSTEM_PROMPT = """Você é um agente roteador. Sua única tarefa é classificar a pergunta do usuário em uma destas três categorias:

- calculator: pergunta envolve cálculo matemático (números, operações, conversões matemáticas)
- web_search: pergunta requer informação externa atualizada (notícias, fatos recentes, dados atuais)
- knowledge: pergunta pode ser respondida com conhecimento geral (definições, conceitos, explicações)

Responda APENAS com uma única palavra: calculator, web_search ou knowledge. Nada mais."""


def route(user_input: str, context: str = "") -> str:
    """Classifica a intenção. Retorna o nome da rota."""
    tracer = get_tracer("agent.router")
    with tracer.start_as_current_span("router.classify") as span:
        span.set_attribute("router.input", user_input[:200])

        prompt = f"Pergunta: {user_input}\n\nClassificação:"
        if context:
            prompt = f"Contexto recente:\n{context}\n\n{prompt}"

        raw = invoke_llm(prompt, system=SYSTEM_PROMPT).lower().strip()

        # Sanitização: o LLM às vezes retorna texto extra
        decision = "knowledge"  # default seguro
        for route_name in VALID_ROUTES:
            if route_name in raw:
                decision = route_name
                break

        span.set_attribute("router.raw_output", raw)
        span.set_attribute("router.decision", decision)
        return decision
