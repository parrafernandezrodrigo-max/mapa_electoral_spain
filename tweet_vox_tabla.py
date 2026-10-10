"""
tweet_vox_tabla.py
Infográfico vertical 1200×1680 px con tabla completa por provincia:
  VOX 2023% | VOX 2026% | umbral D'Hondt | gap | confianza
Ordenado por nivel de confianza, luego por gap.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
from datetime import datetime
import pandas as pd

BG_DARK    = "#0D1117"
BG_CARD    = "#161B22"
ACCENT     = "#F4A261"
TEXT_WHITE = "#F0F6FC"
TEXT_MUTED = "#8B949E"
SEPARATOR  = "#30363D"
VOX_GREEN  = "#5A9A2E"

CONF_COLOR = {
    "MUY PROBABLE":  "#3FB950",
    "PROBABLE":      "#52C46A",
    "POSIBLE":       "#D29922",
    "POCO PROBABLE": "#F85149",
}
CONF_SHORT = {
    "MUY PROBABLE":  "MUY PROB",
    "PROBABLE":      "PROBABLE",
    "POSIBLE":       "POSIBLE ",
    "POCO PROBABLE": "POCO    ",
}

df = pd.read_csv(Path(__file__).parent / "data" / "vox_threshold_2026.csv")
CONF_ORDER = ["MUY PROBABLE", "PROBABLE", "POSIBLE", "POCO PROBABLE"]
df["conf_order"] = df["confidence"].map({c: i for i, c in enumerate(CONF_ORDER)})
df = df.sort_values(["conf_order", "gap_pp"]).reset_index(drop=True)

N = len(df)

# Canvas: 1200 wide, height enough for all rows
HDR_H    = 0.070   # fracción del total
ROW_H_PX = 24      # píxeles por fila
PAD_PX   = 14      # px arriba/abajo de header/footer
FIG_W    = 12
HDR_PX   = 110
FTR_PX   = 40
TOTAL_H_PX = HDR_PX + N * ROW_H_PX + 20 + FTR_PX + PAD_PX
FIG_H = TOTAL_H_PX / 100   # dpi=100

fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=100)
fig.patch.set_facecolor(BG_DARK)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
ax.set_facecolor(BG_DARK)

# Coordenadas en píxeles, y=0 abajo; trabajamos de arriba a abajo
def y(px_from_top): return FIG_H - px_from_top / 100

# ── Header ────────────────────────────────────────────────────────────────────
ax.add_patch(plt.Rectangle((0, y(HDR_PX)), FIG_W, HDR_PX/100,
                            color=VOX_GREEN, zorder=3))
ax.text(0.18, y(HDR_PX/2 - 8), "VOX — ¿Dónde entra, dónde no?",
        color=BG_DARK, fontsize=15, fontweight="bold", va="center", zorder=5)
ax.text(0.18, y(HDR_PX/2 + 14), "Umbral D'Hondt real por provincia · Elecciones noviembre 2026",
        color=BG_DARK, fontsize=9.5, va="center", zorder=5,
        fontstyle="italic")
ax.text(FIG_W - 0.18, y(HDR_PX/2 - 8),
        "Swing 40dB/El País/SER oct-26",
        color=BG_DARK+"CC", fontsize=8.5, ha="right", va="center", zorder=5)
ax.text(FIG_W - 0.18, y(HDR_PX/2 + 14),
        "N=800 · modelo swing uniforme sobre 23J",
        color=BG_DARK+"99", fontsize=7.5, ha="right", va="center", fontstyle="italic", zorder=5)

# ── Cabecera de columnas ─────────────────────────────────────────────────────
COL_HDR_Y = HDR_PX + 16

ax.add_patch(plt.Rectangle((0, y(COL_HDR_Y + 18)), FIG_W, 18/100,
                            color=SEPARATOR+"88", zorder=2))

# Posiciones X de columnas (en unidades de figura, 0–12)
CX = {
    "prov":    0.18,
    "esc":     3.55,
    "vox23":   4.40,
    "vox26":   5.50,
    "umbral":  6.65,
    "gap":     7.85,
    "conf":    9.30,
    "bar":    10.30,
}

def hdr_text(x, txt, align="center"):
    ax.text(x, y(COL_HDR_Y + 9), txt,
            color=TEXT_MUTED, fontsize=7.5, ha=align, va="center",
            fontweight="bold", zorder=5)

hdr_text(CX["prov"],  "PROVINCIA",  "left")
hdr_text(CX["esc"],   "ESC",        "center")
hdr_text(CX["vox23"], "VOX 23",     "center")
hdr_text(CX["vox26"], "VOX 26 est", "center")
hdr_text(CX["umbral"],"UMBRAL",     "center")
hdr_text(CX["gap"],   "FALTA",      "center")
hdr_text(CX["conf"],  "CONFIANZA",  "left")

ax.plot([0.10, FIG_W - 0.10],
        [y(COL_HDR_Y + 18), y(COL_HDR_Y + 18)],
        color=SEPARATOR, lw=0.6, zorder=4)

# ── Filas ─────────────────────────────────────────────────────────────────────
ROW_Y0 = COL_HDR_Y + 18 + 2
prev_conf = None

for i, r in df.iterrows():
    row_top = ROW_Y0 + i * ROW_H_PX
    row_cy  = row_top + ROW_H_PX / 2
    color   = CONF_COLOR[r["confidence"]]

    # Separador entre niveles de confianza
    if r["confidence"] != prev_conf:
        if prev_conf is not None:
            ax.plot([0.10, FIG_W - 0.10],
                    [y(row_top - 1), y(row_top - 1)],
                    color=color + "44", lw=1.0, zorder=4)
        # Etiqueta de nivel
        ax.text(CX["prov"], y(row_cy - ROW_H_PX * 0.1),
                f"── {r['confidence']} ──",
                color=color, fontsize=6.8, va="center",
                fontweight="bold", alpha=0.7, zorder=5)
        prev_conf = r["confidence"]
        row_cy_data = row_cy + ROW_H_PX * 0.38
    else:
        row_cy_data = row_cy

    # Fondo alternado
    if i % 2 == 0:
        ax.add_patch(plt.Rectangle(
            (0.08, y(row_top + ROW_H_PX)), FIG_W - 0.16, ROW_H_PX/100,
            color="#FFFFFF08", zorder=1))

    # Franja de color de confianza (lateral izquierdo)
    ax.add_patch(plt.Rectangle(
        (0.08, y(row_cy_data + ROW_H_PX*0.35)), 0.06, ROW_H_PX*0.7/100,
        color=color, zorder=4))

    fsize = 8.2

    # Provincia
    ax.text(CX["prov"], y(row_cy_data),
            r["provincia"], color=TEXT_WHITE, fontsize=fsize,
            fontweight="bold", va="center", zorder=5)

    # Escaños
    ax.text(CX["esc"], y(row_cy_data),
            str(r["escanos"]), color=TEXT_MUTED, fontsize=fsize,
            ha="center", va="center", zorder=5)

    # VOX 23%
    ax.text(CX["vox23"], y(row_cy_data),
            f"{r['vox_pct_19']:.1f}→{r['vox_pct_23']:.1f}%",
            color=TEXT_MUTED, fontsize=7.5, ha="center", va="center", zorder=5)

    # VOX 26 est
    ax.text(CX["vox26"], y(row_cy_data),
            f"{r['vox_pct_26']:.1f}%",
            color=TEXT_WHITE, fontsize=fsize, fontweight="bold",
            ha="center", va="center", zorder=5)

    # Umbral
    ax.text(CX["umbral"], y(row_cy_data),
            f"{r['umbral_pct']:.1f}%",
            color=TEXT_MUTED, fontsize=fsize, ha="center", va="center", zorder=5)

    # Gap
    gap_color = color
    gap_str = f"{r['gap_pp']:+.1f}pp"
    ax.text(CX["gap"], y(row_cy_data),
            gap_str, color=gap_color, fontsize=fsize, fontweight="bold",
            ha="center", va="center", zorder=5)

    # Confianza: mini-barra de puntos
    dots_total = 5
    dots_filled = {"MUY PROBABLE": 4, "PROBABLE": 3, "POSIBLE": 2, "POCO PROBABLE": 1}
    n_fill = dots_filled[r["confidence"]]
    for d in range(dots_total):
        dcol = color if d < n_fill else TEXT_MUTED + "44"
        ax.scatter([CX["bar"] + d * 0.22], [y(row_cy_data)],
                   s=18, color=dcol, zorder=5)

    # Escaños actuales vs estimados (pequeño)
    s23 = int(r["vox_seats_23"])
    s26 = int(r["vox_seats_26"])
    esc_str = f"{s23}→{s26}" if s23 != s26 else f"={s26}"
    esc_col = "#3FB950" if s26 > s23 else TEXT_MUTED if s26 == s23 else "#F85149"
    ax.text(FIG_W - 0.18, y(row_cy_data),
            esc_str, color=esc_col, fontsize=7.5, ha="right",
            va="center", fontweight="bold", zorder=5)

# ── Leyenda columnas (abajo) ──────────────────────────────────────────────────
legend_y = ROW_Y0 + N * ROW_H_PX + 10
ax.plot([0.10, FIG_W - 0.10], [y(legend_y), y(legend_y)],
        color=SEPARATOR, lw=0.6, zorder=4)
ax.text(0.18, y(legend_y + 9),
        "VOX 23 = trayectoria 19N→23J  ·  VOX 26 = swing uniforme sobre 23J  ·  "
        "Umbral = % mínimo D'Hondt para próximo escaño  ·  Falta = gap a cubrir  ·  "
        "Escaños (dcha) = 23→26 swing",
        color=TEXT_MUTED, fontsize=7, va="center", zorder=5)

# ── Footer ────────────────────────────────────────────────────────────────────
ax.text(FIG_W / 2, y(legend_y + 26),
        f"Encuesta 40dB / El País / SER oct. 2026  ·  mapa electoral spain  ·  "
        f"{datetime.today().strftime('%d/%m/%Y')}",
        color=TEXT_MUTED + "99", fontsize=7.5, ha="center", va="center", zorder=5)

out_dir = Path("tweets")
out_dir.mkdir(exist_ok=True)
out = out_dir / f"vox_tabla_provincias_{datetime.today().strftime('%Y%m%d')}.png"
plt.savefig(out, dpi=100, bbox_inches="tight",
            facecolor=BG_DARK, edgecolor="none")
plt.close(fig)
print(f"Imagen guardada: {out.resolve()}")
