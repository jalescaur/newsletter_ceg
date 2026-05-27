"""
app.py — Interface Streamlit do Gerador de Boletim CEG-UnB.
Multipage via st.tabs: Editor | Aparência | Rodapé | Guia de Uso

Execute com:  streamlit run app.py
"""

import base64
import streamlit as st
import streamlit.components.v1 as components

from renderer import build_email_html, build_full_html, _render_footer
from config import DEFAULT_CONFIG, FONT_OPTIONS, DATE_FORMAT_OPTIONS, SAMPLE_CONTENT

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(page_title="Boletim CEG-UnB", page_icon="📰",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  .block-container{padding-top:1rem;padding-bottom:.5rem}
  .stTextArea textarea{font-family:'Menlo','Consolas',monospace;
                       font-size:12.5px;line-height:1.75}
  .stTabs [data-baseweb="tab-list"]{gap:4px}
  .stTabs [data-baseweb="tab"]{padding:6px 18px;border-radius:6px 6px 0 0;font-size:13px}
  .stDownloadButton>button{width:100%;background:#0f0f0f!important;color:#fff!important;
    border:none!important;border-radius:6px!important;font-weight:600!important}
  div[data-testid="stExpander"]{border:1px solid #e0dbd4;border-radius:8px}
</style>
""", unsafe_allow_html=True)

# ── Session state helpers ────────────────────────────────────────────────────
def _ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

_ss("md_text",        SAMPLE_CONTENT)
_ss("footer_left",    DEFAULT_CONFIG["footer_left"])
_ss("footer_right",   DEFAULT_CONFIG["footer_right"])
_ss("banner_b64",     "")
_ss("banner_ext",     "png")
# Aparência
_ss("org",            DEFAULT_CONFIG["org"])
_ss("edition",        DEFAULT_CONFIG["edition"])
_ss("date_fmt_key",   list(DATE_FORMAT_OPTIONS.keys())[0])
_ss("banner_height",  int(DEFAULT_CONFIG["banner_height"].replace("px","")))
_ss("banner_fallback","#0f0f0f")
_ss("grad_left",      DEFAULT_CONFIG["grad_left"])
_ss("grad_right",     DEFAULT_CONFIG["grad_right"])
_ss("grad_h",         int(DEFAULT_CONFIG["grad_height"]))
_ss("accent",         DEFAULT_CONFIG["accent"])
_ss("highlight",      DEFAULT_CONFIG["highlight"])
_ss("body_text",      DEFAULT_CONFIG["body_text"])
_ss("primary",        DEFAULT_CONFIG["primary"])
_ss("bg_color",       DEFAULT_CONFIG["bg_color"])
_ss("font_label",     list(FONT_OPTIONS.keys())[0])
_ss("font_size",      int(DEFAULT_CONFIG["font_size"]))
_ss("line_height",    float(DEFAULT_CONFIG["line_height"]))
_ss("footer_cols",    1)
_ss("footer_bg",      DEFAULT_CONFIG["footer_bg"])
_ss("table_header_bg", DEFAULT_CONFIG["table_header_bg"])
_ss("table_event_bg",  DEFAULT_CONFIG["table_event_bg"])
_ss("use_temp_colors", DEFAULT_CONFIG["use_temp_colors"])
_ss("footer_color",   DEFAULT_CONFIG["footer_color"])


def build_cfg() -> dict:
    """Monta o dicionário de configuração a partir do session_state."""
    return {
        "org":                st.session_state.org,
        "edition":            st.session_state.edition,
        "date_format":        DATE_FORMAT_OPTIONS[st.session_state.date_fmt_key],
        "banner_img_b64":     st.session_state.banner_b64,
        "banner_img_ext":     st.session_state.banner_ext,
        "banner_height":      f"{st.session_state.banner_height}px",
        "banner_fallback_color": st.session_state.banner_fallback,
        "grad_left":          st.session_state.grad_left,
        "grad_right":         st.session_state.grad_right,
        "grad_height":        str(st.session_state.grad_h),
        "accent":             st.session_state.accent,
        "highlight":          st.session_state.highlight,
        "body_text":          st.session_state.body_text,
        "primary":            st.session_state.primary,
        "bg_color":           st.session_state.bg_color,
        "body_font":          FONT_OPTIONS[st.session_state.font_label],
        "font_size":          str(st.session_state.font_size),
        "line_height":        str(st.session_state.line_height),
        "footer_cols":        st.session_state.footer_cols,
        "footer_left":        st.session_state.footer_left,
        "footer_right":       st.session_state.footer_right,
        "footer_bg":          st.session_state.footer_bg,
        "footer_color":       st.session_state.footer_color,
        "table_header_bg":    st.session_state.get("table_header_bg", DEFAULT_CONFIG["table_header_bg"]),
        "table_event_bg":     st.session_state.get("table_event_bg",  DEFAULT_CONFIG["table_event_bg"]),
        "use_temp_colors":    st.session_state.get("use_temp_colors", True),
    }


# ── Tabs ──────────────────────────────────────────────────────────────────────
t_editor, t_aparencia, t_rodape, t_guia = st.tabs([
    "Editor", "Aparência", "Rodapé", "Guia de uso",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — EDITOR
# ══════════════════════════════════════════════════════════════════════════════
with t_editor:
    col_ed, col_pv = st.columns([1, 1], gap="large")

    with col_ed:
        st.markdown("##### Conteúdo Markdown")
        md_text = st.text_area(
            "md", value=st.session_state.md_text,
            height=540, label_visibility="collapsed", key="md_input"
        )
        st.session_state.md_text = md_text
        st.caption(
            "**#** Tema · **##** Seção · **###** Artigo &nbsp;|&nbsp; "
            "`**negrito**` `*itálico*` `~~tachado~~` `` `código` `` `[link](url)` "
            "`- lista` `1. numerada` `> citação` `|col1|col2|` "
            "`{center}...{/center}` `---` `![alt](url)`"
        )

    with col_pv:
        st.markdown("##### Preview")
        cfg = build_cfg()
        bg  = cfg["bg_color"]
        email_html = build_email_html(st.session_state.md_text, cfg)
        components.html(
            f'<div style="background:{bg};padding:20px 14px;border-radius:8px">{email_html}</div>',
            height=580, scrolling=True
        )

    st.divider()
    cfg2 = build_cfg()
    full_html = build_full_html(st.session_state.md_text, cfg2)
    frag_html = build_email_html(st.session_state.md_text, cfg2)

    dc1, dc2, dc3 = st.columns([2, 2, 3])
    with dc1:
        st.download_button("⬇️ Baixar HTML completo", data=full_html,
                           file_name="boletim-ceg-unb.html", mime="text/html",
                           use_container_width=True)
    with dc2:
        st.download_button("📋 Fragmento para Outlook", data=frag_html,
                           file_name="boletim-outlook.html", mime="text/html",
                           use_container_width=True)
    with dc3:
        st.info("💡 Para enviar pelo Outlook, veja a aba **📖 Guia de uso**.", icon=None)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — APARÊNCIA
# ══════════════════════════════════════════════════════════════════════════════
with t_aparencia:
    ap1, ap2 = st.columns([1, 1], gap="large")

    with ap1:
        # Banner
        st.markdown("#### 🖼️ Banner")
        uploaded = st.file_uploader("Imagem (PNG, JPG, GIF)",
                                    type=["png","jpg","jpeg","gif"],
                                    help="Será embutida em base64 — funciona offline no Outlook.")
        if uploaded:
            raw = uploaded.read()
            st.session_state.banner_b64 = base64.b64encode(raw).decode()
            st.session_state.banner_ext = uploaded.type.split("/")[-1].replace("jpeg","jpg")
            st.success(f"Banner carregado — {len(raw)//1024} KB")
        if st.session_state.banner_b64:
            if st.button("🗑️ Remover banner"):
                st.session_state.banner_b64 = ""
                st.rerun()

        bh = st.slider("Altura do banner (px)", 60, 360,
                       st.session_state.banner_height, key="s_banner_h")
        st.session_state.banner_height = bh

        bf = st.color_picker("Cor do banner (sem imagem)",
                              st.session_state.banner_fallback, key="s_banner_fb")
        st.session_state.banner_fallback = bf

        st.divider()

        # Faixa de degradê
        st.markdown("#### 🌈 Faixa de degradê")
        gc1, gc2, gc3 = st.columns([1,1,1])
        with gc1:
            gl = st.color_picker("Esquerda", st.session_state.grad_left, key="s_gl")
            st.session_state.grad_left = gl
        with gc2:
            gr = st.color_picker("Direita", st.session_state.grad_right, key="s_gr")
            st.session_state.grad_right = gr
        with gc3:
            gh = st.slider("Espessura px", 1, 16, st.session_state.grad_h, key="s_gh")
            st.session_state.grad_h = gh

        st.divider()

        # Data e identificação
        st.markdown("#### 📅 Data e identificação")
        org_v = st.text_input("Organização", st.session_state.org, key="s_org")
        st.session_state.org = org_v
        ed_v = st.text_input("Edição / Volume", st.session_state.edition, key="s_ed")
        st.session_state.edition = ed_v
        dfmt_v = st.radio("Formato de data", list(DATE_FORMAT_OPTIONS.keys()),
                          index=list(DATE_FORMAT_OPTIONS.keys()).index(st.session_state.date_fmt_key),
                          horizontal=True, label_visibility="collapsed", key="s_dfmt")
        st.session_state.date_fmt_key = dfmt_v

    with ap2:
        # Cores
        st.markdown("#### 🎨 Cores")
        cc1, cc2 = st.columns(2)
        with cc1:
            ac = st.color_picker("Acento (temas/links)",   st.session_state.accent,    key="s_ac")
            st.session_state.accent = ac
            hi = st.color_picker("Destaque (seções/data)", st.session_state.highlight, key="s_hi")
            st.session_state.highlight = hi
            bt = st.color_picker("Texto do corpo",         st.session_state.body_text, key="s_bt")
            st.session_state.body_text = bt
        with cc2:
            pr = st.color_picker("Rodapé / títulos",       st.session_state.primary,   key="s_pr")
            st.session_state.primary = pr
            bg = st.color_picker("Fundo da página",         st.session_state.bg_color,  key="s_bg")
            st.session_state.bg_color = bg

        st.divider()

        # Tipografia
        st.markdown("#### 🔤 Tipografia")
        fl = st.selectbox("Fonte", list(FONT_OPTIONS.keys()),
                          index=list(FONT_OPTIONS.keys()).index(st.session_state.font_label),
                          key="s_font")
        st.session_state.font_label = fl
        tc1, tc2 = st.columns(2)
        with tc1:
            fs = st.slider("Tamanho (px)", 12, 22, st.session_state.font_size, key="s_fs")
            st.session_state.font_size = fs
        with tc2:
            lh = st.slider("Entrelinha", 1.2, 2.5, st.session_state.line_height,
                           step=0.05, format="%.2f", key="s_lh")
            st.session_state.line_height = lh

        st.divider()
        st.markdown("#### 📊 Tabelas")
        tc1, tc2 = st.columns(2)
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            tbg = st.color_picker("Cabeçalho da tabela",
                                   st.session_state.table_header_bg, key="s_tbg")
            st.session_state.table_header_bg = tbg
        with tc2:
            tebg = st.color_picker("Linha de evento",
                                    st.session_state.table_event_bg, key="s_tebg")
            st.session_state.table_event_bg = tebg
        with tc3:
            utc = st.toggle("Cores de temperatura nos scores",
                             value=st.session_state.use_temp_colors, key="s_utc")
            st.session_state.use_temp_colors = utc
        st.caption("Cores de temperatura: 🟢 positivo → 🔴 negativo")

        st.divider()
        st.markdown("#### Preview rápido")
        cfg_ap = build_cfg()
        sample_preview = build_email_html(
            "## Exemplo de seção\n\n### Título do artigo\n\n"
            "Texto com **negrito**, *itálico* e [link](https://unb.br).\n\n"
            "- Item de lista\n- Outro item\n\n> Citação em destaque",
            cfg_ap
        )
        components.html(
            f'<div style="background:{cfg_ap["bg_color"]};padding:16px;border-radius:8px">'
            f'{sample_preview}</div>',
            height=380, scrolling=True
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — RODAPÉ
# ══════════════════════════════════════════════════════════════════════════════
with t_rodape:
    rd1, rd2 = st.columns([1, 1], gap="large")

    with rd1:
        st.markdown("#### 📌 Configuração do rodapé")

        fcols = st.radio("Layout", ["1 coluna", "2 colunas"],
                         index=st.session_state.footer_cols - 1,
                         horizontal=True, key="s_fcols")
        ncols = 2 if fcols == "2 colunas" else 1
        st.session_state.footer_cols = ncols

        frc1, frc2 = st.columns(2)
        with frc1:
            fbg = st.color_picker("Fundo do rodapé", st.session_state.footer_bg, key="s_fbg")
            st.session_state.footer_bg = fbg
        with frc2:
            fco = st.color_picker("Cor do texto", st.session_state.footer_color, key="s_fco")
            st.session_state.footer_color = fco

        st.markdown("**Coluna esquerda**" if ncols == 2 else "**Texto do rodapé**")
        st.caption("Suporta `**negrito**`, `*itálico*`, `[texto](url)` e `{date}` para data automática.")
        fl_v = st.text_area("footer_left_inp", value=st.session_state.footer_left,
                             height=80, label_visibility="collapsed", key="s_fl")
        st.session_state.footer_left = fl_v

        if ncols == 2:
            st.markdown("**Coluna direita**")
            fr_v = st.text_area("footer_right_inp", value=st.session_state.footer_right,
                                 height=80, label_visibility="collapsed", key="s_fr")
            st.session_state.footer_right = fr_v
        else:
            st.session_state.footer_right = ""

        st.markdown("**Exemplos rápidos:**")
        examples = {
            "Simples":       "CEG — UnB · {date}",
            "Com site":      "CEG — UnB · [Site](https://ceg.unb.br) · {date}",
            "Links duplos":  "[Site](https://ceg.unb.br) | [E-mail](mailto:ceg@unb.br)",
            "Negrito+data":  "**CEG — UnB** · Boletim de Conjuntura · {date}",
        }
        cols_ex = st.columns(len(examples))
        for i, (label, ex) in enumerate(examples.items()):
            with cols_ex[i]:
                if st.button(label, key=f"ex_{label}", use_container_width=True):
                    st.session_state.footer_left = ex
                    st.rerun()

    with rd2:
        st.markdown("#### Preview do rodapé")
        cfg_rd = build_cfg()
        ftr_only = _render_footer(cfg_rd)
        components.html(
            f'<div style="max-width:560px;margin:0 auto;font-family:sans-serif">{ftr_only}</div>',
            height=100
        )
        st.markdown("#### Preview completo")
        full_prev = build_email_html("## Seção\n\n### Artigo\n\nCorpo do texto de exemplo.", cfg_rd)
        components.html(
            f'<div style="background:{cfg_rd["bg_color"]};padding:16px;border-radius:8px">'
            f'{full_prev}</div>',
            height=380, scrolling=True
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — GUIA DE USO
# ══════════════════════════════════════════════════════════════════════════════
with t_guia:
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

**Duas colunas:**
```
| Coluna esquerda | Coluna direita |
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
### 📧 Como enviar pelo Outlook

O Outlook não abre `.html` como corpo diretamente —
o método mais confiável é copiar o conteúdo renderizado.

---

#### ✅ Método 1 — Chrome + Outlook Desktop *(recomendado)*

1. Clique em **"Baixar HTML completo"**
2. Abra o arquivo `.html` no **Google Chrome**
3. `Ctrl+A` → selecionar tudo
4. `Ctrl+C` → copiar
5. Abra o **Outlook Desktop** (não o web)
6. Novo email → clique no corpo → `Ctrl+V`
7. A formatação é preservada — envie normalmente

> ⚠️ Use o Outlook **Desktop**.
> O Outlook Web pode perder parte da formatação.

---

#### 🔁 Método 2 — Word como intermediário

1. Abra o `.html` no Chrome, copie tudo
2. Cole no **Word** e salve como `.docx`
3. No Outlook: **Inserir → Objeto → Texto do arquivo** → selecione o `.docx`

---

#### ⚙️ Configuração do Outlook

Verifique se o Outlook está em modo HTML:

`Arquivo → Opções → Email → Formato de mensagem → HTML`

---

#### 🖼️ Imagens no email

| Tipo | Como funciona |
|------|--------------|
| **Banner** (upload aqui) | Embutida em base64 — funciona sem internet |
| **Imagens no corpo** `![](url)` | URL externa — destinatário precisa de internet |

---

#### 🧪 Antes de enviar

- Envie para você mesmo primeiro
- Teste no celular (Outlook mobile)
- Clientes como Gmail podem renderizar diferente

---

#### 📐 Compatibilidade técnica

- Largura máxima: **560px**
- Apenas `inline styles` — sem CSS externo
- Layout baseado em `<table>` — padrão Outlook-safe
- Testado em Outlook 2016, 2019, 365 e Gmail
""")