"""Elements communs aux pages du site : chemins, palette, mise en forme Plotly et tableaux."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from IPython.display import HTML

RACINE = Path("..").resolve()
METRIQUES = RACINE / "outputs" / "metriques"
DATASET = RACINE / "data" / "processed" / "dataset_quotidien.parquet"

# Palette categorielle validee (ordre fixe), encre et surface claires.
SERIE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
ENCRE, ENCRE_2, MUET = "#0b0b0b", "#52514e", "#898781"
GRILLE, AXE, SURFACE = "#e1e0d9", "#c3c2b7", "#fcfcfb"
DIVERGENT = [[0, "#1c5cab"], [0.5, "#f0efec"], [1, "#e34948"]]
SEQUENTIEL = [[0, "#f0efec"], [0.35, "#9ec5f4"], [0.7, "#3987e5"], [1, "#104281"]]

FAMILLES = {"climat": "Climat", "geopolitique": "Géopolitique", "biodiversite": "Biodiversité",
            "couts_production": "Coûts de production", "production_offre": "Production / offre",
            "marche_finance": "Marché et finance", "investisseurs_biais": "Investisseurs et biais",
            "demande_substituts": "Demande et substituts"}

pio.templates["cacao"] = go.layout.Template(layout=go.Layout(
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=ENCRE_2),
    title=dict(font=dict(size=16, color=ENCRE), x=0, xanchor="left"),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, colorway=SERIE, separators=", ",
    xaxis=dict(gridcolor=GRILLE, linecolor=AXE, zerolinecolor=AXE, tickfont=dict(color=MUET)),
    yaxis=dict(gridcolor=GRILLE, linecolor=AXE, zerolinecolor=AXE, tickfont=dict(color=MUET)),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
    hoverlabel=dict(bgcolor="white", font_color=ENCRE, bordercolor=AXE),
    margin=dict(l=60, r=20, t=70, b=50)))
pio.templates.default = "cacao"


def tableau(df: pd.DataFrame, decimales: int = 3) -> HTML:
    """Tableau HTML simple, nombres arrondis, sans index."""
    return HTML(df.round(decimales).to_html(index=False, classes="table table-sm table-striped", border=0,
                                            na_rep="", justify="left"))


def lire(nom: str) -> pd.DataFrame:
    return pd.read_csv(METRIQUES / nom)
