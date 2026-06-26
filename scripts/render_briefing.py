"""
render_briefing.py
==================
Converte briefing_YYYYMMDD.json → briefing_YYYYMMDD.html

Tema escuro (modelo aprovado em 15/06/2026).
Consome o mesmo schema JSON definido em prompt_briefing.md.

Uso:
    python render_briefing.py output/briefing_20260615.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime


# ─── helpers de cor ──────────────────────────────────────────────────────────

# Mapeia as classes curtas do JSON (cg/cr/ca/cb e vg/va/vr) para HEX do tema.
COR = {
    "cg": "#16a34a", "cr": "#dc2626", "ca": "#d97706", "cb": "#3b82f6",
    "vg": "#16a34a", "va": "#d97706", "vr": "#dc2626",
}

def cor(classe: str, padrao: str = "#e2e8f0") -> str:
    return COR.get(classe, padrao)


def get_last_3_months() -> tuple:
    """
    Retorna os últimos 3 meses (mês-2, mês-1, mês-atual) capitalizados.
    Ex.: em junho/2026 → ("Abril", "Maio", "Junho")
    """
    meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
    }
    hoje = datetime.now()
    m = hoje.month
    m1 = m - 2 if m - 2 > 0 else m - 2 + 12
    m2 = m - 1 if m - 1 > 0 else m - 1 + 12
    return (meses[m1], meses[m2], meses[m])


# ─── cards genéricos (banco_central, trump, cripto, brasil) ──────────────────

def tag_html(t: dict) -> str:
    return f'<span class="tag {t.get("cor","tn")}">{t.get("texto","")}</span>'

def fonte_html(f: dict) -> str:
    return (f'<a href="{f.get("url","#")}" target="_blank" rel="noopener" '
            f'class="fonte-link">{f.get("nome","fonte")}</a>')

def card_html(item: dict) -> str:
    tags = "".join(tag_html(t) for t in item.get("tags", []))
    fontes = "".join(fonte_html(f) for f in item.get("fontes", []))
    tags_block = f'<div class="tags">{tags}</div>' if tags else ""
    fontes_block = f'<div class="fontes">{fontes}</div>' if fontes else ""
    return f"""
    <div class="card">
      <div class="card-header">
        <span class="card-icon">{item.get('icone','•')}</span>
        <div class="card-title-wrap">
          <span class="card-titulo">{item.get('titulo','')}</span>
          <span class="impacto-badge {item.get('impacto_classe','imp-m')}">{item.get('impacto','')}</span>
        </div>
      </div>
      <div class="card-corpo">{item.get('corpo','')}</div>
      {tags_block}
      {fontes_block}
    </div>"""

def cards_grid(items: list) -> str:
    if not items:
        return '<div class="cards-grid"></div>'
    return f'<div class="cards-grid">{"".join(card_html(i) for i in items)}</div>'


# ─── gráfico semanal (barras) ────────────────────────────────────────────────

def svg_semanal(g: dict) -> str:
    """
    Barras de fluxo diário. viewBox 304x145, linha do zero em y=62.
    Lê os campos já calculados no JSON (y, h, cor, valor, label_y, label_cor).
    """
    dias = g.get("dias", [])
    xs = [64, 112, 160, 208, 256]
    bars = ""
    labels = ""
    for i, d in enumerate(dias[:5]):
        x = xs[i] - 16
        y = d.get("y", 62)
        h = max(1, d.get("h", 1))
        c = d.get("cor", "#d1d5db")
        bars += f'<rect x="{x}" y="{y}" width="32" height="{h}" rx="3" fill="{c}"/>'
        val = d.get("valor", "")
        ly = d.get("label_y", 52)
        lc = d.get("label_cor", "#9ca3af")
        if val == "aguardando":
            bars += (f'<text x="{xs[i]}" y="{ly}" text-anchor="middle" '
                     f'font-size="7" fill="{lc}">—</text>')
        else:
            bars += (f'<text x="{xs[i]}" y="{ly}" text-anchor="middle" '
                     f'font-size="8" font-weight="600" fill="{lc}">{val}</text>')
        labels += (f'<text x="{xs[i]}" y="128" text-anchor="middle" '
                   f'font-size="7.5" fill="#6b7280">{d.get("data","")}</text>')

    return f"""<svg viewBox="0 0 304 145" width="100%" style="max-height:145px">
{bars}
<line x1="40" y1="62" x2="296" y2="62" stroke="#6b7280" stroke-width="0.8" stroke-dasharray="2,2"/>
<text x="36" y="14" text-anchor="end" font-size="7" fill="#9ca3af">{g.get('escala_max','')}</text>
<text x="36" y="36" text-anchor="end" font-size="7" fill="#9ca3af">{g.get('escala_meio','')}</text>
<text x="36" y="65" text-anchor="end" font-size="7" fill="#9ca3af">0</text>
<text x="36" y="95" text-anchor="end" font-size="7" fill="#9ca3af">{g.get('escala_neg','')}</text>
{labels}
</svg>"""


# ─── gráfico acumulado (linha) ───────────────────────────────────────────────

def svg_acumulado(meses: list) -> str:
    """
    Linha do acumulado mensal. viewBox 320x80.
    Aceita lista de {"label","acum"} em US$M.
    """
    if not meses:
        return '<svg viewBox="0 0 320 80" width="100%"></svg>'

    valores = [m.get("acum", 0) for m in meses]
    labels = [m.get("label", "") for m in meses]
    n = len(valores)

    vmax = max(valores)
    vmin = min(valores)
    rng = vmax - vmin if vmax != vmin else 1

    PAD_L, PAD_R, PAD_T, PAD_B = 40, 10, 8, 24
    W, H = 320, 80
    plot_w = W - PAD_L - PAD_R
    plot_h = H - PAD_T - PAD_B

    def x_of(i):
        return PAD_L + (i / (n - 1) * plot_w if n > 1 else 0)

    def y_of(v):
        return PAD_T + plot_h - (v - vmin) / rng * plot_h

    cor_linha = "#16a34a" if valores[-1] >= 0 else "#dc2626"

    pts = " ".join(f"{x_of(i):.1f},{y_of(v):.1f}" for i, v in enumerate(valores))
    poly = (f'<polyline points="{pts}" fill="none" stroke="{cor_linha}" '
            f'stroke-width="1.8" stroke-linejoin="round"/>')

    dots = ""
    for i, v in enumerate(valores):
        x = x_of(i)
        y = y_of(v)
        if abs(v) >= 1000:
            lbl = f"${v/1000:.1f}B" if v >= 0 else f"−${abs(v)/1000:.1f}B"
        else:
            lbl = f"${int(v)}M" if v >= 0 else f"−${int(abs(v))}M"
        ly = y - 4 if v >= 0 else y + 10
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="{cor_linha}"/>'
        dots += (f'<text x="{x:.1f}" y="{H-4}" text-anchor="middle" '
                 f'font-size="7" fill="#9ca3af">{labels[i]}</text>')
        dots += (f'<text x="{x:.1f}" y="{ly:.1f}" text-anchor="middle" '
                 f'font-size="6.5" fill="{cor_linha}" font-weight="600">{lbl}</text>')

    return f'<svg viewBox="0 0 320 80" width="100%" style="max-height:90px">{poly}{dots}</svg>'


# ─── seção ETF completa ──────────────────────────────────────────────────────

def etf_section(e: dict, ativo: str, periodo_sem: str) -> str:
    t = e.get("totais", {})
    mes_1, mes_2, mes_3 = get_last_3_months()

    svg_week = svg_semanal(e.get("grafico_semanal", {}))
    svg_area = svg_acumulado(e.get("grafico_acumulado", {}).get("meses", []))

    tot = f"""<div class="tot-grid">
<div class="tot-row"><span class="tot-label">Semanal</span><span class="tot-val" style="color:{cor(t.get('semanal_cor'))}">{t.get('semanal_val','')}</span><span class="tot-sub">{t.get('semanal_sub','')}</span></div>
<div class="tot-row"><span class="tot-label">YTD</span><span class="tot-val" style="color:{cor(t.get('ytd_cor'))}">{t.get('ytd_val','')}</span><span class="tot-sub">{t.get('ytd_sub','')}</span></div>
<div class="tot-row"><span class="tot-label">Acumulado</span><span class="tot-val" style="color:{cor(t.get('acum_cor'))}">{t.get('acum_val','')}</span><span class="tot-sub">{t.get('acum_sub','')}</span></div>
<div class="tot-row"><span class="tot-label">{mes_3}/26</span><span class="tot-val" style="color:{cor(t.get('mes_3_cor'))}">{t.get('mes_3_val','')}</span><span class="tot-sub"></span></div>
<div class="tot-row"><span class="tot-label">{mes_2}/26</span><span class="tot-val" style="color:{cor(t.get('mes_2_cor'))}">{t.get('mes_2_val','')}</span><span class="tot-sub"></span></div>
<div class="tot-row"><span class="tot-label">{mes_1}/26</span><span class="tot-val" style="color:{cor(t.get('mes_1_cor'))}">{t.get('mes_1_val','')}</span><span class="tot-sub"></span></div>
</div>"""

    analise = e.get("analise", "")
    nota_acum = e.get("grafico_acumulado_analise", "")

    return f"""
    <div class="etf-section">
      <div class="etf-header">
        <h3 class="etf-title">ETF {ativo} — Spot US</h3>
        <span class="ytd-badge {e.get('ytd_classe','imp-m')}">{e.get('ytd_label','')}</span>
      </div>
      <div class="etf-grid">
        <div class="etf-col">
          <div class="chart-label">Fluxo Semanal ({periodo_sem})</div>
          {svg_week}
        </div>
        <div class="etf-col">
          <div class="chart-label">Acumulado Mensal</div>
          {svg_area}
          <div class="acum-nota">{nota_acum}</div>
        </div>
      </div>
      {tot}
      <div class="etf-analise">{analise}</div>
    </div>"""


# ─── calendário ──────────────────────────────────────────────────────────────

def calendario_html(cal: dict) -> str:
    destaques = ""
    for d in cal.get("destaques", []):
        data = f'<span class="dest-data">{d.get("data","")}</span>' if d.get("data") else ""
        destaques += (f'<div class="dest-item"><span class="dest-icon" '
                      f'style="color:{d.get("cor","#94a3b8")}">{d.get("valor","")}</span>'
                      f'<span class="dest-label">{d.get("label","")}</span>{data}</div>')

    hoje = cal.get("hoje", {})
    empresas = hoje.get("empresas", [])
    if empresas:
        linhas = ""
        for e in empresas:
            linhas += (f'<div class="prox-row"><span class="prox-data">{e.get("horario","")}</span>'
                       f'<span class="imp-dot {e.get("impacto_dot","dm")}"></span>'
                       f'<span class="prox-nome">{e.get("ticker","")} · {e.get("empresa","")}</span>'
                       f'<span class="prox-exp">{e.get("expectativa","")}</span></div>')
        hoje_body = linhas
    else:
        hoje_body = '<div class="emp-empty">Nenhum resultado relevante hoje</div>'

    prox = ""
    for p in cal.get("proximas", []):
        prox += (f'<div class="prox-row"><span class="prox-data">{p.get("data","")}</span>'
                 f'<span class="imp-dot {p.get("impacto_dot","dm")}"></span>'
                 f'<span class="prox-nome">{p.get("empresa","")}</span>'
                 f'<span class="prox-exp">{p.get("expectativa","")}</span></div>')

    return f"""
    <div class="calendario-section">
      <h3 class="section-title">📅 Calendário — {cal.get('periodo','')}</h3>
      <div class="fase-badge">{cal.get('fase','')}</div>
      <div class="destaques-grid">{destaques}</div>
      <div class="hoje-box">
        <div class="hoje-label">{hoje.get('dia_label','Hoje')}</div>
        {hoje_body}
      </div>
      <div class="proximas-box">
        <div class="prox-title">Próximos eventos</div>
        {prox}
      </div>
    </div>"""


# ─── termômetro ──────────────────────────────────────────────────────────────

def termometro_html(th: dict) -> str:
    return f"""
    <div class="termometro-section">
      <h3 class="section-title">🌡️ Termômetro do Dia — {th.get('data_completa','')}</h3>
      <div class="termo-grid">
        <div class="termo-row"><span class="termo-label">Cripto</span><span class="termo-val" style="color:{cor(th.get('cripto_cor'))}">{th.get('cripto_val','')}</span><span class="termo-sub">{th.get('cripto_sub','')}</span></div>
        <div class="termo-row"><span class="termo-label">B3</span><span class="termo-val" style="color:{cor(th.get('b3_cor'))}">{th.get('b3_val','')}</span><span class="termo-sub">{th.get('b3_sub','')}</span></div>
        <div class="termo-row"><span class="termo-label">Dólar</span><span class="termo-val" style="color:{cor(th.get('dolar_cor'))}">{th.get('dolar_val','')}</span><span class="termo-sub">{th.get('dolar_sub','')}</span></div>
        <div class="termo-row"><span class="termo-label">Brent</span><span class="termo-val" style="color:{cor(th.get('brent_cor'))}">{th.get('brent_val','')}</span><span class="termo-sub">{th.get('brent_sub','')}</span></div>
      </div>
      <div class="atencao-box"><span class="atencao-icon">⚠️</span> <strong>Atenção:</strong> {th.get('atencao','')}</div>
      <div class="oportunidade-box"><span class="op-icon">💡</span> <strong>Insight do Analista:</strong> {th.get('oportunidade','')}</div>
    </div>"""


# ─── macro bar (com Fear & Greed circular) ───────────────────────────────────

def macro_bar_html(mb: dict) -> str:
    fg = mb.get("fear_greed", {})
    fg_cor = fg.get("cor", "#6b7280")
    fg_val = fg.get("valor", "N/D")
    fg_sent = fg.get("sentimento", "dado não disponível")

    return f"""
    <div class="macro-bar">
      <div class="macro-item">
        <span class="macro-icon">₿</span>
        <div>
          <div class="macro-price" style="color:{cor(mb.get('btc_cor'))}">{mb.get('btc_preco','')}</div>
          <div class="macro-sub" style="color:{cor(mb.get('btc_cor'))}">{mb.get('btc_var','')}</div>
        </div>
      </div>
      <div class="macro-item">
        <span class="macro-icon">Ξ</span>
        <div>
          <div class="macro-price" style="color:{cor(mb.get('eth_cor'))}">{mb.get('eth_preco','')}</div>
          <div class="macro-sub" style="color:{cor(mb.get('eth_cor'))}">{mb.get('eth_var','')}</div>
        </div>
      </div>
      <div class="macro-item">
        <span class="macro-icon">💵</span>
        <div>
          <div class="macro-price">{mb.get('dolar','')}</div>
          <div class="macro-sub">{mb.get('dolar_sub','')}</div>
        </div>
      </div>
      <div class="macro-item">
        <span class="macro-icon">🛢️</span>
        <div>
          <div class="macro-price" style="color:{cor(mb.get('brent_cor'))}">{mb.get('brent','')}</div>
          <div class="macro-sub">{mb.get('brent_var','')}</div>
        </div>
      </div>
      <div class="macro-item macro-fg">
        <div class="fg-circle" style="border-color:{fg_cor}; color:{fg_cor}">{fg_val}</div>
        <div>
          <div class="macro-price" style="color:{fg_cor}">{fg_sent}</div>
          <div class="macro-sub">Fear &amp; Greed</div>
        </div>
      </div>
    </div>"""


# ─── CSS (tema escuro, modelo 15/06) ─────────────────────────────────────────

CSS = """
    :root {
      --bg: #0f1117; --bg2: #1a1d27; --bg3: #22263a; --border: #2d3148;
      --text: #e2e8f0; --text2: #94a3b8;
      --green: #16a34a; --red: #dc2626; --yellow: #d97706; --blue: #3b82f6; --accent: #6366f1;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: var(--bg); color: var(--text); font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; line-height: 1.5; }
    a { color: var(--blue); text-decoration: none; }
    a:hover { text-decoration: underline; }

    .header { background: linear-gradient(135deg, #1e1b4b 0%, #0f1117 100%); padding: 24px 32px; border-bottom: 1px solid var(--border); }
    .header-top { display: flex; align-items: center; justify-content: space-between; }
    .header-title { font-size: 22px; font-weight: 700; color: #a5b4fc; letter-spacing: -0.3px; }
    .header-sub { font-size: 13px; color: var(--text2); margin-top: 4px; }
    .header-badge { background: #1e293b; border: 1px solid var(--border); border-radius: 20px; padding: 4px 14px; font-size: 12px; color: var(--text2); }

    .macro-bar { display: flex; gap: 0; border-bottom: 1px solid var(--border); background: var(--bg2); }
    .macro-item { display: flex; align-items: center; gap: 10px; padding: 14px 20px; border-right: 1px solid var(--border); flex: 1; }
    .macro-item:last-child { border-right: none; }
    .macro-icon { font-size: 18px; }
    .macro-price { font-size: 15px; font-weight: 700; }
    .macro-sub { font-size: 11px; color: var(--text2); margin-top: 1px; }
    .macro-fg { min-width: 160px; }
    .fg-circle { width: 44px; height: 44px; border-radius: 50%; border: 3px solid; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 800; flex-shrink: 0; }

    .main { max-width: 1200px; margin: 0 auto; padding: 24px 20px; }
    .section-title { font-size: 15px; font-weight: 700; color: #a5b4fc; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
    .section { margin-bottom: 32px; }

    .cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 14px; }
    .card { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 16px; transition: border-color .2s; }
    .card:hover { border-color: var(--accent); }
    .card-header { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 10px; }
    .card-icon { font-size: 22px; flex-shrink: 0; margin-top: 2px; }
    .card-title-wrap { display: flex; align-items: flex-start; gap: 8px; flex-wrap: wrap; }
    .card-titulo { font-size: 13px; font-weight: 600; line-height: 1.4; flex: 1; min-width: 180px; }
    .card-corpo { font-size: 12.5px; color: #cbd5e1; line-height: 1.65; }
    .card-corpo strong { color: #e2e8f0; }
    .divr { margin: 10px 0 4px; border-top: 1px solid var(--border); }

    .impacto-badge { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 12px; white-space: nowrap; flex-shrink: 0; }
    .imp-h { background: #7f1d1d; color: #fca5a5; }
    .imp-m { background: #78350f; color: #fcd34d; }
    .imp-p { background: #14532d; color: #86efac; }

    .tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
    .tag { font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 600; }
    .tg { background: #14532d; color: #86efac; }
    .tr { background: #7f1d1d; color: #fca5a5; }
    .tn { background: #1e293b; color: #94a3b8; border: 1px solid var(--border); }

    .fontes { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--border); }
    .fonte-link { font-size: 10px; color: var(--text2); background: var(--bg3); padding: 2px 8px; border-radius: 8px; border: 1px solid var(--border); }
    .fonte-link:hover { color: var(--blue); border-color: var(--blue); text-decoration: none; }

    .etf-section { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 18px; margin-bottom: 16px; }
    .etf-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
    .etf-title { font-size: 14px; font-weight: 700; color: #a5b4fc; }
    .ytd-badge { font-size: 12px; font-weight: 700; padding: 3px 12px; border-radius: 12px; }
    .etf-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 16px; }
    .chart-label { font-size: 11px; color: var(--text2); margin-bottom: 6px; font-weight: 600; }
    .acum-nota { font-size: 10.5px; color: #d97706; margin-top: 4px; text-align: center; }
    .tot-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 14px; }
    .tot-row { background: var(--bg3); border-radius: 8px; padding: 10px 12px; }
    .tot-label { display: block; font-size: 10px; color: var(--text2); margin-bottom: 2px; }
    .tot-val { display: block; font-size: 14px; font-weight: 700; }
    .tot-sub { display: block; font-size: 9px; color: var(--text2); margin-top: 2px; }
    .etf-analise { font-size: 12px; color: #cbd5e1; line-height: 1.65; background: var(--bg3); border-radius: 8px; padding: 12px 14px; border-left: 3px solid var(--accent); }

    .calendario-section { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 18px; }
    .fase-badge { display: inline-block; font-size: 11px; background: var(--bg3); border: 1px solid var(--border); border-radius: 20px; padding: 3px 12px; color: var(--text2); margin-bottom: 14px; }
    .destaques-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-bottom: 16px; }
    .dest-item { background: var(--bg3); border-radius: 8px; padding: 10px 12px; display: flex; align-items: center; gap: 8px; }
    .dest-icon { font-size: 18px; }
    .dest-label { font-size: 12px; font-weight: 600; flex: 1; }
    .dest-data { font-size: 10px; color: var(--text2); white-space: nowrap; }
    .hoje-box, .proximas-box { background: var(--bg3); border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; }
    .hoje-label, .prox-title { font-size: 11px; font-weight: 700; color: var(--text2); margin-bottom: 8px; text-transform: uppercase; letter-spacing: .5px; }
    .emp-empty { font-size: 12px; color: var(--text2); font-style: italic; }
    .prox-row { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 12px; }
    .prox-row:last-child { border-bottom: none; }
    .prox-data { font-size: 10px; color: var(--text2); min-width: 36px; }
    .prox-nome { font-weight: 600; flex: 1; }
    .prox-exp { font-size: 11px; color: var(--text2); }
    .imp-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
    .da { background: var(--red); }
    .dm { background: var(--yellow); }
    .db { background: #4b5563; }

    .termometro-section { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 18px; }
    .termo-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 14px; }
    .termo-row { background: var(--bg3); border-radius: 8px; padding: 12px 14px; }
    .termo-label { display: block; font-size: 10px; color: var(--text2); margin-bottom: 3px; text-transform: uppercase; letter-spacing: .4px; }
    .termo-val { display: block; font-size: 14px; font-weight: 700; margin-bottom: 4px; }
    .termo-sub { display: block; font-size: 11px; color: #94a3b8; }
    .atencao-box { background: #1c1917; border: 1px solid #78350f; border-radius: 8px; padding: 10px 14px; margin-bottom: 10px; font-size: 12.5px; color: #fcd34d; }
    .atencao-icon { margin-right: 4px; }
    .oportunidade-box { background: #0c1a2e; border: 1px solid #1d4ed8; border-radius: 8px; padding: 10px 14px; font-size: 12.5px; color: #93c5fd; }
    .op-icon { margin-right: 4px; }

    .footer { background: var(--bg2); border-top: 1px solid var(--border); padding: 16px 32px; text-align: center; font-size: 11px; color: var(--text2); }

    @media (max-width: 768px) {
      .macro-bar { flex-wrap: wrap; }
      .macro-item { flex: 1 1 45%; border-right: none; border-bottom: 1px solid var(--border); }
      .etf-grid { grid-template-columns: 1fr; }
      .tot-grid { grid-template-columns: repeat(2, 1fr); }
      .termo-grid { grid-template-columns: 1fr; }
      .header { padding: 16px; }
    }
"""


# ─── render principal ────────────────────────────────────────────────────────

def render(data: dict) -> str:
    m = data.get("meta", {})
    mb = data.get("macro_bar", {})
    cal = data.get("calendario", {})
    th = data.get("termometro", {})

    # período semanal para rótulo dos gráficos ETF (usa o semanal_sub do BTC)
    periodo_sem = (data.get("etf_btc", {}).get("totais", {})
                   .get("semanal_sub", "").replace("semana de ", ""))

    gerado = m.get("gerado_em", "")
    gerado_txt = f" · Gerado às {gerado}" if gerado else ""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Briefing Financeiro — {m.get('data','')}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="header">
  <div class="header-top">
    <div>
      <div class="header-title">📊 Briefing Financeiro Diário</div>
      <div class="header-sub">{m.get('dia_semana','')}, {m.get('data','')}{gerado_txt}</div>
    </div>
    <div class="header-badge">Economista Sênior · Análise de Mercado</div>
  </div>
</div>

{macro_bar_html(mb)}

<div class="main">

  <div class="section">
    <div class="section-title">🏦 Banco Central &amp; Macro</div>
    {cards_grid(data.get('banco_central', []))}
  </div>

  <div class="section">
    <div class="section-title">🇺🇸 Trump &amp; Macro Global</div>
    {cards_grid(data.get('trump_macro', []))}
  </div>

  <div class="section">
    <div class="section-title">₿ Cripto — Top Notícias</div>
    {cards_grid(data.get('cripto_top3', []))}
  </div>

  <div class="section">
    <div class="section-title">📊 ETF Flows — Spot Bitcoin</div>
    {etf_section(data.get('etf_btc', {}), 'BTC', periodo_sem)}
  </div>

  <div class="section">
    <div class="section-title">📊 ETF Flows — Spot Ethereum</div>
    {etf_section(data.get('etf_eth', {}), 'ETH', periodo_sem)}
  </div>

  <div class="section">
    <div class="section-title">🇧🇷 Brasil — Destaques</div>
    {cards_grid(data.get('brasil_top2', []))}
  </div>

  <div class="section">
    {calendario_html(cal)}
  </div>

  <div class="section">
    {termometro_html(th)}
  </div>

</div>

<div class="footer">
  <strong>Fontes:</strong> {data.get('fontes_rodape','')}<br>
  Gerado automaticamente por Briefing Engine · {m.get('data','')}{gerado_txt}
</div>
</body>
</html>"""


# ─── main ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Uso: python render_briefing.py output/briefing_YYYYMMDD.json")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"Arquivo não encontrado: {json_path}")
        sys.exit(1)

    print(f"📂 Lendo {json_path.name}...")
    data = json.loads(json_path.read_text(encoding="utf-8"))

    html_path = json_path.with_suffix(".html")
    html_path.write_text(render(data), encoding="utf-8")
    print(f"✅ HTML gerado: {html_path.name}")
    print(f"\n🎯 Pronto! Arquivo em: {json_path.parent.resolve()}")


if __name__ == "__main__":
    main()
