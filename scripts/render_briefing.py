"""
render_briefing.py
==================
Converte briefing_YYYYMMDD.json → briefing_YYYYMMDD.html + .pdf

Uso:
    python render_briefing.py briefing_20260512.json

Dependências:
    pip install weasyprint
"""

import json
import sys
import re
from pathlib import Path
from datetime import date


# ─── helpers ─────────────────────────────────────────────────────────────────

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


def render_fear_greed(fg: dict) -> str:
    """Renderiza barra visual de Fear & Greed Index"""
    valor = int(fg["valor"])
    # Posição percentual na barra (0-100)
    posicao = max(0, min(100, valor))
    
    return f"""
<div class="fg-bar">
  <div class="fg-label">😨 Fear & Greed Index</div>
  <div class="fg-container">
    <div class="fg-track">
      <div class="fg-fill"></div>
      <div class="fg-indicator" style="left:{posicao}%"></div>
    </div>
    <div class="fg-value">{valor}</div>
  </div>
  <div class="fg-legend">
    <div class="fg-legend-item">Extremo<br>Medo</div>
    <div class="fg-legend-item">Medo</div>
    <div class="fg-legend-item">Neutro</div>
    <div class="fg-legend-item">Ganância</div>
    <div class="fg-legend-item">Extrema<br>Ganância</div>
  </div>
  <div style="font-size:11px;color:#52525b;margin-top:.5rem;text-align:center"><strong>{fg["sentimento"]}</strong></div>
</div>"""



# ─── gráfico SVG semanal ─────────────────────────────────────────────────────

def svg_semanal(g: dict) -> str:
    xs = [89, 177, 265, 353, 441]
    bars = ""
    labels_x = ""
    for i, d in enumerate(g["dias"]):
        x = xs[i] - 34
        bars += f'<rect x="{x}" y="{d["y"]}" width="68" height="{d["h"]}" fill="{d["cor"]}" rx="3"/>\n'
        # label do valor
        ly = d["label_y"]
        lc = d["label_cor"]
        val = d["valor"]
        if val == "aguardando":
            bars += f'<text x="{xs[i]}" y="{ly}" font-size="7" fill="{lc}" text-anchor="middle">{d["data"].split(" ")[0]}</text>\n'
            bars += f'<text x="{xs[i]}" y="{int(ly)+14}" font-size="6.5" fill="{lc}" text-anchor="middle">aguardando</text>\n'
        else:
            bars += f'<text x="{xs[i]}" y="{ly}" font-size="8" fill="{lc}" text-anchor="middle" font-weight="700">{val}</text>\n'
        # labels_x ajustados para não sobrepor
        labels_x += f'<text x="{xs[i]}" y="107" font-size="6" fill="#71717a" text-anchor="middle">{d["data"]}</text>\n'

    return f"""
<svg viewBox="0 0 560 115" xmlns="http://www.w3.org/2000/svg">
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


# ─── gráfico SVG área acumulada ──────────────────────────────────────────────

def svg_acumulado(meses: list, ativo: str) -> str:
    """
    Gera gráfico de área acumulada estilo Farside.
    Valores em US$M. Positivo = azul escuro. Negativo = vermelho.
    """
    valores = [m["acum"] for m in meses]
    labels  = [m["label"] for m in meses]
    n = len(valores)

    vmax = max(valores)
    vmin = min(valores)
    rng  = vmax - vmin if vmax != vmin else 1

    W, H = 520, 105
    PAD_L, PAD_R, PAD_T, PAD_B = 52, 10, 8, 23

    plot_w = W - PAD_L - PAD_R
    plot_h = H - PAD_T - PAD_B

    # normaliza: y cresce para baixo
    def px(v):
        return PAD_T + plot_h - int((v - vmin) / rng * plot_h)

    zero_y = px(0)
    # Clamp zero_y dentro do plot para evitar overflow quando todos os valores
    # são positivos (BTC) ou todos negativos (ETH)
    zero_y_clamped = max(PAD_T, min(PAD_T + plot_h, zero_y))

    # pontos da linha
    pts = []
    for i, v in enumerate(valores):
        x = PAD_L + int(i / (n - 1) * plot_w)
        y = px(v)
        pts.append((x, y))

    # path da área (fecha pelo zero — sempre dentro do viewBox)
    path_pts = " ".join(f"{x},{y}" for x, y in pts)
    x_start = pts[0][0]
    x_end   = pts[-1][0]

    cor_area  = "#1d4ed8" if valores[-1] >= 0 else "#dc2626"
    cor_linha = "#1e3a8a" if valores[-1] >= 0 else "#b91c1c"
    cor_area_opacity = "0.18"

    area_path = (
        f"M{x_start},{zero_y_clamped} "
        + " ".join(f"L{x},{y}" for x, y in pts)
        + f" L{x_end},{zero_y_clamped} Z"
    )
    line_path = "M" + " L".join(f"{x},{y}" for x, y in pts)

    # labels eixo X — mostrar a cada ~4-6 meses para não sobrepor
    step = max(1, n // 5)
    x_labels = ""
    for i in range(0, n, step):
        x = PAD_L + int(i / (n - 1) * plot_w)
        x_labels += f'<text x="{x}" y="{H - 1}" font-size="6" fill="#a1a1aa" text-anchor="middle">{labels[i]}</text>\n'

    # labels eixo Y
    y_vals = [vmax, (vmax + vmin) / 2, vmin]
    y_labels = ""
    for v in y_vals:
        y = px(v)
        label = f"${int(v/1000)}B" if abs(v) >= 1000 else f"${int(v)}M"
        if v < 0:
            label = f"−${int(abs(v)/1000)}B" if abs(v) >= 1000 else f"−${int(abs(v))}M"
        y_labels += f'<text x="{PAD_L - 4}" y="{y + 3}" font-size="6.5" fill="#a1a1aa" text-anchor="end">{label}</text>\n'

    # linha do zero (se dentro do range)
    zero_line = ""
    if vmin < 0 < vmax:
        zero_line = f'<line x1="{PAD_L}" y1="{zero_y}" x2="{W - PAD_R}" y2="{zero_y}" stroke="#94a3b8" stroke-width="0.5" stroke-dasharray="2,2"/>'

    # grid horizontal sutil
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


# ─── card ETF completo ────────────────────────────────────────────────────────

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

  <!-- 6 totalizadores: linha 1 -->
  <div class="tots">
    <div class="tot"><div class="tl">📅 Semanal</div><div class="tv {t['semanal_cor']}">{t['semanal_val']}</div><div class="ts">{t['semanal_sub']}</div></div>
    <div class="tot"><div class="tl">📊 YTD 2026</div><div class="tv {t['ytd_cor']}">{t['ytd_val']}</div><div class="ts">{t['ytd_sub']}</div></div>
    <div class="tot"><div class="tl">🏦 Acumulado total</div><div class="tv {t['acum_cor']}">{t['acum_val']}</div><div class="ts">{t['acum_sub']}</div></div>
  </div>

  <!-- linha 2: últimos 3 meses -->
  <div class="tots" style="margin-top:.25rem">
    <div class="tot"><div class="tl">📆 Maio acum.</div><div class="tv {t['maio_cor']}" style="font-size:14px">{t['maio_val']}</div></div>
    <div class="tot"><div class="tl">📆 Abril acum.</div><div class="tv {t['abril_cor']}" style="font-size:14px">{t['abril_val']}</div></div>
    <div class="tot"><div class="tl">📆 Março acum.</div><div class="tv {t['marco_cor']}" style="font-size:14px">{t['marco_val']}</div></div>
  </div>

  <!-- gráfico semanal -->
  <div class="clbl" style="margin-top:.625rem">Fluxo diário — semana atual</div>
  <div class="leg">
    <div class="li"><div class="lsq" style="background:#16a34a"></div>Entrada</div>
    <div class="li"><div class="lsq" style="background:#dc2626"></div>Saída</div>
    <div class="li"><div class="lsq" style="background:#d1d5db"></div>Aguardando</div>
  </div>
  <div class="ch">{svg_week}</div>

  <!-- gráfico acumulado estilo Farside -->
  <div class="clbl" style="margin-top:.5rem">Fluxo acumulado histórico (US$M) — estilo Farside</div>
  <div style="height:113px;margin-bottom:.375rem">{svg_area}</div>
  <div class="an" style="margin-bottom:.5rem"><strong>Leitura:</strong> {e['analise']} {e['grafico_acumulado_analise']}</div>

  <!-- botão Farside -->
  <a href="{farside_url}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:600;color:#1d4ed8;background:#eff6ff;border:1px solid #bfdbfe;border-radius:20px;padding:4px 12px;text-decoration:none;margin-bottom:.375rem">
    📊 Ver gráfico completo — Farside ↗
  </a>

  <div class="meta">
    <a class="src" href="https://www.coinglass.com/etf/{'bitcoin' if ativo=='BTC' else 'ethereum'}" target="_blank">CoinGlass ↗</a>
    <a class="src" href="{farside_url}" target="_blank">Farside ↗</a>
    <a class="src" href="https://x.com/DocumentingBTC" target="_blank">𝕏 @DocumentingBTC</a>
  </div>
</div>"""


# ─── calendário ──────────────────────────────────────────────────────────────

def render_calendario(cal: dict) -> str:
    destaques_html = ""
    for d in cal["destaques"]:
        destaques_html += f'<div class="si"><div class="sn" style="color:{d["cor"]}">{d["valor"]}</div><div class="sl2">{d["label"]}<br>{d["data"]}</div></div>'

    # tabela hoje
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

    # tabela próximas
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


# ─── CSS ─────────────────────────────────────────────────────────────────────

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
.fg-bar{background:#fff;border:1px solid #e4e4e7;border-radius:10px;padding:.75rem 1rem;margin-bottom:.5rem}
.fg-label{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#71717a;margin-bottom:.5rem}
.fg-container{display:flex;align-items:center;gap:.75rem;margin-bottom:.375rem}
.fg-track{flex:1;height:24px;background:#f4f4f5;border-radius:6px;position:relative;overflow:hidden;border:1px solid #e4e4e7}
.fg-fill{height:100%;background:linear-gradient(90deg,#d32f2f,#ff6f00,#ffc107,#66bb6a,#2e7d32);width:100%}
.fg-indicator{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:3px;height:28px;background:#18181b;border-radius:2px;z-index:10}
.fg-value{font-size:18px;font-weight:800;min-width:45px;text-align:center;color:#18181b}
.fg-legend{display:flex;justify-content:space-between;font-size:8px;color:#a1a1aa;font-weight:600;margin-top:.375rem}
.fg-legend-item{text-align:center;flex:1}
@media print{body{background:#fff;padding:0}.w{max-width:100%}.card,.tw,.thm,.mi,.si,.tot{break-inside:avoid}}
"""


# ─── render principal ─────────────────────────────────────────────────────────

def render(data: dict) -> str:
    m   = data["meta"]
    mb  = data["macro_bar"]
    th  = data["termometro"]
    cal = data["calendario"]

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

<div class="sec"><div class="sl">🏦 Bancos Centrais</div>{card_section(data['banco_central'])}</div>
<div class="sec"><div class="sl">🇺🇸 Macro Global & Declarações do Presidente dos EUA</div>{card_section(data['trump_macro'])}</div>
<div class="sec"><div class="sl">₿ Top 3 — Cripto</div>{card_section(data['cripto_top3'])}</div>

<div class="sec">{render_fear_greed(data['macro_bar']['fear_greed'])}</div>

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


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Uso: python render_briefing.py briefing_YYYYMMDD.json")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"Arquivo não encontrado: {json_path}")
        sys.exit(1)

    print(f"📂 Lendo {json_path.name}...")
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # Gera HTML
    html_path = json_path.with_suffix(".html")
    html = render(data)
    html_path.write_text(html, encoding="utf-8")
    print(f"✅ HTML gerado: {html_path.name}")

    # Gera PDF
    pdf_path = json_path.with_suffix(".pdf")
    try:
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        print(f"✅ PDF gerado:  {pdf_path.name}")
    except ImportError:
        print("⚠️  WeasyPrint não instalado — PDF não gerado.")
        print("   Instale com: pip install weasyprint")

    print(f"\n🎯 Pronto! Arquivos em: {json_path.parent.resolve()}")


if __name__ == "__main__":
    main()
