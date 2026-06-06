"""
Agente Validador.

Verifica a saída do Executor antes do retorno ao usuário. Aplica três
checagens: não-vazio, ausência de marcadores de falha e coerência
semântica via LLM.
"""
from observability import get_tracer
from llm import invoke_llm


VALIDATION_PROMPT = """Avalie se a RESPOSTA abaixo endereça a PERGUNTA de forma minimamente coerente.

Responda APENAS com:
- OK: se a resposta tenta responder à pergunta de maneira relevante
- FAIL: se a resposta é claramente desconexa, vazia ou irrelevante

PERGUNTA: {question}
RESPOSTA: {answer}

Veredicto:"""


FAILURE_MARKERS = [
    "não consegui",
    "i don't know",
    "erro:",
    "erro na",
    "erro interno",
]


def validate(user_input: str, agent_output: str) -> dict:
    """Retorna {'valid': bool, 'reason': str}."""
    tracer = get_tracer("agent.validator")
    with tracer.start_as_current_span("validator.check") as span:
        span.set_attribute("validator.input_question", user_input[:200])
        span.set_attribute("validator.output_chars", len(agent_output))

        # Não-vazio
        if not agent_output or len(agent_output.strip()) < 5:
            span.set_attribute("validator.result", "fail.empty")
            return {"valid": False, "reason": "Resposta vazia ou muito curta."}

        # Marcadores de falha
        low = agent_output.lower()
        for marker in FAILURE_MARKERS:
            if marker in low:
                span.set_attribute("validator.result", "fail.error_marker")
                span.set_attribute("validator.failure_marker", marker)
                return {"valid": False, "reason": f"Resposta contém marcador de falha: '{marker}'."}

        # Coerência via LLM
        verdict = invoke_llm(
            VALIDATION_PROMPT.format(question=user_input, answer=agent_output)
        ).strip().upper()

        span.set_attribute("validator.llm_verdict", verdict[:50])

        if "OK" in verdict.split():
            span.set_attribute("validator.result", "ok")
            return {"valid": True, "reason": "Resposta coerente com a pergunta."}

        span.set_attribute("validator.result", "fail.incoherent")
        return {"valid": False, "reason": "Resposta avaliada como incoerente."}
