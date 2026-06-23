"""
app.py — Boletim CEG-UnB · Gerador de Newsletter
Reformulado: sidebar persistente · editor com syntax highlight · exportação PDF
"""

from __future__ import annotations
import base64
import io
import streamlit as st
import streamlit.components.v1 as components

from renderer import build_email_html, build_full_html, _render_footer
from config import (
    DEFAULT_CONFIG, DATE_FORMAT_OPTIONS, SAMPLE_CONTENT,
    list_profiles, save_profile, load_profile, delete_profile,
)

# ── Página ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GPS Brasil Editor",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* Base */
[data-testid="stAppViewContainer"] { background: #f7f5f2; }
[data-testid="stSidebar"] { background: #1a1a1a !important; }
[data-testid="stSidebar"] * { color: #e8e4de !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stColorPicker label { color: #a8a098 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: .06em; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,[data-testid="stSidebar"] h4 { color: #fff !important; }
[data-testid="stSidebar"] hr { border-color: #333 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: #2a2a2a !important; color: #e8e4de !important;
    border: 1px solid #444 !important; border-radius: 6px !important;
    font-size: 12px !important; width: 100%;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #00a99d !important; border-color: #00a99d !important; color: #fff !important;
}
/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 2px; border-bottom: 2px solid #e0dbd4; }
.stTabs [data-baseweb="tab"] {
    padding: 8px 20px; border-radius: 6px 6px 0 0;
    font-size: 13px; font-weight: 500; color: #666;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    background: #fff !important; color: #0f0f0f !important;
    border-bottom: 2px solid #00a99d !important; font-weight: 700;
}
/* Editor */
.stTextArea textarea {
    font-family: 'Menlo', 'Consolas', 'Monaco', monospace !important;
    font-size: 12.5px !important; line-height: 1.75 !important;
    background: #1e1e1e !important; color: #d4d0c8 !important;
    border: 1px solid #333 !important; border-radius: 8px !important;
}
/* Botões de ação */
.action-btn > button {
    background: #0f0f0f !important; color: #fff !important;
    border: none !important; border-radius: 6px !important;
    font-weight: 600 !important; font-size: 13px !important;
}
.action-btn-accent > button {
    background: #00a99d !important; color: #fff !important;
    border: none !important; border-radius: 6px !important;
    font-weight: 600 !important; font-size: 13px !important;
}
/* Cards de seção */
.section-card {
    background: #fff; border-radius: 10px; padding: 16px 20px;
    border: 1px solid #e8e3dc; margin-bottom: 12px;
}
/* Expanders */
div[data-testid="stExpander"] { border: 1px solid #e0dbd4 !important; border-radius: 8px !important; background: #fff; }
/* Cabeçalho da sidebar */
.sidebar-header {
    padding: 4px 0 12px;
    border-bottom: 1px solid #333;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def _ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

_ss("md_text",          SAMPLE_CONTENT)
_ss("banner_b64",       "")
_ss("banner_ext",       "png")
# Aparência (carregada do DEFAULT_CONFIG — persistida via perfis)
_ss("org",              DEFAULT_CONFIG["org"])
_ss("edition",          DEFAULT_CONFIG["edition"])
_ss("product_name",      DEFAULT_CONFIG["product_name"])
_ss("product_tagline",   DEFAULT_CONFIG["product_tagline"])
_ss("product_name_size", DEFAULT_CONFIG["product_name_size"])
_ss("product_name_bold", DEFAULT_CONFIG["product_name_bold"])
_ss("editorial",         DEFAULT_CONFIG["editorial"])
_ss("date_fmt_key",     list(DATE_FORMAT_OPTIONS.keys())[0])
_ss("banner_height",    int(DEFAULT_CONFIG["banner_height"].replace("px","")))
_ss("banner_fallback",  DEFAULT_CONFIG["banner_fallback"])
_ss("accent",           DEFAULT_CONFIG["accent"])
_ss("highlight",        DEFAULT_CONFIG["highlight"])
_ss("body_text",        DEFAULT_CONFIG["body_text"])
_ss("primary",          DEFAULT_CONFIG["primary"])
_ss("bg_color",         DEFAULT_CONFIG["bg_color"])
_ss("font_size",        int(DEFAULT_CONFIG["font_size"]))
_ss("line_height",      float(DEFAULT_CONFIG["line_height"]))
_ss("footer_cols",      1)
_ss("footer_left",      DEFAULT_CONFIG["footer_left"])
_ss("footer_right",     DEFAULT_CONFIG["footer_right"])
_ss("footer_bg",        DEFAULT_CONFIG["footer_bg"])
_ss("footer_color",     DEFAULT_CONFIG["footer_color"])
_ss("table_header_bg",  DEFAULT_CONFIG["table_header_bg"])
_ss("table_event_bg",   DEFAULT_CONFIG["table_event_bg"])
_ss("use_temp_colors",  DEFAULT_CONFIG["use_temp_colors"])
_ss("active_profile",   None)


def build_cfg() -> dict:
    return {
        "org":                st.session_state.org,
        "edition":            st.session_state.edition,
        "product_name":       st.session_state.product_name,
        "product_tagline":    st.session_state.product_tagline,
        "product_name_size":  st.session_state.product_name_size,
        "product_name_bold":  st.session_state.product_name_bold,
        "editorial":          st.session_state.editorial,
        "date_format":        DATE_FORMAT_OPTIONS[st.session_state.date_fmt_key],
        "banner_img_b64":     st.session_state.banner_b64,
        "banner_img_ext":     st.session_state.banner_ext,
        "banner_height":      f"{st.session_state.banner_height}px",
        "banner_fallback_color": st.session_state.banner_fallback,
        "accent":             st.session_state.accent,
        "highlight":          st.session_state.highlight,
        "body_text":          st.session_state.body_text,
        "primary":            st.session_state.primary,
        "bg_color":           st.session_state.bg_color,
        "body_font":          "Arial, Helvetica, sans-serif",
        "font_size":          str(st.session_state.font_size),
        "line_height":        str(st.session_state.line_height),
        "footer_cols":        st.session_state.footer_cols,
        "footer_left":        st.session_state.footer_left,
        "footer_right":       st.session_state.footer_right,
        "footer_bg":          st.session_state.footer_bg,
        "footer_color":       st.session_state.footer_color,
        "table_header_bg":    st.session_state.table_header_bg,
        "table_event_bg":     st.session_state.table_event_bg,
        "use_temp_colors":    st.session_state.use_temp_colors,
    }


def _apply_profile_to_ss(cfg: dict):
    """Aplica um dict de configuração carregado ao session_state."""
    date_map_inv = {v: k for k, v in DATE_FORMAT_OPTIONS.items()}

    st.session_state.org           = cfg.get("org", DEFAULT_CONFIG["org"])
    st.session_state.edition       = cfg.get("edition", DEFAULT_CONFIG["edition"])
    st.session_state.product_name      = cfg.get("product_name",      DEFAULT_CONFIG["product_name"])
    st.session_state.product_tagline   = cfg.get("product_tagline",   DEFAULT_CONFIG["product_tagline"])
    st.session_state.product_name_size = cfg.get("product_name_size", DEFAULT_CONFIG["product_name_size"])
    st.session_state.product_name_bold = cfg.get("product_name_bold", DEFAULT_CONFIG["product_name_bold"])
    st.session_state.editorial         = cfg.get("editorial",         DEFAULT_CONFIG["editorial"])
    st.session_state.date_fmt_key  = date_map_inv.get(cfg.get("date_format","extenso"), list(DATE_FORMAT_OPTIONS.keys())[0])
    st.session_state.banner_height = int(cfg.get("banner_height","160px").replace("px",""))
    st.session_state.banner_fallback = cfg.get("banner_fallback", DEFAULT_CONFIG["banner_fallback"])
    st.session_state.accent        = cfg.get("accent",       DEFAULT_CONFIG["accent"])
    st.session_state.highlight     = cfg.get("highlight",    DEFAULT_CONFIG["highlight"])
    st.session_state.body_text     = cfg.get("body_text",    DEFAULT_CONFIG["body_text"])
    st.session_state.primary       = cfg.get("primary",      DEFAULT_CONFIG["primary"])
    st.session_state.bg_color      = cfg.get("bg_color",     DEFAULT_CONFIG["bg_color"])
    st.session_state.font_size     = int(cfg.get("font_size","14"))
    st.session_state.line_height   = float(cfg.get("line_height","1.25"))
    st.session_state.footer_cols   = int(cfg.get("footer_cols", 1))
    st.session_state.footer_left   = cfg.get("footer_left",  DEFAULT_CONFIG["footer_left"])
    st.session_state.footer_right  = cfg.get("footer_right", DEFAULT_CONFIG["footer_right"])
    st.session_state.footer_bg     = cfg.get("footer_bg",    DEFAULT_CONFIG["footer_bg"])
    st.session_state.footer_color  = cfg.get("footer_color", DEFAULT_CONFIG["footer_color"])
    st.session_state.table_header_bg = cfg.get("table_header_bg", DEFAULT_CONFIG["table_header_bg"])
    st.session_state.table_event_bg  = cfg.get("table_event_bg",  DEFAULT_CONFIG["table_event_bg"])
    st.session_state.use_temp_colors = cfg.get("use_temp_colors", True)


def _make_pdf(html_full: str) -> bytes:
    """Gera PDF página única (scrollável) usando WeasyPrint."""
    try:
        from weasyprint import HTML, CSS
        # Página única e larga — perfeita para rolamento no celular
        scroll_css = CSS(string=(
            "@page { size: 600px 999999px; margin: 0; }"
            "body { margin: 0; padding: 20px 0; }"
            "p, li, blockquote, table { page-break-inside: avoid; }"
        ))
        return HTML(string=html_full).write_pdf(stylesheets=[scroll_css])
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")
        return b""


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Aparência + Rodapé + Perfis (persistente)
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sidebar-header">', unsafe_allow_html=True)
    st.markdown("### 📰 GPS Brasil | CEG")
    st.caption("Gerador de Newsletter")
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Perfis ────────────────────────────────────────────────────────────────
    with st.expander("💾 Perfis de aparência", expanded=False):
        profiles = list_profiles()
        if profiles:
            sel_profile = st.selectbox("Carregar perfil", ["— selecionar —"] + profiles, key="sb_profile_sel")
            col_load, col_del = st.columns(2)
            with col_load:
                if st.button("📂 Carregar", key="btn_load_profile"):
                    if sel_profile != "— selecionar —":
                        _apply_profile_to_ss(load_profile(sel_profile))
                        st.session_state.active_profile = sel_profile
                        st.success(f"Perfil «{sel_profile}» carregado.")
                        st.rerun()
            with col_del:
                if st.button("🗑️ Excluir", key="btn_del_profile"):
                    if sel_profile != "— selecionar —":
                        delete_profile(sel_profile)
                        st.rerun()
        else:
            st.caption("Nenhum perfil salvo ainda.")

        st.divider()
        new_profile_name = st.text_input("Nome do novo perfil", placeholder="ex: padrão-ceg", key="sb_profile_new")
        if st.button("💾 Salvar perfil atual", key="btn_save_profile"):
            name = new_profile_name.strip()
            if name:
                save_profile(name, build_cfg())
                st.session_state.active_profile = name
                st.success(f"Perfil «{name}» salvo!")
                st.rerun()
            else:
                st.warning("Digite um nome para o perfil.")

    if st.session_state.active_profile:
        st.caption(f"✅ Perfil ativo: **{st.session_state.active_profile}**")

    st.divider()

    # ── Identificação ─────────────────────────────────────────────────────────
    st.markdown("#### 🏛️ Identificação")
    st.session_state.org      = st.text_input("Organização",     st.session_state.org,     key="sb_org")
    st.session_state.edition  = st.text_input("Edição / Volume", st.session_state.edition, key="sb_ed")
    st.session_state.product_name    = st.text_input("Nome do produto",  st.session_state.product_name,    key="sb_pname")
    st.session_state.product_tagline = st.text_input("Tagline",          st.session_state.product_tagline, key="sb_ptag")
    pn1, pn2 = st.columns(2)
    with pn1:
        st.session_state.product_name_size = st.slider("Tamanho título (px)", 16, 50, st.session_state.product_name_size, key="sb_pnsz")
    with pn2:
        st.session_state.product_name_bold = st.toggle("Negrito", st.session_state.product_name_bold, key="sb_pnbd")
    st.session_state.date_fmt_key = st.selectbox(
        "Formato de data",
        list(DATE_FORMAT_OPTIONS.keys()),
        index=list(DATE_FORMAT_OPTIONS.keys()).index(st.session_state.date_fmt_key),
        key="sb_dfmt",
    )

    st.divider()

    # ── Banner ────────────────────────────────────────────────────────────────
    st.markdown("#### 🖼️ Banner")
    uploaded = st.file_uploader("Imagem (PNG, JPG, GIF)", type=["png","jpg","jpeg","gif"], key="sb_upload")
    if uploaded:
        raw = uploaded.read()
        st.session_state.banner_b64 = base64.b64encode(raw).decode()
        st.session_state.banner_ext = uploaded.type.split("/")[-1].replace("jpeg","jpg")
        st.success(f"{len(raw)//1024} KB carregados")
    if st.session_state.banner_b64:
        if st.button("🗑️ Remover banner"):
            st.session_state.banner_b64 = ""
            st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.banner_height = st.slider("Altura (px)", 60, 360, st.session_state.banner_height, key="sb_bh")
    with c2:
        st.session_state.banner_fallback = st.color_picker("Fundo s/ imagem", st.session_state.banner_fallback, key="sb_bf")

    st.divider()

    # ── Cores ─────────────────────────────────────────────────────────────────
    st.markdown("#### 🎨 Cores")
    cc1, cc2 = st.columns(2)
    with cc1:
        st.session_state.bg_color   = st.color_picker("Fundo",     st.session_state.bg_color,   key="sb_bg")
        st.session_state.accent     = st.color_picker("Accent",    st.session_state.accent,     key="sb_ac")
        st.session_state.primary    = st.color_picker("Primária",  st.session_state.primary,    key="sb_pr")
    with cc2:
        st.session_state.highlight  = st.color_picker("Destaque",  st.session_state.highlight,  key="sb_hl")
        st.session_state.body_text  = st.color_picker("Corpo",     st.session_state.body_text,  key="sb_bt")

    st.markdown("**Tabelas**")
    tc1, tc2 = st.columns(2)
    with tc1:
        st.session_state.table_header_bg = st.color_picker("Cabeçalho", st.session_state.table_header_bg, key="sb_thbg")
    with tc2:
        st.session_state.table_event_bg  = st.color_picker("Evento",    st.session_state.table_event_bg,  key="sb_tebg")
    st.session_state.use_temp_colors = st.toggle("Cores de temperatura nos scores", st.session_state.use_temp_colors, key="sb_utc")

    st.divider()

    # ── Tipografia ────────────────────────────────────────────────────────────
    st.markdown("#### 🔤 Tipografia")
    st.caption("Fonte: Arial / Helvetica (sem serifa, fixa)")
    fc1, fc2 = st.columns(2)
    with fc1:
        st.session_state.font_size   = st.slider("Tamanho corpo (px)", 11, 20, st.session_state.font_size, key="sb_fs")
    with fc2:
        st.session_state.line_height = st.slider("Espaçamento entre linhas", 1.3, 2.0, st.session_state.line_height, step=0.05, key="sb_lh")

    st.divider()

    # ── Rodapé ────────────────────────────────────────────────────────────────
    st.markdown("#### 📌 Rodapé")
    fcols_label = st.radio("Layout", ["1 coluna", "2 colunas"],
                           index=st.session_state.footer_cols - 1,
                           horizontal=True, key="sb_fcols")
    st.session_state.footer_cols = 2 if fcols_label == "2 colunas" else 1

    frc1, frc2 = st.columns(2)
    with frc1:
        st.session_state.footer_bg    = st.color_picker("Fundo",  st.session_state.footer_bg,    key="sb_fbg")
    with frc2:
        st.session_state.footer_color = st.color_picker("Texto",  st.session_state.footer_color, key="sb_fco")

    label_left = "Coluna esquerda" if st.session_state.footer_cols == 2 else "Texto do rodapé"
    st.caption(f"**{label_left}** — suporta `**negrito**`, `[link](url)`, `{{date}}`")
    st.session_state.footer_left = st.text_area("footer_l", st.session_state.footer_left,
                                                 height=68, label_visibility="collapsed", key="sb_fl")
    if st.session_state.footer_cols == 2:
        st.caption("**Coluna direita**")
        st.session_state.footer_right = st.text_area("footer_r", st.session_state.footer_right,
                                                      height=68, label_visibility="collapsed", key="sb_fr")

    st.caption("**Editorial** — nomes separados por vírgula ou quebra de linha (deixe vazio para omitir)")
    st.session_state.editorial = st.text_area("editorial_field", st.session_state.editorial,
                                               height=68, label_visibility="collapsed", key="sb_editorial",
                                               placeholder="Ex: João Silva, Maria Souza")

    st.markdown("**Atalhos:**")
    ex_cols = st.columns(2)
    examples = {
        "Simples":      "CEG — UnB · {date}",
        "Com site":     "CEG — UnB · [Site](https://ceg.unb.br) · {date}",
        "Links":        "[Site](https://ceg.unb.br) | [E-mail](mailto:ceg@unb.br)",
        "Negrito":      "**CEG — UnB** · Boletim de Conjuntura · {date}",
    }
    for i, (label, ex) in enumerate(examples.items()):
        with ex_cols[i % 2]:
            if st.button(label, key=f"ft_ex_{i}", use_container_width=True):
                st.session_state.footer_left = ex
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — Tabs: Editor | Preview completo | Guia
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📰 Boletim CEG-UnB")

t_editor, t_preview, t_guia = st.tabs(["✏️ Editor", "🔍 Preview completo", "📖 Guia de uso"])

cfg = build_cfg()

# ── TAB 1: EDITOR ─────────────────────────────────────────────────────────────
with t_editor:
    col_ed, col_pv = st.columns([1, 1], gap="large")

    with col_ed:
        st.markdown("##### Conteúdo Markdown")

        # Editor com aparência de IDE (dark)
        md_text = st.text_area(
            "editor_md",
            value=st.session_state.md_text,
            height=520,
            label_visibility="collapsed",
            key="md_input",
            help="Escreva o conteúdo em Markdown. Use # Tema, ## Seção, ### Artigo.",
        )
        st.session_state.md_text = md_text

        # Referência rápida de sintaxe
        with st.expander("📋 Referência rápida de sintaxe"):
            st.markdown("""
| Sintaxe | Resultado |
|---------|-----------|
| `# Tema` | Faixa colorida de tema |
| `## Seção` | Label de seção |
| `### Artigo` | Título de artigo |
| `**negrito**` | **negrito** |
| `*itálico*` | *itálico* |
| `~~tachado~~` | ~~tachado~~ |
| `` `código` `` | `código` |
| `[texto](url)` | link |
| `- item` | lista com marcador |
| `1. item` | lista numerada |
| `> texto` | citação em bloco |
| `\| col1 \| col2 \|` | tabela |
| `{center}…{/center}` | texto centralizado |
| `---` | linha divisória |
| `![alt](url)` | imagem |
| `$E = mc^2$` | LaTeX inline |
| `$$\frac{1}{2}$$` | LaTeX em bloco |
""")

        # ── Helpers de inserção ───────────────────────────────────────────────
        with st.expander("🖼️ Inserir imagem por link"):
            img_url = st.text_input("URL da imagem", placeholder="https://...", key="img_url")
            img_alt = st.text_input("Texto alternativo", placeholder="Descrição", key="img_alt", value="imagem")
            if st.button("➕ Inserir no editor", key="btn_img_insert"):
                if img_url.strip():
                    snippet = f"\n![{img_alt}]({img_url.strip()})\n"
                    st.session_state.md_text += snippet
                    st.rerun()
            if img_url.strip():
                st.code(f"![{img_alt}]({img_url.strip()})", language=None)

        with st.expander("📊 Inserir tabela"):
            tc1, tc2 = st.columns(2)
            with tc1:
                t_cols = st.number_input("Colunas", 2, 8, 3, key="tbl_cols")
            with tc2:
                t_rows = st.number_input("Linhas", 1, 20, 3, key="tbl_rows")
            headers = [st.text_input(f"Cabeçalho {i+1}", value=f"Coluna {i+1}", key=f"th_{i}") for i in range(int(t_cols))]
            if st.button("➕ Inserir tabela no editor", key="btn_tbl_insert"):
                sep  = "| " + " | ".join(["---"] * int(t_cols)) + " |"
                head = "| " + " | ".join(headers) + " |"
                rows = "\n".join(
                    "| " + " | ".join([""] * int(t_cols)) + " |"
                    for _ in range(int(t_rows))
                )
                snippet = f"\n{head}\n{sep}\n{rows}\n"
                st.session_state.md_text += snippet
                st.rerun()
            tbl_preview = "| " + " | ".join(headers) + " |\n"
            tbl_preview += "| " + " | ".join(["---"] * int(t_cols)) + " |\n"
            tbl_preview += ("| " + " | ".join(["…"] * int(t_cols)) + " |\n") * int(t_rows)
            st.code(tbl_preview, language=None)

        # Ações rápidas no editor
        st.markdown("**Ações rápidas**")
        qa1, qa2, qa3 = st.columns(3)
        with qa1:
            if st.button("🔄 Resetar exemplo", use_container_width=True, key="btn_reset"):
                st.session_state.md_text = SAMPLE_CONTENT
                st.rerun()
        with qa2:
            if st.button("🧹 Limpar editor", use_container_width=True, key="btn_clear"):
                st.session_state.md_text = ""
                st.rerun()
        with qa3:
            char_count = len(md_text)
            word_count = len(md_text.split())
            st.metric("Palavras", word_count, delta=None)

    with col_pv:
        st.markdown("##### Preview em tempo real")
        email_html = build_email_html(st.session_state.md_text, cfg)
        components.html(
            f'<div style="background:{cfg["bg_color"]};padding:20px 14px;border-radius:8px">'
            f'{email_html}</div>',
            height=580,
            scrolling=True,
        )

    st.divider()

    # ── Exportações ───────────────────────────────────────────────────────────
    st.markdown("##### Exportar")
    full_html = build_full_html(st.session_state.md_text, cfg)
    frag_html = build_email_html(st.session_state.md_text, cfg)

    ex1, ex2, ex3, ex4 = st.columns([2, 2, 2, 3])

    with ex1:
        st.markdown('<div class="action-btn">', unsafe_allow_html=True)
        st.download_button(
            "⬇️ HTML completo",
            data=full_html,
            file_name="boletim-ceg-unb.html",
            mime="text/html",
            use_container_width=True,
            key="dl_full",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with ex2:
        st.markdown('<div class="action-btn">', unsafe_allow_html=True)
        st.download_button(
            "📋 Fragmento Outlook",
            data=frag_html,
            file_name="boletim-outlook.html",
            mime="text/html",
            use_container_width=True,
            key="dl_frag",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with ex3:
        st.markdown('<div class="action-btn-accent">', unsafe_allow_html=True)
        if st.button("📄 Gerar PDF", use_container_width=True, key="btn_pdf"):
            with st.spinner("Gerando PDF scrollável…"):
                pdf_html = build_full_html(st.session_state.md_text, cfg, for_pdf=True)
                pdf_bytes = _make_pdf(pdf_html)
            if pdf_bytes:
                st.download_button(
                    "⬇️ Baixar PDF",
                    data=pdf_bytes,
                    file_name="boletim-ceg-unb.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_pdf",
                )
                st.caption("✅ PDF página única — ideal para rolamento no celular")
        st.markdown("</div>", unsafe_allow_html=True)

    with ex4:
        st.info("💡 Para Outlook: baixe o HTML completo → abra no Chrome → Ctrl+A → Ctrl+C → cole no email.", icon=None)


# ── TAB 2: PREVIEW COMPLETO ───────────────────────────────────────────────────
with t_preview:
    st.markdown("##### Preview completo da newsletter")
    st.caption("Renderização fiel ao email gerado. Altera a aparência na sidebar à esquerda.")

    # Preview do rodapé isolado
    with st.expander("🔍 Preview isolado do rodapé"):
        ftr = _render_footer(cfg)
        components.html(
            f'<div style="max-width:560px;margin:0 auto">{ftr}</div>',
            height=80,
        )

    # Preview completo
    email_full = build_email_html(st.session_state.md_text, cfg)
    components.html(
        f'<div style="background:{cfg["bg_color"]};padding:32px 16px;min-height:600px">'
        f'{email_full}</div>',
        height=720,
        scrolling=True,
    )


# ── TAB 3: GUIA ───────────────────────────────────────────────────────────────
with t_guia:
    with st.expander("∑ LaTeX — Guia de fórmulas matemáticas", expanded=False):
        st.markdown("""
**Sintaxe:** use `$...$` para fórmula inline e `$$...$$` para bloco centralizado.

> ⚠️ Para valores monetários (R\\$, US\\$, €), escreva normalmente — o `$` só vira LaTeX quando **não** é precedido por letra ou dígito.

---

#### Operações básicas

| Sintaxe | Resultado |
|---------|-----------|
| `$a + b$` | *a* + *b* |
| `$a - b$` | *a* − *b* |
| `$a \\times b$` | *a* × *b* |
| `$a \\div b$` | *a* ÷ *b* |
| `$a^{2}$` | *a*² |
| `$a_{i}$` | *aᵢ* |
| `$\\sqrt{x}$` | √*x* |
| `$\\sqrt[n]{x}$` | ⁿ√*x* |

---

#### Frações e somatórios

| Sintaxe | Descrição |
|---------|-----------|
| `$\\frac{a}{b}$` | Fração *a/b* |
| `$\\sum_{i=1}^{n} x_i$` | Somatório de *x*ᵢ |
| `$\\prod_{i=1}^{n} x_i$` | Produtório |
| `$\\int_{a}^{b} f(x)\\,dx$` | Integral definida |
| `$\\lim_{x \\to 0} f(x)$` | Limite |

---

#### Letras gregas comuns

| Sintaxe | Letra |
|---------|-------|
| `$\\alpha$` | α |
| `$\\beta$` | β |
| `$\\gamma$ / $\\Gamma$` | γ / Γ |
| `$\\delta$ / $\\Delta$` | δ / Δ |
| `$\\theta$` | θ |
| `$\\lambda$` | λ |
| `$\\mu$` | μ |
| `$\\sigma$ / $\\Sigma$` | σ / Σ |
| `$\\pi$ / $\\Pi$` | π / Π |
| `$\\omega$ / $\\Omega$` | ω / Ω |
| `$\\epsilon$` | ε |
| `$\\rho$` | ρ |

---

#### Economia e estatística — exemplos prontos

```
$\\hat{\\beta} = (X^{\\top}X)^{-1}X^{\\top}y$
```
```
$\\text{PIB} = C + I + G + (X - M)$
```
```
$$\\bar{x} = \\frac{1}{n}\\sum_{i=1}^{n} x_i$$
```
```
$$\\text{Var}(X) = E[X^2] - (E[X])^2$$
```
```
$$\\frac{\\partial \\ln L}{\\partial \\theta} = 0$$
```

---

#### Operadores e símbolos úteis

| Sintaxe | Símbolo |
|---------|---------|
| `$\\leq$` / `$\\geq$` | ≤ / ≥ |
| `$\\neq$` | ≠ |
| `$\\approx$` | ≈ |
| `$\\infty$` | ∞ |
| `$\\in$` | ∈ |
| `$\\subset$` | ⊂ |
| `$\\cup$` / `$\\cap$` | ∪ / ∩ |
| `$\\rightarrow$` | → |
| `$\\Rightarrow$` | ⇒ |
| `$\\text{palavra}$` | texto em fonte normal dentro da fórmula |
""")

    g1, g2 = st.columns([1, 1], gap="large")

    with g1:
        st.markdown("""
### 📝 Estrutura do Markdown

O editor reconhece 1, 2 ou 3 níveis de cabeçalho automaticamente:

| Símbolo | Função |
|---------|--------|
| `# Texto` | Tema — faixa colorida |
| `## Texto` | Seção — label dourado + linha |
| `### Texto` | Artigo — título em negrito |

Se usar só `#` e `##`, o parser trata `#` como seção e `##` como artigo.

---

### ✍️ Formatação inline

| Sintaxe | Resultado |
|---------|-----------|
| `**texto**` | **negrito** |
| `*texto*` | *itálico* |
| `***texto***` | ***negrito + itálico*** |
| `~~texto~~` | ~~tachado~~ |
| `` `código` `` | `código inline` |
| `[texto](url)` | link clicável |

---

### 🧱 Blocos especiais

**Citação:**
```
> Texto da citação
```

**Lista não-ordenada:**
```
- Item um
- Item dois
```

**Lista ordenada:**
```
1. Primeiro
2. Segundo
```

**Tabela:**
```
| Coluna 1 | Coluna 2 |
|----------|----------|
| dado     | dado     |
```

**Centralizado:**
```
{center}Texto centralizado{/center}
```

**Linha divisória:**
```
---
```

**Imagem:**
```
![Descrição](https://url-da-imagem.jpg)
```
""")

    with g2:
        st.markdown("""
### 💾 Perfis de aparência

Salve qualquer combinação de cores, fontes e rodapé como um **perfil nomeado**.
Perfis ficam na pasta `profiles/` como arquivos JSON — você pode versionar no Git ou compartilhar.

Para criar: configure a aparência na sidebar → expanda **Perfis de aparência** → dê um nome → **Salvar**.

---

### 📧 Como enviar pelo Outlook

#### ✅ Método recomendado — Chrome + Outlook Desktop

1. Clique em **"HTML completo"** para baixar
2. Abra o arquivo no **Google Chrome**
3. `Ctrl+A` → `Ctrl+C`
4. Abra o **Outlook Desktop**, novo email → cole com `Ctrl+V`
5. A formatação é preservada — envie normalmente

> ⚠️ Use o Outlook **Desktop** (não o web). O Outlook Web pode perder formatação.

---

#### 📄 Exportar como PDF

Clique em **"Gerar PDF"** na aba Editor. O PDF é gerado pelo WeasyPrint com fidelidade ao layout do email.

---

#### ⚙️ Configuração do Outlook

Verifique se o Outlook está em modo HTML:
`Arquivo → Opções → Email → Formato de mensagem → HTML`

---

#### 🖼️ Imagens no email

| Tipo | Como funciona |
|------|--------------|
| **Banner** (upload na sidebar) | Embutida em base64 — funciona offline |
| **Imagens no corpo** `![](url)` | URL externa — requer internet |

---

#### 📐 Compatibilidade técnica

- Largura máxima: **560px**
- Apenas `inline styles` — sem CSS externo
- Layout baseado em `<table>` — padrão Outlook-safe
- Testado em Outlook 2016, 2019, 365 e Gmail
""")
