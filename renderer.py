"""
renderer.py — Gera HTML de email compatível com Outlook (table-based).

Suporte a:
  - Banner como imagem uploadada (base64) ou cor sólida
  - Faixa de degradê editável
  - Markdown completo no corpo (negrito, itálico, listas, colunas, citações…)
  - Rodapé editável com 1 ou 2 colunas + links Markdown
  - 100% inline styles — sem classes, sem CSS externo (Outlook-safe)
"""

from __future__ import annotations
import datetime
from parser import (
    parse_markdown, parse_footer_markdown,
    TextBlock, ImageBlock, QuoteBlock, ListBlock, TableBlock, DividerBlock,
)

MONTHS_PT = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


# ── Data ──────────────────────────────────────────────────────────────────────

def _fmt_date(fmt: str) -> str:
    t = datetime.date.today()
    if fmt == "ddmmyyyy": return t.strftime("%d/%m/%Y")
    if fmt == "precisa":  return f"{MONTHS_PT[t.month].capitalize()} de {t.year}"
    return f"{t.day} de {MONTHS_PT[t.month]} de {t.year}"


# ── Renderizadores de bloco ───────────────────────────────────────────────────

def _r_text(b: TextBlock, font: str, size: str, lh: str, color: str) -> str:
    align = "center" if b.align == "center" else "left"
    return (
        f'<p style="margin:0 0 8px;font-size:{size}px;line-height:{lh};'
        f'color:{color};font-family:{font};text-align:{align}">{b.text}</p>'
    )

def _r_image(b: ImageBlock) -> str:
    return (
        f'<div style="margin:10px 0 14px">'
        f'<img src="{b.url}" alt="{b.alt}" '
        f'style="max-width:100%;height:auto;display:block;border-radius:4px" /></div>'
    )

def _r_quote(b: QuoteBlock, accent: str, font: str) -> str:
    return (
        f'<table cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;margin:10px 0 14px">'
        f'<tr><td style="width:4px;background:{accent};border-radius:2px">&nbsp;</td>'
        f'<td style="padding:8px 14px;font-style:italic;font-size:13px;'
        f'color:#555;font-family:{font}">{b.text}</td></tr></table>'
    )

def _r_list(b: ListBlock, font: str, size: str, color: str) -> str:
    tag = "ol" if b.ordered else "ul"
    style = (
        f'style="margin:6px 0 12px;padding-left:22px;font-size:{size}px;'
        f'line-height:1.7;color:{color};font-family:{font}"'
    )
    items = "".join(f'<li style="margin-bottom:4px">{item}</li>' for item in b.items)
    return f'<{tag} {style}>{items}</{tag}>'

def _temp_color(val_str: str) -> str:
    """Cor de temperatura baseada no valor numérico do score."""
    try:
        v = float(val_str)
        if   v >=  0.5: return "#1a7a4a"   # verde escuro — forte oportunidade
        elif v >=  0.1: return "#5aaa72"   # verde claro
        elif v >= -0.1: return "#888"      # neutro
        elif v >= -0.5: return "#d4734a"   # laranja — risco moderado
        else:           return "#b03030"   # vermelho — risco alto
    except (ValueError, TypeError):
        return "#3a3530"


def _r_table(b: TableBlock, font: str, size: str, color: str, accent: str, highlight: str,
             table_header_bg: str = "", use_temp_colors: bool = True) -> str:
    if not table_header_bg:
        table_header_bg = accent

    ncols  = max(len(b.headers) if b.headers else 0,
                 max((len(r) for r in b.rows), default=0))
    aligns = (b.aligns + ["left"] * ncols)[:ncols]

    wide  = ncols >= 4
    fs    = str(int(size) - 2) if wide else size
    pad_h = "5px 8px"  if wide else "7px 10px"
    pad_d = "5px 8px"  if wide else "6px 10px"

    def _align(ci): return aligns[ci] if ci < len(aligns) else "left"

    # ── Ordena grupos de evento pelo score (col -1 da linha do evento) ─────────
    rows = b.rows[:]
    if rows:
        # Separa grupos: cada grupo = [linha_evento, *dims]
        groups, current = [], []
        for row in rows:
            r = (row + [""] * ncols)[:ncols]
            if r[0] != "":
                if current: groups.append(current)
                current = [r]
            else:
                current.append(r)
        if current: groups.append(current)

        # Ordena: score negativo primeiro (maior risco), positivo por último
        def _score(g):
            try:    return float(g[0][-1])
            except: return 0.0
        groups.sort(key=_score)

        # Reconstrói rows ordenados
        rows = [r for g in groups for r in g]
    else:
        groups = []

    # ── Cor de texto adaptativa ao fundo ──────────────────────────────────────
    def _contrast(hex_color: str) -> str:
        """Retorna #fff ou #111 dependendo da luminância do fundo."""
        h = hex_color.lstrip("#")
        if len(h) != 6:
            return "#fff"
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        # Luminância relativa (fórmula WCAG)
        lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#111" if lum > 0.55 else "#fff"

    th_fg        = _contrast(table_header_bg)
    ev_fg        = _contrast(highlight)
    th_sep       = f"rgba(0,0,0,.12)" if th_fg == "#111" else "rgba(255,255,255,.15)"
    ev_sep       = f"rgba(0,0,0,.12)" if ev_fg == "#111" else "rgba(255,255,255,.2)"

    # ── Estilos ────────────────────────────────────────────────────────────────
    th_style = (
        f"background:{table_header_bg};color:{th_fg};font-family:{font};"
        f"font-size:{fs}px;font-weight:700;letter-spacing:.03em;"
        f"padding:{pad_h};border-right:1px solid {th_sep};text-align:{{align}}"
    )
    td_event_first = (
        f"background:{highlight};color:{ev_fg};font-family:{font};"
        f"font-size:{fs}px;font-weight:700;"
        f"padding:{pad_h};border-bottom:1px solid {ev_sep};"
        f"border-right:1px solid {ev_sep};vertical-align:middle"
    )
    td_event_score = (
        f"background:{highlight};color:{ev_fg};font-family:{font};"
        f"font-size:{fs}px;font-weight:700;text-align:right;"
        f"padding:{pad_h};border-bottom:1px solid {ev_sep};vertical-align:middle"
    )
    td_event_empty = (
        f"background:{highlight};padding:{pad_h};"
        f"border-bottom:1px solid {ev_sep};"
        f"border-right:1px solid {ev_sep}"
    )
    td_dim = (
        f"font-family:{font};font-size:{fs}px;color:{color};"
        f"padding:{pad_d};border-bottom:1px solid #e8e3dc;"
        f"border-right:1px solid #ede8e1;vertical-align:middle;text-align:{{align}}"
    )
    td_arrow = (
        f"font-family:{font};font-size:{fs}px;color:#aaa;"
        f"padding:{pad_d};padding-left:12px;"
        f"border-bottom:1px solid #e8e3dc;"
        f"border-right:1px solid #ede8e1;vertical-align:middle;text-align:center"
    )
    td_dim_name = (
        f"font-family:{font};font-size:{fs}px;color:{color};"
        f"padding:{pad_d};"
        f"border-bottom:1px solid #e8e3dc;"
        f"border-right:1px solid #ede8e1;vertical-align:middle"
    )

    # ── Cabeçalho ──────────────────────────────────────────────────────────────
    header_html = ""
    if b.headers:
        cells = "".join(
            f'<th style="{th_style.format(align=_align(ci))}">{cell}</th>'
            for ci, cell in enumerate(b.headers)
        )
        header_html = f"<tr>{cells}</tr>"

    # ── Corpo ──────────────────────────────────────────────────────────────────
    rows_html = ""
    i = 0
    while i < len(rows):
        row = (rows[i] + [""] * ncols)[:ncols]

        if row[0] != "":
            # Dimensões extras (linhas com col 0 vazia)
            extra_dims = []
            j = i + 1
            while j < len(rows):
                nr = (rows[j] + [""] * ncols)[:ncols]
                if nr[0] == "":
                    extra_dims.append(nr)
                    j += 1
                else:
                    break

            # Score do evento (último valor da linha do evento)
            event_score = row[-1] if row[-1] else ""
            score_color = _temp_color(event_score) if use_temp_colors else "#fff"
            td_ev_score_colored = td_event_score.replace(
                "color:#fff", f"color:{score_color}"
            ) if use_temp_colors else td_event_score

            # Linha do evento — só nome e score, meio vazio
            event_cells = f'<td style="{td_event_first}">{row[0]}</td>'
            for ci in range(1, ncols):
                if ci == ncols - 1:
                    event_cells += f'<td style="{td_ev_score_colored}">{event_score}</td>'
                else:
                    event_cells += f'<td style="{td_event_empty}">&nbsp;</td>'
            rows_html += f"<tr>{event_cells}</tr>"

            # Dimensões — todas vêm das linhas extras (col 0 vazia)
            for di, dim in enumerate(extra_dims):
                dim_score = dim[-1] if dim[-1] else ""
                sc = _temp_color(dim_score) if use_temp_colors else color
                arrow = f'<td style="{td_arrow}">&#8627;</td>'
                name  = f'<td style="{td_dim_name}">{dim[1] if ncols > 1 else ""}</td>'
                rest  = "".join(
                    f'<td style="{td_dim.format(align=_align(ci))}">{dim[ci]}</td>'
                    if ci < ncols - 1 else
                    f'<td style="{td_dim.format(align=_align(ci))};color:{sc};font-weight:600">{dim[ci]}</td>'
                    for ci in range(2, ncols)
                )
                rows_html += f"<tr>{arrow}{name}{rest}</tr>"

            i = j
        else:
            cells = "".join(
                f'<td style="{td_dim.format(align=_align(ci))}">{cell}</td>'
                for ci, cell in enumerate(row)
            )
            rows_html += f"<tr>{cells}</tr>"
            i += 1

    return (
        f'<table cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;border-collapse:collapse;margin:10px 0 16px;'
        f'border:1px solid #e0dbd4;overflow:hidden">'
        f'{"<thead>" + header_html + "</thead>" if header_html else ""}'
        f"<tbody>{rows_html}</tbody>"
        f"</table>"
    )

def _r_divider() -> str:
    return '<div style="height:1px;background:#ddd5c8;margin:16px 0"></div>'

def _render_block(block, cfg: dict) -> str:
    font      = cfg.get("body_font",  "Georgia,'Times New Roman',serif")
    size      = cfg.get("font_size",  "14")
    lh        = cfg.get("line_height","1.78")
    color     = cfg.get("body_text",  "#3a3530")
    accent    = cfg.get("accent",     "#00a99d")
    highlight = cfg.get("highlight",  "#b5a98a")

    if isinstance(block, TextBlock):   return _r_text(block, font, size, lh, color)
    if isinstance(block, ImageBlock):  return _r_image(block)
    if isinstance(block, QuoteBlock):  return _r_quote(block, accent, font)
    if isinstance(block, ListBlock):   return _r_list(block, font, size, color)
    if isinstance(block, TableBlock):  return _r_table(
        block, font, size, color, accent,
        highlight=cfg.get('table_event_bg', cfg.get('highlight', '#b5a98a')),
        table_header_bg=cfg.get('table_header_bg', accent),
        use_temp_colors=cfg.get('use_temp_colors', True),
    )
    if isinstance(block, DividerBlock):return _r_divider()
    return ""

def _render_article(art, cfg: dict, first: bool) -> str:
    divider = ""  # sem divisória entre artigos
    font    = cfg.get("body_font", "Georgia,'Times New Roman',serif")
    primary = cfg.get("primary",   "#0f0f0f")
    size    = cfg.get("font_size", "14")
    title_size = str(int(size) + 1)
    blocks_html = "".join(_render_block(b, cfg) for b in art.blocks)
    title_html = (
        f'<p style="margin:0 0 10px;font-size:{title_size}px;font-weight:700;'
        f'font-family:{font};color:{primary};line-height:1.35">{art.title}</p>'
        if art.title else ""
    )
    return f'{divider}<div style="margin-bottom:4px">{title_html}{blocks_html}</div>'

def _render_section(sec, cfg: dict) -> str:
    highlight = cfg.get("highlight", "#b5a98a")
    articles  = "".join(_render_article(a, cfg, i == 0) for i, a in enumerate(sec.articles))
    return (
        f'<div style="margin-bottom:10px">'
        f'<p style="margin:0 0 14px;font-size:9px;letter-spacing:.18em;'
        f'text-transform:uppercase;font-family:Arial,sans-serif;font-weight:700;'
        f'color:{highlight};padding-bottom:7px;border-bottom:2px solid {highlight}">'
        f'{sec.title}</p>'
        f'{articles}'
        f'</div>'
    )

def _render_theme(theme, cfg: dict) -> str:
    accent      = cfg.get("accent",      "#00a99d")
    banner_color= cfg.get("banner_color_theme", cfg.get("accent", "#00a99d"))
    sections    = "".join(_render_section(s, cfg) for s in theme.sections)
    header = ""
    if theme.title:
        header = (
            f'<div style="background:{accent};padding:9px 28px;margin-bottom:0">'
            f'<p style="margin:0;font-size:9px;letter-spacing:.24em;'
            f'text-transform:uppercase;font-family:Arial,sans-serif;'
            f'font-weight:700;color:#fff">{theme.title}</p></div>'
        )
    return f'<div>{header}<div style="padding:20px 28px 4px">{sections}</div></div>'


# ── Banner ────────────────────────────────────────────────────────────────────

def _render_banner(cfg: dict) -> str:
    b64   = cfg.get("banner_img_b64", "")
    ext   = cfg.get("banner_img_ext", "png")
    h     = cfg.get("banner_height",  "180px")
    if b64:
        return (
            f'<div style="line-height:0">'
            f'<img src="data:image/{ext};base64,{b64}" alt="banner" '
            f'style="width:100%;max-width:560px;height:{h};object-fit:cover;display:block" /></div>'
        )
    # fallback: cor sólida com texto
    org     = cfg.get("org", "CEG — UnB")
    accent  = cfg.get("accent", "#00a99d")
    banner_bg = cfg.get("banner_fallback_color", "#0f0f0f")
    return (
        f'<div style="background:{banner_bg};padding:30px 28px 24px">'
        f'<p style="margin:0 0 6px;font-size:20px;font-weight:700;'
        f'color:#fff;font-family:Arial,sans-serif">{org}</p>'
        f'<p style="margin:0;font-size:10px;letter-spacing:.15em;'
        f'text-transform:uppercase;color:{accent};font-family:Arial,sans-serif">'
        f'Boletim de Conjuntura</p>'
        f'</div>'
    )


# ── Faixa de data ─────────────────────────────────────────────────────────────

def _render_datebar(cfg: dict) -> str:
    edition   = cfg.get("edition", "")
    date_str  = _fmt_date(cfg.get("date_format", "extenso"))
    highlight = cfg.get("highlight", "#b5a98a")
    text = f"{edition} &nbsp;·&nbsp; {date_str}" if edition else date_str
    return (
        f'<div style="background:#fff;padding:10px 28px;border-bottom:1px solid #eee">'
        f'<p style="margin:0;font-size:11px;color:{highlight};'
        f'font-family:Arial,sans-serif;letter-spacing:.07em">{text}</p>'
        f'</div>'
    )


# ── Faixa de degradê ──────────────────────────────────────────────────────────

def _render_gradient(cfg: dict) -> str:
    left  = cfg.get("grad_left",   "#00a99d")
    right = cfg.get("grad_right",  "#b5a98a")
    h     = cfg.get("grad_height", "4")
    return f'<div style="height:{h}px;background:linear-gradient(90deg,{left} 0%,{right} 100%)"></div>'


# ── Rodapé ────────────────────────────────────────────────────────────────────

def _render_footer(cfg: dict) -> str:
    date_str  = _fmt_date(cfg.get("date_format", "extenso"))
    left_raw  = cfg.get("footer_left",  "CEG — UnB · {date}").replace("{date}", date_str)
    right_raw = cfg.get("footer_right", "").replace("{date}", date_str)
    cols      = int(cfg.get("footer_cols", 1))
    bg        = cfg.get("footer_bg",    "#0f0f0f")
    color     = cfg.get("footer_color", "#b5a98a")

    left_html  = parse_footer_markdown(left_raw)
    right_html = parse_footer_markdown(right_raw) if right_raw else ""

    cell_style = (
        f'font-size:10px;color:{color};font-family:Arial,sans-serif;'
        f'letter-spacing:.05em;vertical-align:middle'
    )
    # Override link color inside footer
    footer_link_css = f'color:{color}'

    if cols == 2 and right_html:
        inner = (
            f'<table cellpadding="0" cellspacing="0" border="0" style="width:100%">'
            f'<tr>'
            f'<td style="{cell_style};text-align:left">{left_html}</td>'
            f'<td style="{cell_style};text-align:right">{right_html}</td>'
            f'</tr></table>'
        )
    else:
        inner = f'<p style="margin:0;{cell_style}">{left_html}</p>'

    return (
        f'<div style="background:{bg};padding:14px 28px">'
        f'<style>.footer-wrap a{{color:{color}!important;text-decoration:none}}</style>'
        f'<div class="footer-wrap">{inner}</div>'
        f'</div>'
    )


# ── Montagem principal ────────────────────────────────────────────────────────

def build_email_html(text: str, cfg: dict) -> str:
    """Fragmento HTML do email — inline styles, Outlook-safe."""
    themes = parse_markdown(text)
    body   = (
        "".join(_render_theme(t, cfg) for t in themes)
        if themes else
        '<div style="padding:24px 28px;font-size:13px;color:#aaa;font-style:italic">'
        'Cole o conteúdo no editor usando # Tema, ## Seção e ### Artigo.</div>'
    )

    return (
        f'<div style="background:#fff;max-width:560px;margin:0 auto;'
        f'font-family:{cfg.get("body_font","Georgia,serif")};'
        f'border:1px solid #ddd;overflow:hidden">'
        f'{_render_banner(cfg)}'
        f'{_render_datebar(cfg)}'
        f'{_render_gradient(cfg)}'
        f'<div style="padding:6px 0 28px">{body}</div>'
        f'{_render_footer(cfg)}'
        f'</div>'
    )


def build_full_html(text: str, cfg: dict) -> str:
    """Página HTML completa para download e abertura no browser."""
    bg    = cfg.get("bg_color", "#f0ede8")
    email = build_email_html(text, cfg)
    org   = cfg.get("org", "CEG-UnB")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Boletim — {org}</title>
</head>
<body style="margin:0;padding:40px 16px;background:{bg}">
{email}
</body>
</html>"""