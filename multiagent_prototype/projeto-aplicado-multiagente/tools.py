"""
Ferramentas externas acionadas pelo Agente Executor.

- Calculadora: avaliação segura via AST (sem eval())
- Busca web: DuckDuckGo (sem necessidade de API key)
"""
import ast
import operator as op
from typing import Any

from observability import get_tracer


# Calculadora segura via AST

_SAFE_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Constante não numérica: {node.value!r}")
    if isinstance(node, ast.BinOp):
        if type(node.op) not in _SAFE_OPS:
            raise ValueError(f"Operador não permitido: {type(node.op).__name__}")
        return _SAFE_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        if type(node.op) not in _SAFE_OPS:
            raise ValueError(f"Operador unário não permitido: {type(node.op).__name__}")
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.Call):
        # Suporta sqrt() via builtin
        if isinstance(node.func, ast.Name) and node.func.id == "sqrt":
            return _safe_eval(node.args[0]) ** 0.5
        raise ValueError(f"Função não permitida: {ast.dump(node.func)}")
    raise ValueError(f"Nó AST não suportado: {type(node).__name__}")


def calculator(expression: str) -> str:
    """Avalia uma expressão matemática de forma segura."""
    tracer = get_tracer("tools")
    with tracer.start_as_current_span("tool.calculator") as span:
        span.set_attribute("tool.input", expression)
        try:
            # Normaliza notação comum
            expr = expression.replace("^", "**").replace(",", ".")
            tree = ast.parse(expr, mode="eval")
            result = _safe_eval(tree.body)
            span.set_attribute("tool.output", str(result))
            span.set_attribute("tool.status", "success")
            return str(result)
        except Exception as e:
            span.set_attribute("tool.status", "error")
            span.set_attribute("tool.error", str(e))
            return f"Erro na avaliação: {e}"


# Busca web

def web_search(query: str, max_results: int = 3) -> str:
    """Busca na web e retorna snippets concatenados."""
    tracer = get_tracer("tools")
    with tracer.start_as_current_span("tool.web_search") as span:
        span.set_attribute("tool.input", query)
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if not results:
                span.set_attribute("tool.status", "empty")
                return "Nenhum resultado encontrado."
            snippets = []
            for r in results:
                title = r.get("title", "")
                body = r.get("body", "")
                snippets.append(f"- {title}: {body}")
            output = "\n".join(snippets)
            span.set_attribute("tool.status", "success")
            span.set_attribute("tool.results_count", len(results))
            return output
        except Exception as e:
            span.set_attribute("tool.status", "error")
            span.set_attribute("tool.error", str(e))
            return f"Erro na busca: {e}"


# Catalogo de ferramentas

TOOLS = {
    "calculator": calculator,
    "web_search": web_search,
}


def list_tools() -> list[dict[str, str]]:
    """Descreve as ferramentas disponíveis (para o Roteador decidir)."""
    return [
        {
            "name": "calculator",
            "description": "Avalia expressões matemáticas. Ex: '2+2', 'sqrt(144)+7', '15% de 200'.",
        },
        {
            "name": "web_search",
            "description": "Busca informações atuais na web. Use para fatos recentes, notícias, dados externos.",
        },
    ]
