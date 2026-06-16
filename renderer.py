"""
renderer.py — Gera HTML de email compatível com Outlook (table-based).
CEG-UnB · Risco Internacional

Hierarquia de títulos:
  #   → negrito azul (#26619C), fonte grande, espaço acima
  ##  → negrito preto (#1a1a1a), fonte média
  ### → itálico cinza (#555), mesmo tamanho do texto

O parser com 2 níveis mapeia # → section e ## → article.
O parser com 3 níveis mapeia # → theme, ## → section, ### → article.
_render_theme detecta o caso e passa o depth correto para baixo.
"""

from __future__ import annotations
import datetime
from parser import (
    parse_markdown, parse_footer_markdown,
    TextBlock, ImageBlock, QuoteBlock, ListBlock, TableBlock, DividerBlock,
)

MONTHS_PT = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
             "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

# ── Constantes CEG ────────────────────────────────────────────────────────────
HEADER_IMG_URL  = "https://i.ibb.co/CpsGNhxg/site-header.png"
COLOR_PRIMARY   = "#26619C"
COLOR_SECONDARY = "#acac95"
COLOR_BG_EMAIL  = "#f2f2f2"
COLOR_BG_BODY   = "#ffffff"
COLOR_TEXT      = "#2e2e2e"
COLOR_H1        = "#26619C"   # # — negrito azul
COLOR_H2        = "#1a1a1a"   # ## — negrito preto
COLOR_H3        = "#555555"   # ### — itálico cinza
FONT_BODY       = "Georgia, 'Times New Roman', serif"
FONT_UI         = "Arial, Helvetica, sans-serif"

IREL_ADDRESS = (
    "Instituto de Relações Internacionais — Universidade de Brasília<br>"
    "Campus Universitário Darcy Ribeiro, Asa Norte — Brasília, DF 70910-900"
)
CEG_SITE      = "https://estudosglobais.unb.br/"
CEG_EMAIL     = "estudosglobais@unb.br"
CEG_FULL_NAME = "Centro de Estudos Globais da Universidade de Brasília"


# ── Data ──────────────────────────────────────────────────────────────────────

def _fmt_date_today() -> str:
    t = datetime.date.today()
    return f"{t.day} de {MONTHS_PT[t.month]} de {t.year}"

def _fmt_date(fmt: str) -> str:
    t = datetime.date.today()
    if fmt == "ddmmyyyy": return t.strftime("%d/%m/%Y")
    if fmt == "precisa":  return f"{MONTHS_PT[t.month].capitalize()} de {t.year}"
    return f"{t.day} de {MONTHS_PT[t.month]} de {t.year}"

def _next_wednesday() -> str:
    today = datetime.date.today()
    days = (2 - today.weekday()) % 7
    if days == 0:
        days = 7
    nw = today + datetime.timedelta(days=days)
    return f"{nw.day} de {MONTHS_PT[nw.month]} de {nw.year}"


# ── Blocos de conteúdo ────────────────────────────────────────────────────────

def _r_text(b: TextBlock, font: str, size: str, lh: str, color: str) -> str:
    align = "center" if b.align == "center" else "left"
    return (
        f'<p style="margin:0 0 14px;font-size:{size}px;line-height:{lh};'
        f'color:{color};font-family:{font};text-align:{align}">{b.text}</p>'
    )

def _r_image(b: ImageBlock) -> str:
    return (
        f'<div style="margin:10px 0 16px">'
        f'<img src="{b.url}" alt="{b.alt}" '
        f'style="max-width:100%;height:auto;display:block;border-radius:4px" /></div>'
    )

def _r_quote(b: QuoteBlock, font: str) -> str:
    return (
        f'<table cellpadding="0" cellspacing="0" border="0" style="width:100%;margin:10px 0 16px">'
        f'<tr><td style="width:4px;background:{COLOR_PRIMARY};border-radius:2px">&nbsp;</td>'
        f'<td style="padding:8px 14px;font-style:italic;font-size:13px;'
        f'color:#666;font-family:{font}">{b.text}</td></tr></table>'
    )

def _r_list(b: ListBlock, font: str, size: str, color: str) -> str:
    tag = "ol" if b.ordered else "ul"
    style = (
        f'style="margin:6px 0 14px;padding-left:22px;font-size:{size}px;'
        f'line-height:1.6;color:{color};font-family:{font}"'
    )
    items = "".join(f'<li style="margin-bottom:5px">{item}</li>' for item in b.items)
    return f'<{tag} {style}>{items}</{tag}>'

def _r_table(b: TableBlock, font: str, size: str, color: str,
             table_header_bg: str = "", use_temp_colors: bool = True) -> str:
    if not table_header_bg:
        table_header_bg = COLOR_PRIMARY
    ncols  = max(len(b.headers) if b.headers else 0,
                 max((len(r) for r in b.rows), default=0))
    aligns = (b.aligns + ["left"] * ncols)[:ncols]
    wide   = ncols >= 4
    fs     = str(int(size) - 2) if wide else size
    pad_h  = "5px 8px" if wide else "7px 10px"
    pad_d  = "5px 8px" if wide else "6px 10px"

    def _align(ci): return aligns[ci] if ci < len(aligns) else "left"
    def _contrast(hx):
        h = hx.lstrip("#")
        if len(h) != 6: return "#fff"
        r, g, bv = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return "#111" if (0.299*r + 0.587*g + 0.114*bv)/255 > 0.55 else "#fff"

    th_fg  = _contrast(table_header_bg)
    th_sep = "rgba(255,255,255,.15)"
    th_style = (
        f"background:{table_header_bg};color:{th_fg};font-family:{font};"
        f"font-size:{fs}px;font-weight:700;letter-spacing:.03em;"
        f"padding:{pad_h};border-right:1px solid {th_sep};text-align:{{align}}"
    )
    td_style = (
        f"font-family:{font};font-size:{fs}px;color:{color};"
        f"padding:{pad_d};border-bottom:1px solid #e0e0e0;"
        f"border-right:1px solid #e8e8e8;vertical-align:middle;text-align:{{align}}"
    )
    header_html = ""
    if b.headers:
        cells = "".join(
            f'<th style="{th_style.format(align=_align(ci))}">{cell}</th>'
            for ci, cell in enumerate(b.headers)
        )
        header_html = f"<tr>{cells}</tr>"
    rows_html = "".join(
        "<tr>" + "".join(
            f'<td style="{td_style.format(align=_align(ci))}">{cell}</td>'
            for ci, cell in enumerate((row + [""]*ncols)[:ncols])
        ) + "</tr>"
        for row in b.rows
    )
    return (
        f'<table cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;border-collapse:collapse;margin:10px 0 16px;'
        f'border:1px solid #e0e0e0">'
        f'<thead>{header_html}</thead><tbody>{rows_html}</tbody></table>'
    )

def _r_divider() -> str:
    return '<div style="height:1px;background:#ddd;margin:16px 0"></div>'

def _render_block(block, cfg: dict) -> str:
    font  = cfg.get("body_font",   FONT_BODY)
    size  = cfg.get("font_size",   "14")
    lh    = cfg.get("line_height", "1.5")
    color = cfg.get("body_text",   COLOR_TEXT)
    if isinstance(block, TextBlock):    return _r_text(block, font, size, lh, color)
    if isinstance(block, ImageBlock):   return _r_image(block)
    if isinstance(block, QuoteBlock):   return _r_quote(block, font)
    if isinstance(block, ListBlock):    return _r_list(block, font, size, color)
    if isinstance(block, TableBlock):   return _r_table(
        block, font, size, color,
        table_header_bg=cfg.get("table_header_bg", COLOR_PRIMARY),
        use_temp_colors=cfg.get("use_temp_colors", True),
    )
    if isinstance(block, DividerBlock): return _r_divider()
    return ""


# ── Títulos ───────────────────────────────────────────────────────────────────

def _h1(title: str, font: str, size: str) -> str:
    """# — negrito azul, fonte grande, espaço acima"""
    return (
        f'<p style="margin:20px 0 10px;font-size:{int(size)+8}px;'
        f'font-weight:700;font-style:normal;color:{COLOR_H1};'
        f'font-family:{font};line-height:1.15">{title}</p>'
    )

def _h2(title: str, font: str, size: str) -> str:
    """## — negrito preto, mesmo tamanho do texto"""
    return (
        f'<p style="margin:14px 0 8px;font-size:{size}px;'
        f'font-weight:700;font-style:normal;color:{COLOR_H2};'
        f'font-family:{font};line-height:1.25">{title}</p>'
    )

def _h3(title: str, font: str, size: str) -> str:
    """### — itálico cinza, mesmo tamanho do texto"""
    return (
        f'<p style="margin:10px 0 6px;font-size:{size}px;'
        f'font-weight:400;font-style:italic;color:{COLOR_H3};'
        f'font-family:{font};line-height:1.3">{title}</p>'
    )


# ── Estrutura ─────────────────────────────────────────────────────────────────

def _render_article(art, cfg: dict, as_level: int = 3) -> str:
    """
    as_level=3 → ### estilo (itálico cinza)
    as_level=2 → ## estilo (negrito preto)  ← usado quando MD tem só 2 níveis
    """
    font   = cfg.get("body_font", FONT_BODY)
    size   = cfg.get("font_size", "14")
    blocks = "".join(_render_block(b, cfg) for b in art.blocks)
    if art.title:
        title_html = _h2(art.title, font, size) if as_level == 2 else _h3(art.title, font, size)
    else:
        title_html = ""
    return f'<div style="margin-bottom:8px">{title_html}{blocks}</div>'

def _render_section(sec, cfg: dict, as_level: int = 2) -> str:
    """
    as_level=2 → ## estilo (negrito preto)
    as_level=1 → # estilo (negrito azul)  ← usado quando MD tem só 2 níveis
    """
    font     = cfg.get("body_font", FONT_BODY)
    size     = cfg.get("font_size", "14")
    # artigos um nível abaixo da seção
    art_level = as_level + 1
    articles  = "".join(_render_article(a, cfg, as_level=art_level) for a in sec.articles)
    if sec.title:
        title_html = _h1(sec.title, font, size) if as_level == 1 else _h2(sec.title, font, size)
    else:
        title_html = ""
    return f'<div style="margin-bottom:16px">{title_html}{articles}</div>'

def _render_theme(theme, cfg: dict) -> str:
    """
    Com 3 níveis: theme.title existe → # (h1), sections como h2, articles como h3
    Com 2 níveis: theme.title vazio  → sections como h1, articles como h2
    """
    font = cfg.get("body_font", FONT_BODY)
    size = cfg.get("font_size", "14")

    if theme.title:
        # 3 níveis: # → h1, ## → h2, ### → h3
        sec_level = 2
        title_html = _h1(theme.title, font, size)
    else:
        # 2 níveis: # → h1 (via section), ## → h2 (via article)
        sec_level  = 1
        title_html = ""

    sections = "".join(_render_section(s, cfg, as_level=sec_level) for s in theme.sections)
    return f'<div style="margin-bottom:24px">{title_html}{sections}</div>'


# ── Header ────────────────────────────────────────────────────────────────────

def _render_header(cfg: dict) -> str:
    b64 = cfg.get("banner_img_b64", "")
    ext = cfg.get("banner_img_ext", "png")
    h   = cfg.get("banner_height",  "160px")
    img_src = f"data:image/{ext};base64,{b64}" if b64 else HEADER_IMG_URL

    return (
        f'<div style="line-height:0;overflow:hidden">'
        f'<img src="{img_src}" alt="Centro de Estudos Globais — UnB" '
        f'style="width:100%;max-width:560px;height:{h};object-fit:cover;display:block" />'
        f'</div>'
        f'<div style="background:#ffffff;padding:20px 28px 16px;text-align:center">'
        f'<p style="margin:0 0 10px;font-size:11px;color:{COLOR_SECONDARY};'
        f'font-family:{FONT_UI};letter-spacing:.1em;text-transform:uppercase">'
        f'{_fmt_date_today()}</p>'
        f'<p style="margin:0 0 6px;font-size:26px;font-weight:700;'
        f'color:{COLOR_H1};font-family:{FONT_BODY};letter-spacing:-.01em;line-height:1.1">'
        f'{cfg.get("product_name","Risco Internacional")}</p>'
        f'<p style="margin:0;font-size:11px;color:{COLOR_SECONDARY};'
        f'font-family:{FONT_UI};font-style:italic;letter-spacing:.04em">'
        f'{cfg.get("product_tagline","Um produto do Laboratório de Análise de Risco e Conjuntura")}</p>'
        f'</div>'
        f'<div style="height:3px;background:linear-gradient(90deg,{COLOR_PRIMARY} 0%,{COLOR_SECONDARY} 100%)"></div>'
    )


# ── Footer ────────────────────────────────────────────────────────────────────

def _render_footer(cfg: dict) -> str:
    next_ed = _next_wednesday()
    editorial = cfg.get("editorial", "").strip()
    editorial_html = ""
    if editorial:
        editorial_html = (
            f'<p style="margin:0 0 10px;font-size:11px;color:rgba(255,255,255,.85);'
            f'font-family:{FONT_UI};text-align:center;line-height:1.6">'
            f'<strong style="color:#ffffff;letter-spacing:.04em">Editorial</strong><br>'
            f'{editorial}</p>'
            f'<div style="height:1px;background:rgba(255,255,255,.2);margin:0 0 14px"></div>'
        )
    return (
        f'<div style="background:{COLOR_PRIMARY};padding:20px 28px 16px">'
        f'<p style="margin:0 0 14px;font-size:12px;color:#ffffff;'
        f'font-family:{FONT_UI};line-height:1.6;text-align:center;font-style:italic">'
        f'Dúvidas, comentários ou interesse em aprofundar algum tema?<br>'
        f'Entre em contato — teremos prazer em conversar.<br>'
        f'<strong>Próxima edição: {next_ed}</strong></p>'
        f'<div style="height:1px;background:rgba(255,255,255,.2);margin:0 0 14px"></div>'
        f'{editorial_html}'
        f'<p style="margin:0 0 6px;font-size:11px;font-family:{FONT_UI};text-align:center">'
        f'<a href="{CEG_SITE}" target="_blank" '
        f'style="color:#ffffff;text-decoration:none;font-weight:600;letter-spacing:.04em">'
        f'{CEG_FULL_NAME}</a></p>'
        f'<p style="margin:0 0 6px;font-size:11px;font-family:{FONT_UI};text-align:center">'
        f'<a href="mailto:{CEG_EMAIL}" style="color:#ffffff;text-decoration:none">'
        f'{CEG_EMAIL}</a></p>'
        f'<p style="margin:0 0 12px;font-size:10px;color:rgba(255,255,255,.65);'
        f'font-family:{FONT_UI};text-align:center;line-height:1.6">{IREL_ADDRESS}</p>'
        f'<p style="margin:0 0 8px;font-size:9.5px;color:rgba(255,255,255,.5);'
        f'font-family:{FONT_UI};text-align:center;letter-spacing:.03em">'
        f'© {datetime.date.today().year} {CEG_FULL_NAME} — Todos os direitos reservados. '
        f'Reprodução parcial ou total permitida mediante citação da fonte.</p>'
        # TODO: inserir URL da nota metodológica abaixo (substituir # pelo link real)
        f'<p style="margin:0;font-size:9.5px;font-family:{FONT_UI};text-align:center">'
        f'<a href="#" style="color:rgba(255,255,255,.4);text-decoration:none;letter-spacing:.03em">'
        f'Nota Metodológica</a></p>'
        f'</div>'
    )


# ── Montagem ──────────────────────────────────────────────────────────────────

def build_email_html(text: str, cfg: dict) -> str:
    themes = parse_markdown(text)
    body = (
        "".join(_render_theme(t, cfg) for t in themes)
        if themes else
        f'<p style="font-size:13px;color:#aaa;font-style:italic">'
        f'Cole o conteúdo no editor. Use # Título, ## Subtítulo, ### Subseção.</p>'
    )
    font = cfg.get("body_font", FONT_BODY)
    return (
        f'<div style="background:{COLOR_BG_BODY};max-width:560px;margin:0 auto;'
        f'font-family:{font};border:1px solid #ddd;overflow:hidden">'
        f'{_render_header(cfg)}'
        f'<div style="padding:24px 28px 28px;background:{COLOR_BG_BODY}">{body}</div>'
        f'{_render_footer(cfg)}'
        f'</div>'
    )

def build_full_html(text: str, cfg: dict, for_pdf: bool = False) -> str:
    email = build_email_html(text, cfg)
    pdf_css = (
        '<style>'
        '@page { size: 600px 999999px; margin: 0; }'
        'body { margin: 0; padding: 20px 0; }'
        'p, li, blockquote, table { page-break-inside: avoid; }'
        'h1, h2, h3 { page-break-after: avoid; }'
        '</style>'
    ) if for_pdf else ""
    return (
        f'<!DOCTYPE html><html lang="pt-BR"><head>'
        f'<meta charset="UTF-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>Risco Internacional — CEG-UnB</title>'
        f'{pdf_css}'
        f'</head><body style="margin:0;padding:40px 16px;background:{COLOR_BG_EMAIL}">'
        f'{email}</body></html>'
    )
