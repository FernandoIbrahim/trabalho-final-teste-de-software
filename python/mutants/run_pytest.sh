#!/bin/bash

# Script para executar  (Coverage.py) - Análise de Cobertura de Testes

echo "📊 Iniciando análise de cobertura com PYTEST (coverage.py)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Instalar dependências
echo "📦 Verificando dependências..."
pip install -q pytest-cov coverage

echo ""
echo "🧪 Executando testes com cobertura..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Executar testes com cobertura
python3 -m pytest tests/test_gilded_rose.py -v \
    --cov=gilded_rose \
    --cov-branch \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=json \
    --cov-report=xml

echo ""
echo "✅ Análise de cobertura concluída!"
echo ""
echo "📁 Relatórios gerados:"
echo "   📊 Terminal: ↑ (acima)"
echo "   🌐 HTML: coverage_html_report/index.html"
echo "   📄 JSON: coverage.json"
echo "   📋 XML: coverage.xml"
echo ""
echo "💡 Próximos passos:"
echo "   1. Abrir HTML em navegador: open coverage_html_report/index.html"
echo "   2. Revisar linhas não cobertas (Missing)"
echo "   3. Aumentar cobertura adicionando testes"
