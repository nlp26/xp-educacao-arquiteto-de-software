# Protótipo Funcional - Arquitetura de Referência Multiagente com IA Generativa

Implementação executável da arquitetura de referência descrita no Documento de Arquitetura de Software (DAS) do Projeto Aplicado. Este protótipo valida concretamente os componentes, fluxos e decisões formalizadas nos ADRs #001, #002 e #003.

## Componentes implementados (correspondência com a Figura 6 do DAS)

| Componente | Implementação | Arquivo |
|---|---|---|
| Orquestrador | Grafo de estado LangGraph | `orchestrator.py` |
| Agente Roteador | Classificador de intenção | `agents/router.py` |
| Agente Executor | Executor de tarefa + ferramentas | `agents/executor.py` |
| Agente Validador | Verificador de saída | `agents/validator.py` |
| LLM | Qwen2.5:7b via Ollama (local) | `llm.py` |
| Memória híbrida | Working memory + Chroma (vector store) | `memory.py` |
| Ferramentas externas | Calculadora + busca web (DuckDuckGo) | `tools.py` |
| Observabilidade | OpenTelemetry (traces + logs) | `observability.py` |

## Pré-requisitos (Mac Mini M1)

```bash
# 1. Instalar Ollama
brew install ollama
ollama serve  # rodar em terminal separado

# 2. Baixar o modelo (uma vez)
ollama pull qwen2.5:7b

# 3. Python 3.11+ (deve estar instalado)
python3 --version
```

## Instalação

```bash
cd multiagent_prototype
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Execução

### Modo 1: Pergunta única
```bash
python main.py "Qual é a raiz quadrada de 144 mais 7?"
```

### Modo 2: Interativo
```bash
python main.py
```

### Modo 3: Suite completa de evidências (gera artefatos para o DAS)
```bash
python run_evidence.py
```

Este modo executa três cenários distintos (cálculo, busca, pergunta híbrida) e gera:
- `evidence/execution_log.txt` - log completo da execução
- `evidence/traces.json` - traces OpenTelemetry estruturados
- `evidence/run_summary.md` - resumo dos resultados

## Estrutura

```
multiagent_prototype/
├── README.md
├── requirements.txt
├── main.py                  # CLI principal
├── run_evidence.py          # Suite de evidências
├── orchestrator.py          # LangGraph state machine
├── llm.py                   # Wrapper Ollama
├── memory.py                # Working memory + Chroma
├── tools.py                 # Calculadora + busca web
├── observability.py         # OpenTelemetry setup
└── agents/
    ├── router.py            # Classificação de intenção
    ├── executor.py          # Execução de ferramentas/LLM
    └── validator.py         # Verificação de saída
```

## Fluxo de execução (alinhado à Figura 6 do DAS)

1. **Usuário** envia pergunta via `main.py`
2. **Orquestrador** inicializa o estado e consulta a memória
3. **Agente Roteador** classifica a intenção (calculo | busca | conhecimento)
4. **Agente Executor** invoca a ferramenta apropriada ou o LLM diretamente
5. **Agente Validador** verifica se a resposta é consistente com a pergunta
6. **Orquestrador** persiste o turno na memória e retorna ao usuário
7. **Observabilidade**: cada etapa gera spans rastreáveis

## Mapeamento com os ADRs

| ADR | Como é validado no protótipo |
|---|---|
| #001 (LangGraph) | `orchestrator.py` implementa o StateGraph |
| #002 (Memória híbrida) | `memory.py` combina dict em sessão + Chroma persistente |
| #003 (OpenTelemetry) | `observability.py` instrumenta todos os agentes |

## Coleta de evidências

A pasta `evidence/` contém os artefatos gerados durante a execução real do protótipo, incorporados ao DAS como evidência empírica da Sprint 3.
