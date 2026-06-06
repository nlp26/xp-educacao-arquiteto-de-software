"""
CLI principal do protótipo.

Dois modos:
    python main.py "pergunta"   # turno único
    python main.py              # interativo
"""
import sys

from orchestrator import run


BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║   Protótipo: Arquitetura de Referência Multiagente              ║
║   Projeto Aplicado XPE - Sprint 3                                ║
║                                                                  ║
║   Modelo: Qwen2.5:7b (Ollama, local)                            ║
║   Framework: LangGraph + Chroma + OpenTelemetry                 ║
╚══════════════════════════════════════════════════════════════════╝
"""


def render_result(result: dict) -> str:
    lines = [
        "",
        "─" * 70,
        f"Rota escolhida.......: {result.get('route', 'N/A')}",
        f"Ferramenta usada.....: {result.get('tool_used') or 'nenhuma'}",
        f"Validação............: {'OK' if result.get('validation', {}).get('valid') else 'FAIL'}",
        "─" * 70,
        "Resposta:",
        "",
        result.get("final_answer", "(sem resposta)"),
        "─" * 70,
    ]
    return "\n".join(lines)


def run_once(question: str):
    result = run(question)
    print(render_result(result))


def run_interactive():
    print(BANNER)
    print("Digite suas perguntas. 'sair' para encerrar.\n")
    while True:
        try:
            question = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            break
        if not question:
            continue
        if question.lower() in {"sair", "exit", "quit"}:
            print("Encerrando.")
            break
        result = run(question)
        print(render_result(result))
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_once(" ".join(sys.argv[1:]))
    else:
        run_interactive()
