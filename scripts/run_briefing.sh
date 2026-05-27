#!/bin/bash

# run_briefing.sh
# ===============
# Script de execução automática com validação de conexão prévia
# 
# Uso:
#   bash run_briefing.sh <arquivo_json>
#   bash run_briefing.sh output/briefing_20260527.json
#
# O script:
#   1. Valida conexões críticas
#   2. Se OK → executa render_briefing.py
#   3. Se ERRO → pausa e avisa

set -e  # Parar em qualquer erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ─── Configurações ─────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERIFY_SCRIPT="$SCRIPT_DIR/verify_connections.py"
RENDER_SCRIPT="$SCRIPT_DIR/render_briefing.py"

# ─── Validações iniciais ──────────────────────────────────────────────────

if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Erro: arquivo JSON não especificado${NC}"
    echo ""
    echo "Uso:"
    echo "  bash run_briefing.sh <arquivo_json>"
    echo ""
    echo "Exemplo:"
    echo "  bash run_briefing.sh output/briefing_20260527.json"
    echo ""
    exit 1
fi

JSON_FILE="$1"

if [ ! -f "$JSON_FILE" ]; then
    echo -e "${RED}❌ Erro: arquivo não encontrado: $JSON_FILE${NC}"
    exit 1
fi

# ─── Executar verificação de conexão ───────────────────────────────────────

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}ROTINA BRIEFING DIÁRIO${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ ! -f "$VERIFY_SCRIPT" ]; then
    echo -e "${RED}❌ Erro: verify_connections.py não encontrado${NC}"
    echo "   Coloque o script na mesma pasta que render_briefing.py"
    exit 1
fi

echo -e "${YELLOW}[ETAPA 0/3]${NC} Validando conexões..."
echo ""

# Executar verificação
if python "$VERIFY_SCRIPT"; then
    CONNECTION_OK=true
else
    CONNECTION_OK=false
fi

# ─── Verificar resultado ───────────────────────────────────────────────────

if [ "$CONNECTION_OK" = false ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}🛑 ROTINA PAUSADA${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "Motivo: Falha crítica de conexão"
    echo ""
    echo "💡 Próximos passos:"
    echo "   1. Verifique sua conexão com a internet"
    echo "   2. Tente desabilitar VPN/proxy"
    echo "   3. Aguarde 5 minutos e execute novamente:"
    echo ""
    echo -e "   ${YELLOW}bash run_briefing.sh $JSON_FILE${NC}"
    echo ""
    exit 1
fi

# ─── Prosseguir com render ─────────────────────────────────────────────────

echo -e "${GREEN}✅ Conexões validadas${NC}"
echo ""
echo -e "${YELLOW}[ETAPA 1/3]${NC} Coleta e geração de dados..."
echo -e "${YELLOW}[ETAPA 2/3]${NC} Renderizando HTML..."
echo ""

if [ ! -f "$RENDER_SCRIPT" ]; then
    echo -e "${RED}❌ Erro: render_briefing.py não encontrado${NC}"
    exit 1
fi

python "$RENDER_SCRIPT" "$JSON_FILE"

RENDER_EXIT_CODE=$?

# ─── Resultado final ───────────────────────────────────────────────────────

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $RENDER_EXIT_CODE -eq 0 ]; then
    HTML_FILE="${JSON_FILE%.json}.html"
    echo -e "${GREEN}✅ ROTINA CONCLUÍDA COM SUCESSO${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "📄 Arquivo HTML gerado:"
    echo "   → $HTML_FILE"
    echo ""
    echo "🎯 Pronto para visualizar!"
    echo ""
    exit 0
else
    echo -e "${RED}❌ ERRO NA RENDERIZAÇÃO${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    exit 1
fi
