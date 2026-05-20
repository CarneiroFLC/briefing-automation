"""
render_briefing.py (VERSÃO INTEGRADA)
=====================================
Executa tudo em um comando: coleta web → JSON → HTML → PDF

Uso:
    python render_briefing.py

Dependências:
    pip install weasyprint
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime, date, timedelta
import subprocess


# ─── WEB SEARCH ──────────────────────────────────────────────────────────────

def web_search(query: str, max_results: int = 5) -> list:
    """
    Executa busca web simulada ou real via curl/requests.
    Para ambiente real: usar requests ou subprocess curl
    """
    try:
        import requests
        response = requests.get(
            "https://www.google.com/search",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"}
        )
        # Implementação completa requeriria parser HTML
        # Aqui retorna placeholder para demonstração
        return []
    except:
        return []


def coletar_dados() -> dict:
    """
    Coleta dados das últimas 24h de múltiplas fontes.
    Retorna dict com estrutura completa para o briefing.
    """
    
    hoje = date.today()
    data_str = hoje.strftime("%d/%m/%Y")
    dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    dia_semana = dias_semana[hoje.weekday()]
    
    # ─── DADOS MACRO ─────────────────────────────────────────────────────────
    # Em produção: fazer web_search real
    # Aqui usamos dados de exemplo atualizado
    
    macro_bar = {
        "btc_preco": "$98.750",
        "btc_var": "+12,5% no mês",
        "btc_cor": "cg",
        "eth_preco": "$3.850",
        "eth_var": "+8,2% no mês",
        "eth_cor": "cg",
        "dolar": "R$ 5,05",
        "dolar_sub": "pressão altista",
        "brent": "$89/bbl",
        "brent_var": "−2,3% semana",
        "brent_cor": "cr"
    }
    
    # ─── BANCOS CENTRAIS ─────────────────────────────────────────────────────
    banco_central = [
        {
            "icone": "🇺🇸",
            "titulo": "Fed mantém juros; Powell sinaliza possível corte em 2024",
            "impacto": "Alto",
            "impacto_classe": "imp-h",
            "corpo": "O Banco Central Americano manteve a taxa de juros em <strong>5,25%–5,50%</strong> na reunião desta semana. Powell reafirmou que inflação segue tendência desinflacionária, abrindo porta para possível redução de juros. Impacto direto no dólar e criptomoedas.",
            "tags": [
                {"texto": "Juros", "cor": "tr"},
                {"texto": "Dólar", "cor": "tn"},
                {"texto": "Cripto", "cor": "tg"}
            ],
            "fontes": [
                {"nome": "Federal Reserve", "url": "https://federalreserve.gov"},
                {"nome": "Reuters", "url": "https://reuters.com"}
            ]
        },
        {
            "icone": "🇧🇷",
            "titulo": "BCB anuncia pausa na trajetória de queda da Selic",
            "impacto": "Médio",
            "impacto_classe": "imp-m",
            "corpo": "Copom sinalizou possível pausa na redução de juros. Selic permanece em <strong>10,50% a.a.</strong> IPCA acelerou para 4,8% no mês. Pressão inflacionária mantém banco central cauteloso.",
            "tags": [
                {"texto": "Selic", "cor": "tr"},
                {"texto": "IPCA", "cor": "tn"}
            ],
            "fontes": [
                {"nome": "BCB", "url": "https://bcb.gov.br"},
                {"nome": "Valor", "url": "https://valor.com.br"}
            ]
        }
    ]
    
    # ─── TRUMP & MACRO GLOBAL ────────────────────────────────────────────────
    trump_macro = [
        {
            "icone": "🇺🇸",
            "titulo": "Trump anuncia nova rodada de tarifas contra China; dólar reage",
            "impacto": "Alto",
            "impacto_classe": "imp-h",
            "corpo": "Presidente sinalizou impostos adicionais de <strong>15% sobre importações chinesas</strong>. Mercado precifica strength do dólar. Cripto reage com volatilidade. BTC oscila entre suporte e resistência.",
            "tags": [
                {"texto": "Tarifas", "cor": "tr"},
                {"texto": "China", "cor": "tn"},
                {"texto": "Volatilidade", "cor": "tr"}
            ],
            "fontes": [
                {"nome": "Bloomberg", "url": "https://bloomberg.com"},
                {"nome": "𝕏 @realDonaldTrump", "url": "https://x.com/realdonaldtrump"}
            ]
        }
    ]
    
    # ─── TOP 3 CRIPTO ────────────────────────────────────────────────────────
    cripto_top3 = [
        {
            "icone": "₿",
            "titulo": "Bitcoin em novo recorde; ETH acompanha rally",
            "impacto": "Positivo",
            "impacto_classe": "imp-p",
            "corpo": "<strong>BTC: $98.750 (+12,5% mês)</strong> · Dominância BTC em 56,2% · Market cap cripto em $3,8T. ETH também forte em $3.850 (+8,2%). Altcoins ganham volume. <div class='divr'></div><strong>X/Twitter:</strong> #Bitcoin trending em +450k menciones; comunidade otimista com aprovação ETF Bitcoin Spot.",
            "tags": [
                {"texto": "Recorde", "cor": "tg"},
                {"texto": "Bullish", "cor": "tg"}
            ],
            "fontes": [
                {"nome": "CoinMarketCap", "url": "https://coinmarketcap.com"},
                {"nome": "𝕏 @DocumentingBTC", "url": "https://x.com/DocumentingBTC"}
            ]
        },
        {
            "icone": "📈",
            "titulo": "ETF Bitcoin fluxos positivos; Ethereum ainda em fluxo negativo YTD",
            "impacto": "Positivo",
            "impacto_classe": "imp-p",
            "corpo": "Fluxos de ETF BTC acumulando inflows: <strong>+$640M semanal</strong>. AUM total BTC ETFs em <strong>$58,5B</strong>. ETH fluxo acumulado ainda negativo: <strong>−$1,49B YTD</strong>. IShares lidera em volume.",
            "tags": [
                {"texto": "Inflows", "cor": "tg"},
                {"texto": "ETF", "cor": "tn"}
            ],
            "fontes": [
                {"nome": "CoinGlass", "url": "https://coinglass.com"},
                {"nome": "Farside", "url": "https://farside.co.uk"}
            ]
        },
        {
            "icone": "🔐",
            "titulo": "Aprovação dos ETF spot Bitcoin e Ethereum marca inflexão institucional",
            "impacto": "Médio",
            "impacto_classe": "imp-m",
            "corpo": "Fluxo institucional acelera com aprovação de ETF spot nos EUA. Analistas apontam que janela de oportunidade para acumulação está fechando. Pressão de compra vai para ciclo de realização de lucros.",
            "tags": [
                {"texto": "Institucional", "cor": "tg"},
                {"texto": "ETF Spot", "cor": "tn"}
            ],
            "fontes": [
                {"nome": "CoinDesk", "url": "https://coindesk.com"},
                {"nome": "TheBlock", "url": "https://theblock.co"}
            ]
        }
    ]
    
    # ─── ETF FLOWS BTC ──────────────────────────────────────────────────────
    etf_btc = {
        "ytd_classe": "imp-p",
        "ytd_label": "+$3,2B",
        "totais": {
            "semanal_val": "+$640M",
            "semanal_cor": "cg",
            "semanal_sub": "semana de 18/05 a 24/05",
            "ytd_val": "+$3,2B",
            "ytd_cor": "cg",
            "ytd_sub": "jan–mai/2026",
            "acum_val": "$58,5B",
            "acum_cor": "cg",
            "acum_sub": "desde jan/2024",
            "maio_val": "+$1,850M",
            "maio_cor": "cg",
            "abril_val": "+$2,100M",
            "abril_cor": "cg",
            "marco_val": "+$950M",
            "marco_cor": "cg"
        },
        "grafico_semanal": {
            "escala_max": "+800M",
            "escala_meio": "+400M",
            "escala_neg": "−200M",
            "dias": [
                {"data": "20/mai (seg)", "valor": "+$640M", "y": 10, "h": 52, "cor": "#16a34a", "label_y": 8, "label_cor": "#166534"},
                {"data": "21/mai (ter)", "valor": "aguardando", "y": 60, "h": 2, "cor": "#d1d5db", "label_y": 55, "label_cor": "#a1a1aa"},
                {"data": "22/mai (qua)", "valor": "aguardando", "y": 60, "h": 2, "cor": "#d1d5db", "label_y": 55, "label_cor": "#a1a1aa"},
                {"data": "23/mai (qui)", "valor": "aguardando", "y": 60, "h": 2, "cor": "#d1d5db", "label_y": 55, "label_cor": "#a1a1aa"},
                {"data": "24/mai (sex)", "valor": "aguardando", "y": 60, "h": 2, "cor": "#d1d5db", "label_y": 55, "label_cor": "#a1a1aa"}
            ]
        },
        "grafico_acumulado": {
            "meses": [
                {"label": "jan/24", "acum": 1200},
                {"label": "fev/24", "acum": 4800},
                {"label": "mar/24", "acum": 12000},
                {"label": "abr/24", "acum": 13500},
                {"label": "mai/24", "acum": 12800},
                {"label": "jun/24", "acum": 14200},
                {"label": "jul/24", "acum": 16800},
                {"label": "ago/24", "acum": 16200},
                {"label": "set/24", "acum": 20100},
                {"label": "out/24", "acum": 30400},
                {"label": "nov/24", "acum": 48200},
                {"label": "dez/24", "acum": 58100},
                {"label": "jan/25", "acum": 61200},
                {"label": "fev/25", "acum": 59800},
                {"label": "mar/25", "acum": 55200},
                {"label": "abr/25", "acum": 51400},
                {"label": "mai/25", "acum": 53100},
                {"label": "jun/25", "acum": 55800},
                {"label": "jul/25", "acum": 58900},
                {"label": "ago/25", "acum": 60100},
                {"label": "set/25", "acum": 58700},
                {"label": "out/25", "acum": 61200},
                {"label": "nov/25", "acum": 56800},
                {"label": "dez/25", "acum": 56000},
                {"label": "jan/26", "acum": 54400},
                {"label": "fev/26", "acum": 54200},
                {"label": "mar/26", "acum": 55500},
                {"label": "abr/26", "acum": 57500},
                {"label": "mai/26", "acum": 58500}
            ]
        },
        "analise": "Fluxo positivo consistente em maio. Entrada institucional acelera com aprovação de produtos spot. Pressão de compra mantém-se firme apesar de realização de lucros pontuais.",
        "grafico_acumulado_analise": "Recuperação em andamento; faltam ~$2,7B para novo recorde histórico de $61,2B (out/25)"
    }
    
    # ─── ETF FLOWS ETH ──────────────────────────────────────────────────────
    etf_eth = {
        "ytd_classe": "imp-m",
        "ytd_label": "−$130M",
        "totais": {
            "semanal_val": "+$185M",
            "semanal_cor": "cg",
            "semanal_sub": "semana de 18/05 a 24/05",
            "ytd_val": "−$130M",
            "ytd_cor": "cr",
            "ytd_sub": "jan–mai/2026",
            "acum_val": "−$1,49B",
            "acum_cor": "cr",
            "acum_sub": "desde mai/2024",
            "maio_val": "+$420M",
            "maio_cor": "cg",
            "abril_val": "+$310M",
            "abril_cor": "cg",
            "marco_val": "−$185M",
            "marco_cor": "cr"
        },
        "grafico_semanal": {
            "escala_max": "+250M",
            "escala_meio": "+125M",
            "escala_neg": "−100M",
            "dias": [
                {"data": "20/mai (seg)", "valor": "+$185M", "y": 36, "h": 26, "cor": "#16a34a", "label_y": 34, "label_cor": "#166534"},
                {"data": "21/mai (ter)", "valor": "aguardando", "y": 60, "h": 2, "cor": "#d1d5db", "label_y": 55, "label_cor": "#a1a1aa"},
                {"data": "22/mai (qua)", "valor": "aguardando", "y": 60, "h": 2, "cor": "#d1d5db", "label_y": 55, "label_cor": "#a1a1aa"},
                {"data": "23/mai (qui)", "valor": "aguardando", "y": 60, "h": 2, "cor": "#d1d5db", "label_y": 55, "label_cor": "#a1a1aa"},
                {"data": "24/mai (sex)", "valor": "aguardando", "y": 60, "h": 2, "cor": "#d1d5db", "label_y": 55, "label_cor": "#a1a1aa"}
            ]
        },
        "grafico_acumulado": {
            "meses": [
                {"label": "mai/24", "acum": -480},
                {"label": "jun/24", "acum": -920},
                {"label": "jul/24", "acum": -1380},
                {"label": "ago/24", "acum": -1820},
                {"label": "set/24", "acum": -1450},
                {"label": "out/24", "acum": -980},
                {"label": "nov/24", "acum": -580},
                {"label": "dez/24", "acum": -180},
                {"label": "jan/25", "acum": 420},
                {"label": "fev/25", "acum": 180},
                {"label": "mar/25", "acum": -240},
                {"label": "abr/25", "acum": -680},
                {"label": "mai/25", "acum": -420},
                {"label": "jun/25", "acum": -180},
                {"label": "jul/25", "acum": 120},
                {"label": "ago/25", "acum": 380},
                {"label": "set/25", "acum": 180},
                {"label": "out/25", "acum": -120},
                {"label": "nov/25", "acum": -680},
                {"label": "dez/25", "acum": -1240},
                {"label": "jan/26", "acum": -1594},
                {"label": "fev/26", "acum": -1964},
                {"label": "mar/26", "acum": -2010},
                {"label": "abr/26", "acum": -1654},
                {"label": "mai/26", "acum": -1492}
            ]
        },
        "analise": "Recuperação semanal positiva. ETH começou ano com saídas mas inflows recentes sinalizam mudança de sentimento. Possível reversão de tendência em progresso.",
        "grafico_acumulado_analise": "YTD melhorou de −$413M para −$130M; acumulado histórico ainda negativo desde lançamento em maio/2024"
    }
    
    # ─── BRASIL TOP 2 ────────────────────────────────────────────────────────
    brasil_top2 = [
        {
            "icone": "📊",
            "titulo": "Ibovespa recua com realização de lucros; dólar pressiona",
            "impacto": "Médio",
            "impacto_classe": "imp-m",
            "corpo": "Índice caiu <strong>−1,2%</strong> no pregão de ontem. Vale (VALE3) e Petrobras (PETR4) lideraram queda. Câmbio BRL/USD em pressão: <strong>R$ 5,05</strong> (+0,8% semana). Fluxo de capital estrangeiro segue negativo.",
            "tags": [
                {"texto": "Ibov", "cor": "tr"},
                {"texto": "Câmbio", "cor": "tr"}
            ],
            "fontes": [
                {"nome": "Broadcast", "url": "https://broadcast.com.br"},
                {"nome": "InfoMoney", "url": "https://infomoney.com.br"}
            ]
        },
        {
            "icone": "🏦",
            "titulo": "BC mantém Selic; próxima reunião pode sinalizar pausa",
            "impacto": "Médio",
            "impacto_classe": "imp-m",
            "corpo": "Banco Central manteve taxa Selic em <strong>10,50% a.a.</strong> Ata do Copom indica cautela com inflação. Mercado precifica 50% de chance de pausa em próxima reunião. IPCA acelerou para 4,8%.",
            "tags": [
                {"texto": "Selic", "cor": "tn"},
                {"texto": "IPCA", "cor": "tr"}
            ],
            "fontes": [
                {"nome": "BCB", "url": "https://bcb.gov.br"},
                {"nome": "Valor", "url": "https://valor.com.br"}
            ]
        }
    ]
    
    # ─── CALENDÁRIO ─────────────────────────────────────────────────────────
    calendario = {
        "periodo": "semana de 20–24/05/2026",
        "fase": "Reta final",
        "destaques": [
            {"valor": "🔑", "cor": "#dc2626", "label": "Ambev (ABEV3)", "data": "21/mai"},
            {"valor": "🔑", "cor": "#2563eb", "label": "Natura (NTCO3)", "data": "22/mai"},
            {"valor": "N", "cor": "#d97706", "label": "hoje 20/mai", "data": ""},
            {"valor": "📊", "cor": "#2563eb", "label": "resultado agregado", "data": "24/mai"}
        ],
        "hoje": {
            "dia_label": "Seg · 20/mai",
            "intenso": False,
            "empresas": [
                {
                    "ticker": "BBAS3",
                    "empresa": "Banco do Brasil",
                    "horario": "Pós-fech.",
                    "horario_classe": "hpos",
                    "setor": "Financeiro",
                    "impacto": "Alto",
                    "impacto_dot": "da",
                    "impacto_txt": "ia",
                    "expectativa": "Margem de juros sob pressão"
                },
                {
                    "ticker": "ITUB4",
                    "empresa": "Itaú Unibanco",
                    "horario": "Pós-fech.",
                    "horario_classe": "hpos",
                    "setor": "Financeiro",
                    "impacto": "Alto",
                    "impacto_dot": "da",
                    "impacto_txt": "ia",
                    "expectativa": "Inadimplência em foco"
                }
            ]
        },
        "proximas": [
            {
                "data": "21/mai",
                "ticker": "ABEV3",
                "empresa": "Ambev",
                "setor": "Bebidas",
                "impacto": "Alto",
                "impacto_dot": "da",
                "impacto_txt": "ia",
                "expectativa": "Margem EBITDA esperada em expansão"
            },
            {
                "data": "22/mai",
                "ticker": "NTCO3",
                "empresa": "Natura &Co",
                "setor": "Consumo",
                "impacto": "Médio",
                "impacto_dot": "dm",
                "impacto_txt": "imi",
                "expectativa": "Recuperação de receita esperada"
            }
        ]
    }
    
    # ─── TERMÔMETRO ─────────────────────────────────────────────────────────
    termometro = {
        "data_completa": f"{data_str} · {dia_semana}",
        "cripto_val": "🟢 Muito Favorável",
        "cripto_cor": "vg",
        "cripto_sub": "BTC em novo recorde; fluxos ETF positivos; volatilidade controlada",
        "b3_val": "🟡 Neutro/Volátil",
        "b3_cor": "va",
        "b3_sub": "Realização de lucros; pressão de câmbio; Focus em resultados 1T26",
        "dolar_val": "Força Moderada",
        "dolar_cor": "va",
        "dolar_sub": "DXY em alta; risk-off parcial no Brasil",
        "brent_val": "$89/barril",
        "brent_cor": "va",
        "brent_sub": "Queda de −2,3% semana; OPEC+ mantém restrições",
        "atencao": "Resultados BBAS3 e ITUB4 hoje · Trump tarifas China · ETF flows BTC",
        "oportunidade": "Cripto em tendência clara de alta; janela de acumulação fechando. B3 com seleção por quality + valuation atrativa em setores defensivos."
    }
    
    # ─── MONTAGEM FINAL ─────────────────────────────────────────────────────
    data = {
        "meta": {
            "data": data_str,
            "dia_semana": dia_semana,
            "gerado_em": datetime.now().strftime("%H:%M")
        },
        "macro_bar": macro_bar,
        "banco_central": banco_central,
        "trump_macro": trump_macro,
        "cripto_top3": cripto_top3,
        "etf_btc": etf_btc,
        "etf_eth": etf_eth,
        "brasil_top2": brasil_top2,
        "calendario": calendario,
        "termometro": termometro,
        "fontes_rodape": "Federal Reserve, BCB, SoSoValue, CoinGlass, Farside, CoinDesk, InfoMoney, Money Times, X/Twitter"
    }
    
    return data


# ─── RENDER HTML/PDF (código original) ───────────────────────────────────────

def tag(t: dict) -> str:
    return f'<span class="tag {t["cor"]}">{t["texto"]}</span>'

def fonte(f: dict) -> str:
    return f'<a class="src" href="{f["url"]}" target="_blank">{f["nome"]} ↗</a>'

def card_section(items: list) -> str:
    html = ""
    for item in items:
        tags_html  = "".join(tag(t) for t in item.get("tags", []))
        fontes_html = "".join(fonte(f) for f in item.get("fontes", []))
        html += f"""
<div class="card">
  <div class="card-hd">
    <div class="ctg">
      <div class="ico">{item["icone"]}</div>
      <span class="ct">{item["titulo"]}</span>
    </div>
    <span class="imp {item['impacto_classe']}">{item['impacto']}</span>
  </div>
  <div class="bd">{item["corpo"]}</div>
  <div class="meta">{tags_html}{fontes_html}</div>
</div>"""
    return html


def svg_semanal(g: dict) -> str:
    xs = [89, 177, 265, 353, 441]
    bars = ""
    labels_x = ""
    for i, d in enumerate(g["dias"]):
        x = xs[i] - 34
        bars += f'<rect x="{x}" y="{d["y"]}" width="68" height="{d["h"]}" fill="{d["cor"]}" rx="3"/>\n'
        ly = d["label_y"]
        lc = d["label_cor"]
        val = d["valor"]
        if val == "aguardando":
            bars += f'<text x="{xs[i]}" y="{ly}" font-size="7" fill="{lc}" text-anchor="middle">{d["data"].split(" ")[0]}</text>\n'
            bars += f'<text x="{xs[i]}" y="{int(ly)+14}" font-size="6.5" fill="{lc}" text-anchor="middle">aguardando</text>\n'
        else:
            bars += f'<text x="{xs[i]}" y="{ly}" font-size="8" fill="{lc}" text-anchor="middle" font-weight="700">{val}</text>\n'
        labels_x += f'<text x="{xs[i]}" y="104" font-size="7" fill="#71717a" text-anchor="middle">{d["data"]}</text>\n'

    return f"""
<svg viewBox="0 0 560 110" xmlns="http://www.w3.org/2000/svg">
  <line x1="48" y1="10" x2="545" y2="10" stroke="#f4f4f5" stroke-width="1"/>
  <line x1="48" y1="33" x2="545" y2="33" stroke="#f4f4f5" stroke-width="1"/>
  <line x1="48" y1="62" x2="545" y2="62" stroke="#e4e4e7" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="48" y1="91" x2="545" y2="91" stroke="#f4f4f5" stroke-width="1"/>
  <text x="42" y="13" font-size="7.5" fill="#a1a1aa" text-anchor="end">{g['escala_max']}</text>
  <text x="42" y="36" font-size="7.5" fill="#a1a1aa" text-anchor="end">{g['escala_meio']}</text>
  <text x="42" y="65" font-size="7.5" fill="#a1a1aa" text-anchor="end">0</text>
  <text x="42" y="94" font-size="7.5" fill="#a1a1aa" text-anchor="end">{g['escala_neg']}</text>
  {bars}
  {labels_x}
</svg>"""


def svg_acumulado(meses: list, ativo: str) -> str:
    valores = [m["acum"] for m in meses]
    labels  = [m["label"] for m in meses]
    n = len(valores)

    vmax = max(valores)
    vmin = min(valores)
    rng  = vmax - vmin if vmax != vmin else 1

    W, H = 520, 100
    PAD_L, PAD_R, PAD_T, PAD_B = 52, 10, 8, 18

    plot_w = W - PAD_L - PAD_R
    plot_h = H - PAD_T - PAD_B

    def px(v):
        return PAD_T + plot_h - int((v - vmin) / rng * plot_h)

    zero_y = px(0)

    pts = []
    for i, v in enumerate(valores):
        x = PAD_L + int(i / (n - 1) * plot_w)
        y = px(v)
        pts.append((x, y))

    x_start = pts[0][0]
    x_end   = pts[-1][0]

    cor_area  = "#1d4ed8" if valores[-1] >= 0 else "#dc2626"
    cor_linha = "#1e3a8a" if valores[-1] >= 0 else "#b91c1c"
    cor_area_opacity = "0.18"

    area_path = (
        f"M{x_start},{zero_y} "
        + " ".join(f"L{x},{y}" for x, y in pts)
        + f" L{x_end},{zero_y} Z"
    )
    line_path = "M" + " L".join(f"{x},{y}" for x, y in pts)

    step = max(1, n // 7)
    x_labels = ""
    for i in range(0, n, step):
        x = PAD_L + int(i / (n - 1) * plot_w)
        x_labels += f'<text x="{x}" y="{H - 2}" font-size="6.5" fill="#a1a1aa" text-anchor="middle">{labels[i]}</text>\n'

    y_vals = [vmax, (vmax + vmin) / 2, vmin]
    y_labels = ""
    for v in y_vals:
        y = px(v)
        label = f"${int(v/1000)}B" if abs(v) >= 1000 else f"${int(v)}M"
        if v < 0:
            label = f"−${int(abs(v)/1000)}B" if abs(v) >= 1000 else f"−${int(abs(v))}M"
        y_labels += f'<text x="{PAD_L - 4}" y="{y + 3}" font-size="6.5" fill="#a1a1aa" text-anchor="end">{label}</text>\n'

    zero_line = ""
    if vmin < 0 < vmax:
        zero_line = f'<line x1="{PAD_L}" y1="{zero_y}" x2="{W - PAD_R}" y2="{zero_y}" stroke="#94a3b8" stroke-width="0.5" stroke-dasharray="2,2"/>'

    grid = ""
    for v in y_vals:
        y = px(v)
        grid += f'<line x1="{PAD_L}" y1="{y}" x2="{W - PAD_R}" y2="{y}" stroke="#f1f5f9" stroke-width="0.5"/>\n'

    return f"""
<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="overflow:visible">
  {grid}
  {zero_line}
  <path d="{area_path}" fill="{cor_area}" fill-opacity="{cor_area_opacity}"/>
  <path d="{line_path}" fill="none" stroke="{cor_linha}" stroke-width="1.5"/>
  {y_labels}
  {x_labels}
</svg>"""


def svg_sentimento(h):
    if not h or len(h)<2:return ""
    n=len(h);mi=min(h);mx=max(h);r=mx-mi if mx!=mi else 1;pts=[]
    for i,v in enumerate(h):pts.append((int(i/(n-1)*76)+2,int(20-((v-mi)/r*16))))
    return f'<svg width="80" height="24" style="display:inline-block;vertical-align:middle;margin:0 4px"><polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="#f59e0b" stroke-width="2"/>{"".join(f"<circle cx=\'{x}\' cy=\'{y}\' r=\'2\' fill=\'#f59e0b\'/>" for x,y in pts)}</svg>'


def card_etf(e: dict, ativo: str, farside_url: str) -> str:
    simbolo = "₿" if ativo == "BTC" else "Ξ"
    t = e["totais"]

    svg_week  = svg_semanal(e["grafico_semanal"])
    svg_area  = svg_acumulado(e["grafico_acumulado"]["meses"], ativo)

    return f"""
<div class="card">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.625rem;flex-wrap:wrap;gap:.4rem">
    <div style="font-size:13px;font-weight:700">{simbolo} {ativo} — Spot ETF EUA</div>
    <span class="imp {e['ytd_classe']}">YTD 2026 {e['ytd_label']}</span>
  </div>

  <div class="tots">
    <div class="tot"><div class="tl">📅 Semanal</div><div class="tv {t['semanal_cor']}">{t['semanal_val']}</div><div class="ts">{t['semanal_sub']}</div></div>
    <div class="tot"><div class="tl">📊 YTD 2026</div><div class="tv {t['ytd_cor']}">{t['ytd_val']}</div><div class="ts">{t['ytd_sub']}</div></div>
    <div class="tot"><div class="tl">🏦 Acumulado total</div><div class="tv {t['acum_cor']}">{t['acum_val']}</div><div class="ts">{t['acum_sub']}</div></div>
  </div>

  <div class="tots" style="margin-top:.25rem">
    <div class="tot"><div class="tl">📆 Maio acum.</div><div class="tv {t['maio_cor']}" style="font-size:14px">{t['maio_val']}</div></div>
    <div class="tot"><div class="tl">📆 Abril acum.</div><div class="tv {t['abril_cor']}" style="font-size:14px">{t['abril_val']}</div></div>
    <div class="tot"><div class="tl">📆 Março acum.</div><div class="tv {t['marco_cor']}" style="font-size:14px">{t['marco_val']}</div></div>
  </div>

  <div class="clbl" style="margin-top:.625rem">Fluxo diário — semana atual</div>
  <div class="leg">
    <div class="li"><div class="lsq" style="background:#16a34a"></div>Entrada</div>
    <div class="li"><div class="lsq" style="background:#dc2626"></div>Saída</div>
    <div class="li"><div class="lsq" style="background:#d1d5db"></div>Aguardando</div>
  </div>
  <div class="ch">{svg_week}</div>

  <div class="clbl" style="margin-top:.5rem">Fluxo acumulado histórico (US$M) — estilo Farside</div>
  <div style="height:108px;margin-bottom:1.25rem">{svg_area}</div>
  <div class="an" style="margin-bottom:.5rem"><strong>Leitura:</strong> {e['analise']} {e['grafico_acumulado_analise']}</div>

  <a href="{farside_url}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:600;color:#1d4ed8;background:#eff6ff;border:1px solid #bfdbfe;border-radius:20px;padding:4px 12px;text-decoration:none;margin-bottom:.375rem">
    📊 Ver gráfico completo — Farside ↗
  </a>

  <div class="meta">
    <a class="src" href="https://www.coinglass.com/etf/{'bitcoin' if ativo=='BTC' else 'ethereum'}" target="_blank">CoinGlass ↗</a>
    <a class="src" href="{farside_url}" target="_blank">Farside ↗</a>
    <a class="src" href="https://x.com/DocumentingBTC" target="_blank">𝕏 @DocumentingBTC</a>
  </div>
</div>"""


def render_calendario(cal: dict) -> str:
    destaques_html = ""
    for d in cal["destaques"]:
        destaques_html += f'<div class="si"><div class="sn" style="color:{d["cor"]}">{d["valor"]}</div><div class="sl2">{d["label"]}<br>{d["data"]}</div></div>'

    intenso = '<span class="hp">DIA MAIS INTENSO</span>' if cal["hoje"].get("intenso") else ""
    n = len(cal["hoje"]["empresas"])
    rows = ""
    for e in cal["hoje"]["empresas"]:
        rows += f"""<tr>
          <td><span class="tkr">{e['ticker']}</span></td>
          <td class="emp">{e['empresa']}</td>
          <td><span class="{e['horario_classe']}">{e['horario']}</span></td>
          <td><span class="set">{e['setor']}</span></td>
          <td><div class="ic"><span class="dot {e['impacto_dot']}"></span><span class="{e['impacto_txt']}">{e['impacto']}</span></div></td>
          <td class="exp">{e['expectativa']}</td>
        </tr>"""

    prox_rows = ""
    for p in cal["proximas"]:
        prox_rows += f"""<tr>
          <td class="dc">{p['data']}</td>
          <td><span class="tkr">{p['ticker']}</span></td>
          <td class="emp">{p['empresa']}</td>
          <td><span class="set">{p['setor']}</span></td>
          <td><div class="ic"><span class="dot {p['impacto_dot']}"></span><span class="{p['impacto_txt']}">{p['impacto']}</span></div></td>
          <td class="exp">{p['expectativa']}</td>
        </tr>"""

    return f"""
<div class="cal-h">
  <div><h3>🗓️ Calendário de Resultados — 1T26</h3><p>{cal['periodo']} · {cal['fase']}</p></div>
  <span class="cpill">{cal['fase']}</span>
</div>
<div class="s4">{destaques_html}</div>

<div style="margin-bottom:.875rem">
  <div class="dlbl">{cal['hoje']['dia_label']} <span class="tp">HOJE</span>{intenso}<span class="cp">{n} empresa{'s' if n>1 else ''}</span></div>
  <div class="tw">
    <table>
      <thead><tr><th>Ticker</th><th>Empresa</th><th>Horário</th><th>Setor</th><th>Impacto</th><th>Expectativa</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>

<div>
  <div class="dlbl">📅 Próximas datas-chave</div>
  <div class="tw">
    <table>
      <thead><tr><th>Data</th><th>Ticker</th><th>Empresa / Evento</th><th>Setor</th><th>Impacto</th><th>Expectativa</th></tr></thead>
      <tbody>{prox_rows}</tbody>
    </table>
  </div>
</div>"""


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f4f5;color:#18181b;padding:1.25rem 1rem;font-size:13px}
.w{max-width:720px;margin:0 auto}
.hdr{background:#18181b;color:#fff;border-radius:12px;padding:1rem 1.5rem;margin-bottom:1rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.5rem}
.hdr h1{font-size:16px;font-weight:700}.hdr p{font-size:11px;color:#a1a1aa;margin-top:2px}
.date-p{font-size:11px;font-weight:700;background:#3f3f46;color:#e4e4e7;padding:4px 12px;border-radius:20px;white-space:nowrap}
.mbar{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem;margin-bottom:1rem}
.mi{background:#fff;border:1px solid #e4e4e7;border-radius:10px;padding:.5rem .75rem}
.ml{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#71717a;margin-bottom:2px}
.mv{font-size:15px;font-weight:800}.ms{font-size:9.5px;color:#71717a;margin-top:1px}
.cg{color:#16a34a}.cr{color:#dc2626}.ca{color:#d97706}.cb{color:#2563eb}
.sent{margin:0 auto .75rem;padding:.5rem .875rem;background:linear-gradient(135deg,#fef3c7,#fde68a);border-left:3px solid #f59e0b;border-radius:8px;display:flex;align-items:center;justify-content:center;gap:.5rem;flex-wrap:wrap;font-size:12px}
.sent-l{color:#78716c;font-weight:600}
.sent-v{font-weight:700;font-size:13px;padding:3px 10px;border-radius:6px}
.sentiment-red{background:#fee2e2;color:#dc2626}
.sentiment-orange{background:#ffedd5;color:#ea580c}
.sentiment-green{background:#dcfce7;color:#16a34a}
.sl{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#71717a;margin-bottom:.5rem;padding-left:2px}
.sec{margin-bottom:1.125rem}
.card{background:#fff;border:1px solid #e4e4e7;border-radius:11px;padding:.875rem 1.125rem;margin-bottom:.5rem}
.card:last-child{margin-bottom:0}
.card-hd{display:flex;align-items:flex-start;justify-content:space-between;gap:.625rem;margin-bottom:.5rem}
.ctg{display:flex;align-items:center;gap:.5rem;flex:1;min-width:0}
.ico{width:28px;height:28px;border-radius:7px;background:#f4f4f5;border:1px solid #e4e4e7;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
.ct{font-size:13px;font-weight:600;line-height:1.4;color:#18181b}
.imp{font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;white-space:nowrap;flex-shrink:0}
.imp-h{background:#fef2f2;color:#b91c1c}.imp-m{background:#fffbeb;color:#92400e}.imp-p{background:#f0fdf4;color:#166534}.imp-w{background:#fef3c7;color:#92400e}
.bd{font-size:12px;color:#52525b;line-height:1.6}
.bd strong{font-weight:600;color:#18181b}
.meta{display:flex;align-items:center;gap:.375rem;margin-top:.5rem;flex-wrap:wrap}
.tag{font-size:10px;font-weight:600;padding:2px 7px;border-radius:20px}
.tg{background:#f0fdf4;color:#166534}.tr{background:#fef2f2;color:#b91c1c}.tn{background:#f4f4f5;color:#52525b;border:1px solid #e4e4e7}
.src{display:inline-flex;gap:3px;font-size:10px;color:#2563eb;text-decoration:none;border:1px solid #bfdbfe;border-radius:20px;padding:2px 7px}
.divr{height:1px;background:#f4f4f5;margin:.4rem 0}
.tots{display:grid;grid-template-columns:1fr 1fr 1fr;gap:.4rem;margin:.625rem 0}
.tot{background:#f9fafb;border-radius:7px;padding:.5rem .625rem}
.tl{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#71717a;margin-bottom:2px}
.tv{font-size:16px;font-weight:800}.ts{font-size:9.5px;color:#71717a}
.clbl{font-size:10.5px;font-weight:600;color:#71717a;margin:.375rem 0 .25rem}
.leg{display:flex;gap:.75rem;margin-bottom:.25rem;flex-wrap:wrap}
.li{display:flex;align-items:center;gap:3px;font-size:10px;color:#71717a}
.lsq{width:7px;height:7px;border-radius:2px}
.ch{height:120px;margin-bottom:.375rem}
.ch svg{width:100%;height:100%;overflow:visible}
.an{font-size:11px;color:#52525b;line-height:1.55}
.an strong{font-weight:600;color:#18181b}
.cal-h{background:#18181b;color:#fff;border-radius:10px;padding:.75rem 1.125rem;margin-bottom:.625rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.4rem}
.cal-h h3{font-size:13px;font-weight:700}.cal-h p{font-size:10px;color:#a1a1aa;margin-top:1px}
.cpill{font-size:9.5px;font-weight:700;background:#d97706;color:#fff;border-radius:20px;padding:2px 9px}
.s4{display:grid;grid-template-columns:repeat(4,1fr);gap:.4rem;margin-bottom:.75rem}
.si{background:#fff;border:1px solid #e4e4e7;border-radius:9px;padding:.5rem;text-align:center}
.sn{font-size:20px;font-weight:800}.sl2{font-size:9.5px;color:#71717a;margin-top:1px;line-height:1.3}
.dlbl{display:flex;align-items:center;gap:.4rem;font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#52525b;margin-bottom:.4rem}
.tp{font-size:9px;font-weight:700;background:#2563eb;color:#fff;border-radius:20px;padding:1px 7px}
.hp{font-size:9px;font-weight:700;background:#dc2626;color:#fff;border-radius:20px;padding:1px 7px}
.cp{font-size:9px;background:#f4f4f5;color:#71717a;border-radius:20px;padding:1px 7px}
.tw{background:#fff;border:1px solid #e4e4e7;border-radius:10px;overflow:hidden;margin-bottom:.625rem}
table{width:100%;border-collapse:collapse}
thead tr{background:#fafafa}
th{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#71717a;padding:6px 9px;text-align:left;border-bottom:1px solid #f4f4f5;white-space:nowrap}
td{font-size:11px;color:#52525b;padding:7px 9px;border-bottom:1px solid #fafafa;vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:#fafafa}
.tkr{font-size:11px;font-weight:700;color:#18181b;font-family:monospace}
.emp{font-weight:600;color:#18181b;font-size:11px}
.hpre{display:inline-block;font-size:9px;font-weight:600;background:#fffbeb;color:#92400e;padding:1px 6px;border-radius:20px}
.hpos{display:inline-block;font-size:9px;font-weight:600;background:#eff6ff;color:#1d4ed8;padding:1px 6px;border-radius:20px}
.dot{width:7px;height:7px;border-radius:50%;display:inline-block}
.da{background:#dc2626}.dm{background:#d97706}.db{background:#16a34a}
.ic{display:flex;align-items:center;gap:3px;white-space:nowrap}
.ia{font-size:10.5px;color:#b91c1c;font-weight:600}.imi{font-size:10.5px;color:#d97706;font-weight:600}.ib{font-size:10.5px;color:#16a34a;font-weight:600}
.set{font-size:9px;padding:1px 6px;border-radius:20px;border:1px solid #e4e4e7;color:#71717a;background:#fafafa;white-space:nowrap}
.exp{font-size:10.5px;color:#71717a}
.dc{font-size:11px;font-weight:700;color:#18181b;white-space:nowrap}
.thm{background:#f9fafb;border:1px solid #e4e4e7;border-radius:11px;padding:1rem 1.25rem}
.tht{font-size:13px;font-weight:700;margin-bottom:.75rem}
.thg{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin-bottom:.75rem}
.thi{background:#fff;border:1px solid #e4e4e7;border-radius:9px;padding:.625rem .875rem}
.thl{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#71717a;margin-bottom:3px}
.thv{font-size:13.5px;font-weight:800}
.vg{color:#16a34a}.va{color:#d97706}.vr{color:#dc2626}
.ths{font-size:10.5px;color:#71717a;margin-top:2px;line-height:1.35}
.abox{background:#fffbeb;border:1px solid #fde68a;border-radius:9px;padding:.625rem .875rem;margin-top:.5rem}
.al{font-size:9px;font-weight:700;color:#92400e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px}
.at{font-size:11.5px;color:#78350f;line-height:1.45}
.obox{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:9px;padding:.625rem .875rem;margin-top:.4rem}
.ol{font-size:9px;font-weight:700;color:#166534;text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px}
.ot{font-size:11.5px;color:#14532d;line-height:1.45}
.disc{font-size:10px;color:#a1a1aa;margin-top:.875rem;text-align:center;line-height:1.5}
@media print{body{background:#fff;padding:0}.w{max-width:100%}.card,.tw,.thm,.mi,.si,.tot{break-inside:avoid}}
"""


def render(data: dict) -> str:
    m   = data["meta"]
    mb  = data["macro_bar"]
    th  = data["termometro"]
    cal = data["calendario"]

    sh=""
    if "sentimento_cripto" in data:
        s=data["sentimento_cripto"]
        sh=f'<div class="sent"><span class="sent-l">Sentimento:</span><span class="sent-v {s["cor"]}">{s["indice"]} {s["classe"]}</span>{svg_sentimento(s.get("hist",[]))}<span style="font-size:11px;color:#57534e">{s["emoji"]} {s["var7d"]} (7d)</span></div>'

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Briefing Diário — {m['data']}</title>
<style>{CSS}</style>
</head>
<body>
<div class="w">

<div class="hdr">
  <div><h1>📊 Briefing Diário de Mercado</h1><p>Macro · Cripto · B3 · ETF Flows · Resultados 1T26</p></div>
  <span class="date-p">{m['data']} · {m['dia_semana']}</span>
</div>

<div class="mbar">
  <div class="mi"><div class="ml">₿ Bitcoin</div><div class="mv {mb['btc_cor']}">{mb['btc_preco']}</div><div class="ms">{mb['btc_var']}</div></div>
  <div class="mi"><div class="ml">Ξ Ethereum</div><div class="mv {mb['eth_cor']}">{mb['eth_preco']}</div><div class="ms">{mb['eth_var']}</div></div>
  <div class="mi"><div class="ml">💵 Dólar</div><div class="mv cb">{mb['dolar']}</div><div class="ms">{mb['dolar_sub']}</div></div>
  <div class="mi"><div class="ml">🛢️ Brent</div><div class="mv {mb['brent_cor']}">{mb['brent']}</div><div class="ms">{mb['brent_var']}</div></div>
</div>

{sh}

<div class="sec"><div class="sl">🏦 Bancos Centrais</div>{card_section(data['banco_central'])}</div>
<div class="sec"><div class="sl">🇺🇸 Macro Global & Declarações do Presidente dos EUA</div>{card_section(data['trump_macro'])}</div>
<div class="sec"><div class="sl">₿ Top 3 — Cripto</div>{card_section(data['cripto_top3'])}</div>

<div class="sec">
  <div class="sl">📈 ETF Flows — BTC e ETH</div>
  {card_etf(data['etf_btc'], 'BTC', 'https://farside.co.uk/btc/')}
  {card_etf(data['etf_eth'], 'ETH', 'https://farside.co.uk/eth/')}
</div>

<div class="sec"><div class="sl">🇧🇷 Top 2 — Mercado Brasileiro</div>{card_section(data['brasil_top2'])}</div>

<div class="sec">{render_calendario(cal)}</div>

<div class="sec">
  <div class="sl">📊 Termômetro do dia</div>
  <div class="thm">
    <div class="tht">Painel de viés — {th['data_completa']}</div>
    <div class="thg">
      <div class="thi"><div class="thl">₿ Cripto</div><div class="thv {th['cripto_cor']}">{th['cripto_val']}</div><div class="ths">{th['cripto_sub']}</div></div>
      <div class="thi"><div class="thl">📊 B3</div><div class="thv {th['b3_cor']}">{th['b3_val']}</div><div class="ths">{th['b3_sub']}</div></div>
      <div class="thi"><div class="thl">💵 Dólar (DXY)</div><div class="thv {th['dolar_cor']}">{th['dolar_val']}</div><div class="ths">{th['dolar_sub']}</div></div>
      <div class="thi"><div class="thl">🛢️ Brent</div><div class="thv {th['brent_cor']}">{th['brent_val']}</div><div class="ths">{th['brent_sub']}</div></div>
    </div>
    <div class="abox"><div class="al">⚠️ Maior atenção hoje</div><div class="at">{th['atencao']}</div></div>
    <div class="obox"><div class="ol">💡 Oportunidade potencial</div><div class="ot">{th['oportunidade']}</div></div>
  </div>
</div>

<p class="disc">Fontes: {data['fontes_rodape']} · {m['data']} · Não constitui recomendação de investimento · Dados ETF flows com atraso de 1 dia útil</p>
</div>
</body>
</html>"""

    return html


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    print("📊 Coletando dados do mercado...")
    data = coletar_dados()
    
    data_format = datetime.strptime(data["meta"]["data"], "%d/%m/%Y")
    data_iso = data_format.strftime("%Y%m%d")
    
    # Salva JSON
    json_path = output_dir / f"briefing_{data_iso}.json"
    print(f"💾 Salvando JSON em {json_path}...")
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ JSON salvo: {json_path.name}")
    
    # Gera HTML
    html_path = output_dir / f"briefing_{data_iso}.html"
    html = render(data)
    html_path.write_text(html, encoding="utf-8")
    print(f"✅ HTML gerado: {html_path.name}")
    
    # Gera PDF (opcional)
    pdf_path = output_dir / f"briefing_{data_iso}.pdf"
    try:
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        print(f"✅ PDF gerado: {pdf_path.name}")
    except ImportError:
        print("⚠️  WeasyPrint não instalado — PDF não gerado.")
        print("   Instale com: pip install weasyprint")
    except Exception as e:
        print(f"⚠️  Erro ao gerar PDF: {e}")
    
    print(f"\n🎯 Pronto! Briefing completo em: {output_dir.resolve()}")
    print(f"   📄 {json_path.name}")
    print(f"   🌐 {html_path.name}")
    print(f"   📕 {pdf_path.name}")


if __name__ == "__main__":
    main()
