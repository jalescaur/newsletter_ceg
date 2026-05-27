"""
config.py — Configurações padrão, paletas, fontes, formatos de data.
"""

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    # Identificação
    "org":            "CEG — UnB",
    "edition":        "Mai. 2026",
    "date_format":    "extenso",       # extenso | precisa | ddmmyyyy
    # Banner
    "banner_img_b64": "",              # base64 da imagem; "" = sem imagem
    "banner_img_ext": "png",           # extensão para o mime type
    "banner_height":  "180px",         # altura do banner em CSS
    # Faixa de degradê
    "grad_left":      "#00a99d",
    "grad_right":     "#b5a98a",
    "grad_height":    "4",             # px
    # Cores
    "bg_color":       "#f0ede8",
    "primary":        "#0f0f0f",       # rodapé + títulos de artigo
    "accent":         "#00a99d",       # rótulos de tema
    "highlight":      "#b5a98a",       # labels de seção / data
    "table_event_bg": "#b5a98a",       # cor da linha de evento nas tabelas
    "body_text":      "#3a3530",       # cor padrão do corpo
    # Tipografia
    "body_font":      "Georgia, 'Times New Roman', serif",
    "font_size":      "14",            # px
    "line_height":    "1.78",
    # Tabela
    "table_header_bg": "#00a99d",  # cor do cabeçalho das tabelas (independente do accent)
    "use_temp_colors":  True,       # cores de temperatura nos scores
    # Rodapé
    "footer_cols":    1,               # 1 ou 2 colunas
    "footer_left":    "CEG — UnB · {date}",
    "footer_right":   "",
    "footer_bg":      "#0f0f0f",
    "footer_color":   "#b5a98a",
}

# ── Fontes web-safe ───────────────────────────────────────────────────────────
FONT_OPTIONS = {
    "Georgia (serifada — padrão)":         "Georgia, 'Times New Roman', serif",
    "Times New Roman (serifada clássica)": "'Times New Roman', Times, serif",
    "Palatino (serifada elegante)":        "Palatino Linotype, Book Antiqua, Palatino, serif",
    "Arial (sem serifa moderna)":          "Arial, Helvetica, sans-serif",
    "Trebuchet MS (sem serifa suave)":     "'Trebuchet MS', sans-serif",
    "Verdana (sem serifa legível)":        "Verdana, Geneva, sans-serif",
    "Courier New (monoespaçada)":          "'Courier New', Courier, monospace",
}

# ── Formatos de data ──────────────────────────────────────────────────────────
DATE_FORMAT_OPTIONS = {
    "Por extenso   (26 de maio de 2026)": "extenso",
    "Precisa       (maio de 2026)":        "precisa",
    "DD/MM/AAAA    (26/05/2026)":          "ddmmyyyy",
}

# ── Conteúdo de exemplo ───────────────────────────────────────────────────────
SAMPLE_CONTENT = """\
# COMÉRCIO EXTERIOR

## Estreito de Ormuz e exportações Petrobras

Brent oscila em torno de **US$110/bbl**. Relatório da IEA registra aumento de *3,5 mb/d* nas exportações do Atlântico Norte, com ganhos notáveis do Brasil. A Petrobras reorientou mais de **60%** de suas exportações para a China.

## Acordo Mercosul-UE

A Comissão Europeia rebaixou sua previsão de crescimento do Eurozone de 1,2% para **0,9%** em 2026. O acordo representa a maior abertura de mercado da história recente:

- Tarifa zero imediata para manufaturados
- Cotas ampliadas para carnes e proteínas
- Acesso facilitado a lítio, nióbio e cobre

> O vetor de risco mais relevante é o EUDR, que exige rastreabilidade da cadeia produtiva.

# POLÍTICA MACROECONÔMICA

## Diesel e subsídio fiscal

Pela **MP 1.340/2026**, o governo brasileiro zera PIS/Cofins sobre diesel. O IPCA-15 de março mostrou que o diesel subiu ~~2,5%~~ **3,77%** apesar dos subsídios.

{center}Próxima edição: **junho de 2026**{/center}
"""

FOOTER_SAMPLE = "CEG — UnB · {date} | [Site](https://ceg.unb.br) | [Contato](mailto:boletim@ceg.unb.br)"