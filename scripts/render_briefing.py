#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
render_briefing.py (Opção C - Otimizado)

Converte JSON minimalista em HTML + PDF bonito

Uso: python render_briefing.py output/briefing_20260520.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from weasyprint import HTML
except ImportError:
    print("⚠️ WeasyPrint não instalado. Instale: pip install weasyprint")
    HTML = None


CSS = """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f5f5f5;
    color: #333;
    padding: 20px;
    line-height: 1.6;
}

.container {
    max-width: 900px;
    margin: 0 auto;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.1);
    overflow: hidden;
}

.header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: white;
    padding: 30px 40px;
    text-align: center;
}

.header h1 {
    font-size: 28px;
    margin-bottom: 5px;
}

.header p {
    font-size: 14px;
    opacity: 0.9;
}

.content {
    padding: 30px 40px;
}

.section {
    margin-bottom: 40px;
}

.section-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #f0f0f0;
    color: #1a1a2e;
}

.prices-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 15px;
    margin-bottom: 20px;
}

.price-card {
    background: #f9f9f9;
    border-radius: 8px;
    padding: 15px;
    text-align: center;
    border-left: 4px solid #2563eb;
}

.price-card.positive { border-left-color: #16a34a; }
.price-card.negative { border-left-color: #dc2626; }
.price-card.neutral { border-left-color: #f59e0b; }

.price-card .label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    color: #666;
    margin-bottom: 5px;
}

.price-card .value {
    font-size: 18px;
    font-weight: 800;
    color: #1a1a2e;
}

.price-card .change {
    font-size: 12px;
    margin-top: 5px;
    font-weight: 600;
}

.price-card .change.up { color: #16a34a; }
.price-card .change.down { color: #dc2626; }

.highlights {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
}

.highlight-box {
    background: #f9f9f9;
    border-radius: 8px;
    padding: 15px;
    border-left: 4px solid #2563eb;
}

.highlight-box.fed { border-left-color: #dc2626; }
.highlight-box.bcb { border-left-color: #16a34a; }
.highlight-box.cripto { border-left-color: #f59e0b; }
.highlight-box.br { border-left-color: #2563eb; }
.highlight-box.trump { border-left-color: #dc2626; }

.highlight-box .label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    color: #666;
    margin-bottom: 8px;
}

.highlight-box .text {
    font-size: 13px;
    color: #333;
    line-height: 1.5;
}

.sentiment {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-bottom: 20px;
}

.sentiment-item {
    background: #f9f9f9;
    border-radius: 8px;
    padding: 15px;
    text-align: center;
}

.sentiment-item .label {
    font-size: 12px;
    font-weight: 700;
    color: #666;
    margin-bottom: 8px;
}

.sentiment-item .badge {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
}

.badge.bullish { background: #d1fae5; color: #065f46; }
.badge.bearish { background: #fee2e2; color: #991b1b; }
.badge.neutro { background: #fef3c7; color: #92400e; }

.events {
    background: #f9f9f9;
    border-radius: 8px;
    padding: 20px;
}

.events-list {
    list-style: none;
}

.events-list li {
    padding: 8px 0;
    border-bottom: 1px solid #eee;
    font-size: 13px;
}

.events-list li:last-child {
    border-bottom: none;
}

.events-list li:before {
    content: "▸";
    color: #2563eb;
    font-weight: bold;
    margin-right: 8px;
}

.footer {
    background: #f9f9f9;
    padding: 20px 40px;
    border-top: 1px solid #eee;
    font-size: 12px;
    color: #666;
    text-align: center;
}

@media print {
    body { padding: 0; }
    .container { box-shadow: none; }
}
"""


def load_json(filepath):
    """Carrega JSON do arquivo"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_color_class(var_str):
    """Define classe CSS baseada na variação"""
    if var_str.startswith('+'):
        return 'positive up'
    elif var_str.startswith('-'):
        return 'negative down'
    else:
        return 'neutral'


def render_html(data):
    """Gera HTML a partir do JSON"""
    
    meta = data['meta']
    precos = data['precos']
    destaques = data['destaques']
    sentimento = data['sentimento']
    eventos = data.get('proximos_eventos', [])
    
    # Preços HTML
    precos_html = ''
    preco_items = [
        ('BTC', precos['btc'], precos['btc_var']),
        ('ETH', precos['eth'], precos['eth_var']),
        ('Dólar', precos['dolar'], precos['dolar_var']),
        ('Ibov', precos['ibov'], precos['ibov_var']),
        ('Selic', precos['selic'], '')
    ]
    
    for label, valor, variacao in preco_items:
        color_class = get_color_class(variacao) if variacao else 'neutral'
        preco_html = f'<div class="price-card {color_class}">'
        preco_html += f'<div class="label">{label}</div>'
        preco_html += f'<div class="value">{valor}</div>'
        if variacao:
            preco_html += f'<div class="change">{variacao}</div>'
        preco_html += '</div>'
        precos_html += preco_html
    
    # Destaques HTML
    destaques_html = ''
    destaque_items = [
        ('Fed', destaques.get('fed', ''), 'fed'),
        ('BCB', destaques.get('bcb', ''), 'bcb'),
        ('Cripto 1', destaques.get('cripto_1', ''), 'cripto'),
        ('Cripto 2', destaques.get('cripto_2', ''), 'cripto'),
        ('Brasil 1', destaques.get('br_1', ''), 'br'),
        ('Brasil 2', destaques.get('br_2', ''), 'br'),
    ]
    
    for label, texto, tipo in destaque_items:
        if texto:
            destaques_html += f'<div class="highlight-box {tipo}">'
            destaques_html += f'<div class="label">{label}</div>'
            destaques_html += f'<div class="text">{texto}</div>'
            destaques_html += '</div>'
    
    # Sentimento HTML
    sentimento_html = ''
    for chave, valor in sentimento.items():
        label = {'cripto': 'Cripto', 'b3': 'B3', 'dolar': 'Dólar'}.get(chave, chave)
        sentimento_html += f'<div class="sentiment-item">'
        sentimento_html += f'<div class="label">{label}</div>'
        sentimento_html += f'<div class="badge {valor}">{valor.upper()}</div>'
        sentimento_html += '</div>'
    
    # Eventos HTML
    eventos_html = ''
    if eventos:
        eventos_html = '<ul class="events-list">'
        for evento in eventos:
            eventos_html += f'<li>{evento}</li>'
        eventos_html += '</ul>'
    
    # HTML final
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Briefing Diário — {meta['data']}</title>
    <style>{CSS}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Briefing Diário de Mercado</h1>
            <p>{meta['data']} • {meta['dia_semana']}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <div class="section-title">💰 Preços Principais</div>
                <div class="prices-grid">
                    {precos_html}
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">📰 Destaques do Dia</div>
                <div class="highlights">
                    {destaques_html}
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">🎯 Sentimento do Mercado</div>
                <div class="sentiment">
                    {sentimento_html}
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">📅 Próximos Eventos</div>
                <div class="events">
                    {eventos_html}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Fontes: {data.get('fontes', 'Variadas')} • Gerado automaticamente</p>
        </div>
    </div>
</body>
</html>"""
    
    return html


def main():
    """Executa renderização"""
    
    if len(sys.argv) < 2:
        print("❌ Uso: python render_briefing.py <arquivo_json>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not Path(json_file).exists():
        print(f"❌ Arquivo não encontrado: {json_file}")
        sys.exit(1)
    
    print(f"📖 Lendo: {json_file}")
    data = load_json(json_file)
    
    print("🎨 Renderizando HTML...")
    html_content = render_html(data)
    
    # Salvar HTML
    html_file = json_file.replace('.json', '.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ HTML salvo: {html_file}")
    
    # Salvar PDF
    if HTML:
        pdf_file = json_file.replace('.json', '.pdf')
        print("📄 Gerando PDF...")
        try:
            HTML(string=html_content, base_url='.').write_pdf(pdf_file)
            print(f"✅ PDF salvo: {pdf_file}")
        except Exception as e:
            print(f"⚠️ Erro ao gerar PDF: {e}")
    else:
        print("⚠️ WeasyPrint não disponível, PDF não gerado")
    
    print("\n✅ Renderização completa!")


if __name__ == '__main__':
    main()
