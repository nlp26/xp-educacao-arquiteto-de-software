"""
Agente Executor.

Executa a tarefa após a decisão do Roteador. Para rotas com ferramentas
(calculator, web_search), extrai argumentos, invoca a ferramenta e formula
a resposta final. Para a rota knowledge, consulta o LLM diretamente.
"""
from observability import get_tracer
from llm import invoke_llm
from tools import calculator, web_search


EXTRACT_CALC_PROMPT = """Extraia APENAS a expressão matemática contida na pergunta abaixo. Retorne só a expressão pura, pronta para ser avaliada. Use sqrt() para raiz quadrada, ** para potência.

Pergunta: {question}

Expressão:"""


EXTRACT_QUERY_PROMPT = """Extraia uma consulta de busca concisa (3-7 palavras) a partir da pergunta abaixo. Retorne só a consulta, sem aspas.

Pergunta: {question}

Consulta:"""


ANSWER_WITH_TOOL_PROMPT = """Use o resultado da ferramenta abaixo para responder à pergunta do usuário de forma clara e direta, em português.

Pergunta original: {question}
Resultado da ferramenta ({tool}): {result}

Resposta:"""


KNOWLEDGE_PROMPT = """Responda à pergunta do usuário de forma clara, direta e factual em português. Se não tiver certeza, diga isso explicitamente.

{context}

Pergunta: {question}

Resposta:"""


def execute(user_input: str, route: str, context: str = "") -> dict:
    """
    Executa a tarefa conforme a rota decidida.
    Retorna: {'answer': str, 'tool_used': str | None, 'tool_result': str | None}
    """
    tracer = get_tracer("agent.executor")
    with tracer.start_as_current_span("executor.run") as span:
        span.set_attribute("executor.route", route)
        span.set_attribute("executor.input", user_input[:200])

        if route == "calculator":
            return _execute_calculator(user_input, span)
        if route == "web_search":
            return _execute_web_search(user_input, span)
        return _execute_knowledge(user_input, context, span)


def _execute_calculator(user_input: str, span) -> dict:
    expr = invoke_llm(EXTRACT_CALC_PROMPT.format(question=user_input))
    expr = expr.strip().strip("`").strip()
    span.set_attribute("executor.extracted_expr", expr)

    result = calculator(expr)
    answer = invoke_llm(ANSWER_WITH_TOOL_PROMPT.format(
        question=user_input, tool="calculator", result=result,
    ))
    span.set_attribute("executor.tool_used", "calculator")
    return {"answer": answer, "tool_used": "calculator", "tool_result": result}


def _execute_web_search(user_input: str, span) -> dict:
    query = invoke_llm(EXTRACT_QUERY_PROMPT.format(question=user_input))
    query = query.strip().strip('"').strip("'")
    span.set_attribute("executor.search_query", query)

    result = web_search(query)
    answer = invoke_llm(ANSWER_WITH_TOOL_PROMPT.format(
        question=user_input, tool="web_search", result=result,
    ))
    span.set_attribute("executor.tool_used", "web_search")
    return {"answer": answer, "tool_used": "web_search", "tool_result": result[:500]}


def _execute_knowledge(user_input: str, context: str, span) -> dict:
    ctx_block = f"Contexto:\n{context}\n" if context else ""
    answer = invoke_llm(KNOWLEDGE_PROMPT.format(context=ctx_block, question=user_input))
    span.set_attribute("executor.tool_used", "none")
    return {"answer": answer, "tool_used": None, "tool_result": None}
