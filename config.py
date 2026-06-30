"""
config.py — Configurações padrão, paletas, fontes, formatos de data.
Inclui persistência local via JSON para salvar/carregar perfis de aparência.
"""

from __future__ import annotations
import json
import os
from pathlib import Path

# ── Diretório de perfis ────────────────────────────────────────────────────────
PROFILES_DIR = Path("profiles")
PROFILES_DIR.mkdir(exist_ok=True)

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    # Identificação
    "org":            "CEG — UnB",
    "edition":        "Jun. 2026",
    "edition_date":        "",
    "next_edition_date":   "",
    # Produto
    "product_name":      "GPS Brasil",
    "product_tagline":   "O que importa no mundo. O que muda para o Brasil.",
    "product_name_size": 50,
    "product_name_bold": True,
    # Editorial
    "editorial":         "",
    # Banner
    "banner_img_b64": "",
    "banner_img_ext": "png",
    "banner_height":  "160px",
    # Cores (fixas pelo identidade CEG — editáveis na sidebar)
    "bg_color":       "#f2f2f2",
    "primary":        "#26619C",
    "accent":         "#26619C",
    "highlight":      "#acac95",
    "table_event_bg": "#acac95",
    "body_text":      "#2e2e2e",
    # Tipografia
    "body_font":      "Arial, Helvetica, sans-serif",
    "font_size":      "14",
    "line_height":    "1.5",
    # Tabela
    "table_header_bg": "#26619C",
    "use_temp_colors":  True,
    # Rodapé (fixo no renderer — mantidos para compatibilidade)
    "footer_cols":    1,
    "footer_left":    "CEG — UnB · {date}",
    "footer_right":   "",
    "footer_bg":      "#26619C",
    "footer_color":   "#acac95",
    # Banner fallback
    "banner_fallback": "#26619C",
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
    "Por extenso   (26 de junho de 2026)": "extenso",
    "Precisa       (junho de 2026)":        "precisa",
    "DD/MM/AAAA    (26/06/2026)":           "ddmmyyyy",
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

{center}Próxima edição: **julho de 2026**{/center}
"""

FOOTER_SAMPLE = "CEG — UnB · {date} | [Site](https://ceg.unb.br) | [Contato](mailto:boletim@ceg.unb.br)"


# ── Persistência de perfis ────────────────────────────────────────────────────

def list_profiles() -> list[str]:
    """Retorna lista de perfis salvos (sem extensão)."""
    return sorted(
        p.stem for p in PROFILES_DIR.glob("*.json")
    )

def save_profile(name: str, cfg: dict) -> None:
    """Salva um perfil de configuração (exclui banner_img_b64 por tamanho)."""
    safe = {k: v for k, v in cfg.items() if k != "banner_img_b64"}
    path = PROFILES_DIR / f"{name}.json"
    path.write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")

def load_profile(name: str) -> dict:
    """Carrega um perfil e mescla com DEFAULT_CONFIG."""
    path = PROFILES_DIR / f"{name}.json"
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    data = json.loads(path.read_text(encoding="utf-8"))
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    return merged

def delete_profile(name: str) -> None:
    path = PROFILES_DIR / f"{name}.json"
    if path.exists():
        path.unlink()
