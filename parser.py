"""
parser.py — Converte Markdown em estrutura de dados.

Hierarquia detectada automaticamente (1, 2 ou 3 níveis de #).

Sintaxe suportada no corpo dos artigos:
  **negrito**           → <strong>
  *itálico*             → <em>
  ~~tachado~~           → <s>
  `código`              → <code>
  [texto](url)          → <a>
  ![alt](url)           → ImageBlock
  > citação             → blockquote
  - item / * item       → lista não-ordenada
  1. item               → lista ordenada
  | col1 | col2 | col3 | → tabela Markdown (N colunas, cabeçalho, alinhamento)
  {center}...{/center}  → parágrafo centralizado
  ---                   → linha divisória
  linha vazia           → separa parágrafos
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Literal, Union


# ── Tipos de bloco ────────────────────────────────────────────────────────────

@dataclass
class TextBlock:
    kind: Literal["text"] = field(default="text", init=False)
    text: str = ""
    align: str = "left"   # "left" | "center"

@dataclass
class ImageBlock:
    kind: Literal["image"] = field(default="image", init=False)
    url: str = ""
    alt: str = ""

@dataclass
class QuoteBlock:
    kind: Literal["quote"] = field(default="quote", init=False)
    text: str = ""

@dataclass
class ListBlock:
    kind: Literal["list"] = field(default="list", init=False)
    ordered: bool = False
    items: List[str] = field(default_factory=list)

@dataclass
class TableBlock:
    kind: Literal["table"] = field(default="table", init=False)
    headers: List[str] = field(default_factory=list)      # células do cabeçalho (inline HTML)
    rows: List[List[str]] = field(default_factory=list)   # linhas de dados (inline HTML)
    aligns: List[str] = field(default_factory=list)       # "left" | "center" | "right" por coluna

@dataclass
class DividerBlock:
    kind: Literal["divider"] = field(default="divider", init=False)

Block = Union[TextBlock, ImageBlock, QuoteBlock, ListBlock, TableBlock, DividerBlock]

# ── Regexes ───────────────────────────────────────────────────────────────────
_IMAGE_RE   = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")
_TABLE_RE   = re.compile(r"^\|(.+)\|\s*$")          # qualquer linha que começa e termina com |
_SEP_RE     = re.compile(r"^[\s|:\-]+$")             # linha separadora de cabeçalho ex: |---|:---:|
_OL_RE      = re.compile(r"^\d+\.\s+(.+)")
_UL_RE      = re.compile(r"^[-*]\s+(.+)")
_QUOTE_RE   = re.compile(r"^>\s*(.*)")
_CENTER_RE  = re.compile(r"^\{center\}(.*)\{/center\}$", re.DOTALL)

def _parse_table_row(line: str) -> List[str]:
    """Extrai células de uma linha de tabela Markdown."""
    inner = line.strip().strip("|")
    return [c.strip() for c in inner.split("|")]

def _parse_align(sep_cell: str) -> str:
    s = sep_cell.strip()
    if s.startswith(":") and s.endswith(":"): return "center"
    if s.endswith(":"):                        return "right"
    return "left"

def _is_sep_row(line: str) -> bool:
    """Retorna True se a linha for uma linha separadora de cabeçalho ex: |---|:---:|---:|"""
    inner = line.strip().strip("|")
    cells = [c.strip() for c in inner.split("|")]
    if not cells:
        return False
    return all(re.match(r"^:?-{1,}:?$", c) for c in cells if c)

# Inline: aplicados sobre texto puro
def inline(text: str) -> str:
    """Aplica formatação inline Markdown → HTML."""
    # Escapa < e > para segurança (exceto tags já geradas)
    # Negrito+itálico (***) antes de negrito e itálico
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    text = re.sub(r"\*\*(.+?)\*\*",     r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*",         r"<em>\1</em>", text)
    text = re.sub(r"~~(.+?)~~",         r"<s>\1</s>", text)
    text = re.sub(r"`(.+?)`",           r'<code style="background:#f4f4f4;padding:1px 4px;border-radius:3px;font-size:90%">\1</code>', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" style="color:#00a99d;text-decoration:none">\1</a>', text)
    return text


# ── Estrutura ─────────────────────────────────────────────────────────────────

@dataclass
class Article:
    title: str
    blocks: List[Block] = field(default_factory=list)

@dataclass
class Section:
    title: str
    articles: List[Article] = field(default_factory=list)

@dataclass
class Theme:
    title: str
    sections: List[Section] = field(default_factory=list)


# ── Detecção de hierarquia ────────────────────────────────────────────────────

def _detect_levels(lines: list[str]) -> dict[int, str]:
    found = set()
    for line in lines:
        s = line.strip()
        if s.startswith("### "): found.add(3)
        elif s.startswith("## "): found.add(2)
        elif s.startswith("# "): found.add(1)
    sl = sorted(found)
    roles = ["theme", "section", "article"]
    if len(sl) == 0:   return {}
    if len(sl) == 1:   return {sl[0]: "article"}
    if len(sl) == 2:   return {sl[0]: "section", sl[1]: "article"}
    return {sl[0]: "theme", sl[1]: "section", sl[2]: "article"}

def _hlevel(line: str) -> int | None:
    s = line.strip()
    if s.startswith("### "): return 3
    if s.startswith("## "):  return 2
    if s.startswith("# "):   return 1
    return None

def _htext(line: str, level: int) -> str:
    return line.strip()[level + 1:].strip()


# ── Parser de blocos de conteúdo ──────────────────────────────────────────────

def _parse_blocks(raw_lines: list[str]) -> List[Block]:
    """
    Converte linhas brutas de um artigo em blocos tipados.
    Agrupa linhas consecutivas de lista e parágrafos.
    """
    blocks: List[Block] = []
    i = 0

    while i < len(raw_lines):
        line = raw_lines[i].rstrip()
        stripped = line.strip()

        # Linha vazia → separador (ignorado, os parágrafos já são blocos)
        if not stripped:
            i += 1
            continue

        # Imagem
        m = _IMAGE_RE.match(stripped)
        if m:
            blocks.append(ImageBlock(alt=m.group(1), url=m.group(2)))
            i += 1
            continue

        # Divisória
        if stripped in ("---", "***", "___"):
            blocks.append(DividerBlock())
            i += 1
            continue

        # Tabela Markdown: linha que começa e termina com |
        if _TABLE_RE.match(stripped):
            raw_rows = [stripped]
            i += 1
            while i < len(raw_lines):
                ns = raw_lines[i].strip()
                if _TABLE_RE.match(ns):
                    raw_rows.append(ns)
                    i += 1
                else:
                    break
            # Identifica linha separadora na posição 1 (padrão GFM)
            sep_idx = next(
                (ri for ri, row in enumerate(raw_rows) if _is_sep_row(row)),
                None
            )
            if sep_idx is not None:
                headers  = [inline(c) for c in _parse_table_row(raw_rows[0])] if sep_idx == 1 else []
                aligns   = [_parse_align(c) for c in _parse_table_row(raw_rows[sep_idx])]
                data_rows = [
                    [inline(c) for c in _parse_table_row(r)]
                    for ri, r in enumerate(raw_rows)
                    if ri != 0 and not _is_sep_row(r)
                ] if sep_idx == 1 else [
                    [inline(c) for c in _parse_table_row(r)]
                    for r in raw_rows
                    if not _is_sep_row(r)
                ]
            else:
                headers   = []
                aligns    = []
                data_rows = [[inline(c) for c in _parse_table_row(r)] for r in raw_rows]
            blocks.append(TableBlock(headers=headers, rows=data_rows, aligns=aligns))
            continue

        # Blockquote  > texto
        m = _QUOTE_RE.match(stripped)
        if m:
            quote_lines = [m.group(1)]
            i += 1
            while i < len(raw_lines):
                q2 = raw_lines[i].strip()
                qm = _QUOTE_RE.match(q2)
                if qm:
                    quote_lines.append(qm.group(1))
                    i += 1
                else:
                    break
            blocks.append(QuoteBlock(text=inline(" ".join(quote_lines))))
            continue

        # Lista não-ordenada
        m = _UL_RE.match(stripped)
        if m:
            items = [inline(m.group(1))]
            i += 1
            while i < len(raw_lines):
                m2 = _UL_RE.match(raw_lines[i].strip())
                if m2:
                    items.append(inline(m2.group(1)))
                    i += 1
                else:
                    break
            blocks.append(ListBlock(ordered=False, items=items))
            continue

        # Lista ordenada
        m = _OL_RE.match(stripped)
        if m:
            items = [inline(m.group(1))]
            i += 1
            while i < len(raw_lines):
                m2 = _OL_RE.match(raw_lines[i].strip())
                if m2:
                    items.append(inline(m2.group(1)))
                    i += 1
                else:
                    break
            blocks.append(ListBlock(ordered=True, items=items))
            continue

        # Centralizado {center}...{/center}
        m = _CENTER_RE.match(stripped)
        if m:
            blocks.append(TextBlock(text=inline(m.group(1)), align="center"))
            i += 1
            continue

        # Parágrafo normal — agrega linhas contíguas
        para_lines = [stripped]
        i += 1
        while i < len(raw_lines):
            next_s = raw_lines[i].strip()
            # Para se linha vazia ou início de bloco especial
            if (not next_s
                or _IMAGE_RE.match(next_s)
                or _QUOTE_RE.match(next_s)
                or _UL_RE.match(next_s)
                or _OL_RE.match(next_s)
                or _TABLE_RE.match(next_s)
                or _CENTER_RE.match(next_s)
                or next_s in ("---", "***", "___")):
                break
            para_lines.append(next_s)
            i += 1
        blocks.append(TextBlock(text=inline(" ".join(para_lines)), align="left"))

    return blocks


# ── Parser principal ──────────────────────────────────────────────────────────

def parse_markdown(text: str) -> List[Theme]:
    lines = text.splitlines()
    level_map = _detect_levels(lines)

    themes:  List[Theme]   = []
    theme:   Theme | None  = None
    section: Section | None = None
    article: Article | None = None
    # Buffer de linhas brutas do artigo corrente
    art_lines: List[str] = []

    def close_article():
        nonlocal article, art_lines
        if article is not None:
            article.blocks = _parse_blocks(art_lines)
            if section: section.articles.append(article)
            article = None
            art_lines = []

    def close_section():
        close_article()
        nonlocal section
        if section and theme:
            theme.sections.append(section)
            section = None

    def close_theme():
        close_section()
        nonlocal theme
        if theme:
            themes.append(theme)
            theme = None

    for raw in lines:
        lvl = _hlevel(raw)
        if lvl is not None and lvl in level_map:
            role  = level_map[lvl]
            title = _htext(raw, lvl)

            if role == "theme":
                close_theme()
                theme = Theme(title=title)
            elif role == "section":
                close_section()
                if theme is None: theme = Theme(title="")
                section = Section(title=title)
                # Artigo anônimo para receber conteúdo solto abaixo da seção
                article   = Article(title="")
                art_lines = []
            elif role == "article":
                close_article()
                if theme is None:   theme   = Theme(title="")
                if section is None: section = Section(title="")
                article   = Article(title=title)
                art_lines = []
        else:
            if article is not None:
                art_lines.append(raw)

    close_theme()
    return themes


# ── Parser de Markdown simples para footer ────────────────────────────────────

def parse_footer_markdown(text: str) -> str:
    """Converte uma linha de Markdown simples em HTML inline para o rodapé."""
    return inline(text)
