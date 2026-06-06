#!/bin/bash
# Setup automatico para Mac Mini M1
# Uso: bash SETUP_M1.sh

set -e

echo "==> Verificando Python 3.11+"
python3 --version

echo "==> Criando virtual environment"
python3 -m venv .venv
source .venv/bin/activate

echo "==> Atualizando pip"
pip install --upgrade pip

echo "==> Instalando dependencias"
pip install -r requirements.txt

echo "==> Testando compilacao do grafo"
python3 -c "from orchestrator import build_graph; g = build_graph(); print('GRAFO COMPILADO OK')"

echo ""
echo "==> Setup completo!"
echo ""
echo "Proximos passos:"
echo "  1. Garanta que o Ollama esta rodando em outro terminal: ollama serve"
echo "  2. Garanta que o modelo esta baixado:                   ollama pull qwen2.5:7b"
echo "  3. Execute um teste:                                    python main.py 'quanto e 2+2'"
echo "  4. Execute a suite de evidencias:                       python run_evidence.py"
echo ""
