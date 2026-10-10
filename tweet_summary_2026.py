"""
tweet_summary_2026.py
Genera un card 1200×675 px para Twitter con la estimación de escaños noviembre 2026
comparada con los resultados reales del 23J de 2023.

Fuente estimación: encuesta 40dB / El País / SER, octubre 2026.
Metodología: swing uniforme proporcional sobre resultados reales 23J.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
from datetime import datetime

# ─── Datos ────────────────────────────────────────────────────────────────────
# Resultados reales 23J 2023
RESULTS_2023 = [
    {"sigla": "PP",      "label": "PP",      "color": "#1B4F8A", "seats": 137},
    {"sigla": "PSOE",    "label": "PSOE",    "color": "#D62828", "seats": 121},
    {"sigla": "VOX",     "label": "Vox",     "color": "#5A9A2E", "seats":  33},
    {"sigla": "SUMAR",   "label": "Sumar",   "color": "#C0226E", "seats":  31},
    {"sigla": "OTROS",   "label": "Otros",   "color": "#5B6474", "seats":  28},
]

# Estimación 2026 (swing uniforme, base central)
ESTIMATE_2026 = [
    {"sigla": "PP",      "label": "PP",      "color": "#1B4F8A", "seats": 131},
    {"sigla": "PSOE",    "label": "PSOE",    "color": "#D62828", "seats": 112},
    {"sigla": "VOX",     "label": "Vox",     "color": "#5A9A2E", "seats":  64},
    {"sigla": "SUMAR",   "label": "Sumar/FA","color": "#C0226E", "seats":   5},
    {"sigla": "PODEMOS", "label": "Podemos", "color": "#7B2D8B", "seats":   2},
    {"sigla": "OTROS",   "label": "Otros",   "color": "#5B6474", "seats":  36},
]

# Rango de incertidumbre VOX ±5 pp (de sensibilidad_2026.py)
RANGE_2026 = {
    "PP":    (118, 144),
    "PSOE":  (98,  122),
    "VOX":   (42,   91),
}
BLOC_BASE   = {"dcha": 195, "izq": 119}
BLOC_RANGE  = {"dcha": (186, 209), "izq": (105, 129)}

TOTAL = 350
MAJ   = 176

# ─── Tema (idéntico a tweet_gen.py) ──────────────────────────────────────────
BG_DARK    = "#0D1117"
BG_CARD    = "#161B22"
ACCENT     = "#F4A261"
TEXT_WHITE = "#F0F6FC"
TEXT_MUTED = "#8B949E"
SEPARATOR  = "#30363D"
TEXT_GREEN = "#3FB950"
TEXT_RED   = "#F85149"


def draw_seat_bar(ax, parties, y_center, bar_h, bar_x0, bar_x1,
                  total, label_left, show_maj=False, maj=176):
    """Dibuja una barra apilada horizontal de escaños."""
    bar_w = bar_x1 - bar_x0
    gap   = 0.0025
    cursor = bar_x0

    ax.text(bar_x0 - 0.012, y_center, label_left,
            color=TEXT_MUTED, fontsize=9, ha="right", va="center")

    for p in parties:
        seg_w = max((p["seats"] / total) * bar_w - gap, 0.001)
        ax.add_patch(FancyBboxPatch(
            (cursor, y_center - bar_h / 2), seg_w, bar_h,
            boxstyle="round,pad=0.003",
            facecolor=p["color"], edgecolor=BG_CARD, linewidth=1.5, zorder=5,
        ))
        pct = p["seats"] / total
        cx  = cursor + seg_w / 2
        if pct >= 0.06:
            ax.text(cx, y_center, str(p["seats"]),
                    color="white", fontsize=10, fontweight="bold",
                    ha="center", va="center", zorder=6)
        cursor += seg_w + gap

    if show_maj:
        maj_x = bar_x0 + (maj / total) * bar_w
        ax.plot([maj_x, maj_x],
                [y_center - bar_h / 2 - 0.018, y_center + bar_h / 2 + 0.018],
                color=ACCENT, linewidth=1.2, linestyle="--", zorder=7, alpha=0.7)
        ax.text(maj_x, y_center + bar_h / 2 + 0.026,
                f"M.A. {maj}", color=ACCENT, fontsize=7.5,
                ha="center", va="bottom", zorder=7)


def draw_delta_dots(ax, parties_2023, parties_2026, y_row, bar_x0, bar_x1, total):
    """Fila de puntos con delta de escaños por partido."""
    all_siglas = [p["sigla"] for p in parties_2026]
    seats_23 = {p["sigla"]: p["seats"] for p in parties_2023}
    n = len(parties_2026)
    slot_w = (bar_x1 - bar_x0) / n

    for i, p in enumerate(parties_2026):
        cx    = bar_x0 + (i + 0.5) * slot_w
        delta = p["seats"] - seats_23.get(p["sigla"], 0)
        ax.scatter([cx], [y_row + 0.025], color=p["color"], s=60, zorder=6)
        ax.text(cx, y_row + 0.025, str(p["seats"]),
                color=TEXT_WHITE, fontsize=9, fontweight="bold",
                ha="center", va="center", zorder=7)

        # Delta badge
        if delta > 0:
            d_color = TEXT_GREEN
            d_str   = f"+{delta}"
        elif delta < 0:
            d_color = TEXT_RED
            d_str   = str(delta)
        else:
            d_color = TEXT_MUTED
            d_str   = "±0"

        ax.text(cx, y_row - 0.012, d_str,
                color=d_color, fontsize=8.5, fontweight="bold",
                ha="center", va="center", zorder=7)
        ax.text(cx, y_row - 0.038, p["label"],
                color=TEXT_MUTED, fontsize=8,
                ha="center", va="center", zorder=7)


# ─── Canvas ───────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(12, 6.75), dpi=100)
fig.patch.set_facecolor(BG_DARK)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
ax.set_facecolor(BG_DARK)

CARD_X0, CARD_X1 = 0.025, 0.975
CARD_Y0, CARD_Y1 = 0.030, 0.970
PAD_X = 0.050

# Card
ax.fill_betweenx([CARD_Y0, CARD_Y1], CARD_X0, CARD_X1, color=BG_CARD, zorder=1)
ax.add_patch(FancyBboxPatch(
    (CARD_X0, CARD_Y0), CARD_X1 - CARD_X0, CARD_Y1 - CARD_Y0,
    boxstyle="round,pad=0.012", facecolor="none",
    edgecolor=SEPARATOR, linewidth=1.5, zorder=2,
))

# ─── Header strip ─────────────────────────────────────────────────────────────
HDR_Y0, HDR_Y1 = 0.870, 0.970
ax.fill_betweenx([HDR_Y0, HDR_Y1], CARD_X0, CARD_X1, color=ACCENT, zorder=3)
HDR_CY = (HDR_Y0 + HDR_Y1) / 2
ax.text(PAD_X + 0.005, HDR_CY,
        "ESTIMACIÓN ELECTORAL — NOVIEMBRE 2026",
        color=BG_DARK, fontsize=13.5, fontweight="bold", va="center", zorder=5)
ax.text(1 - PAD_X - 0.005, HDR_CY,
        "Encuesta 40dB · El País / SER · Oct. 2026",
        color=BG_DARK, fontsize=9, va="center", ha="right",
        fontstyle="italic", zorder=5)

# ─── Subtítulo metodológico ───────────────────────────────────────────────────
ax.text(0.5, 0.832,
        "Modelo swing uniforme sobre resultados reales del 23J de 2023  ·  N=800 entrevistas nacionales",
        color=TEXT_MUTED, fontsize=9, ha="center", va="center", zorder=5)

# Separador 1
SEP1_Y = 0.805
ax.plot([PAD_X, 1 - PAD_X], [SEP1_Y, SEP1_Y], color=SEPARATOR, lw=0.8)

# ─── Barras de escaños ────────────────────────────────────────────────────────
BAR_X0 = PAD_X + 0.065
BAR_X1 = 1 - PAD_X
BAR_H  = 0.072

draw_seat_bar(ax, ESTIMATE_2026, 0.725, BAR_H, BAR_X0, BAR_X1,
              TOTAL, "2026\nestimado", show_maj=True, maj=MAJ)
draw_seat_bar(ax, RESULTS_2023,  0.600, BAR_H, BAR_X0, BAR_X1,
              TOTAL, "2023\nreal", show_maj=False)

# ─── Separador 2 ─────────────────────────────────────────────────────────────
SEP2_Y = 0.535
ax.plot([PAD_X, 1 - PAD_X], [SEP2_Y, SEP2_Y], color=SEPARATOR, lw=0.8)

# ─── Fila de deltas por partido ───────────────────────────────────────────────
draw_delta_dots(ax, RESULTS_2023, ESTIMATE_2026, 0.455, BAR_X0, BAR_X1, TOTAL)

ax.text(BAR_X0 - 0.012, 0.455 + 0.025, "Esc.",
        color=TEXT_MUTED, fontsize=8, ha="right", va="center")
ax.text(BAR_X0 - 0.012, 0.455 - 0.012, "Δ",
        color=TEXT_MUTED, fontsize=8, ha="right", va="center")

# ─── Separador 3 ─────────────────────────────────────────────────────────────
SEP3_Y = 0.365
ax.plot([PAD_X, 1 - PAD_X], [SEP3_Y, SEP3_Y], color=SEPARATOR, lw=0.8)

# ─── Bloque de incertidumbre ──────────────────────────────────────────────────
UNCT_Y = 0.336
ax.text(PAD_X, UNCT_Y,
        "INCERTIDUMBRE REAL:  ¿y si el swing de VOX varía ±5 pp?",
        color=ACCENT, fontsize=9.5, fontweight="bold", va="center", zorder=5)

# Tabla de rangos compacta — 3 partidos a la izquierda, bloques a la derecha
parties_range = [
    ("PP",    "#1B4F8A", 131, 118, 144),
    ("PSOE",  "#D62828", 112,  98, 122),
    ("VOX",   "#5A9A2E",  64,  42,  91),
]
RANGE_Y = 0.285
COL0 = PAD_X + 0.005
COL_W = 0.280   # ancho por partido

for i, (lbl, col, base, lo, hi) in enumerate(parties_range):
    rx = COL0 + i * COL_W
    ax.text(rx, RANGE_Y,
            f"{lbl}  ", color=col, fontsize=10, fontweight="bold",
            va="center", ha="left")
    ax.text(rx + 0.042, RANGE_Y,
            f"{base} esc.  →  {lo}–{hi}",
            color=TEXT_WHITE, fontsize=8.5, va="center", ha="left")

# Bloques políticos — columna derecha
BLK_X = COL0 + 3 * COL_W + 0.015
ax.text(BLK_X, RANGE_Y + 0.025,
        f"Derecha   {BLOC_BASE['dcha']} esc.  ({BLOC_RANGE['dcha'][0]}–{BLOC_RANGE['dcha'][1]})",
        color="#5B8DB8", fontsize=8.5, va="center")
ax.text(BLK_X, RANGE_Y - 0.025,
        f"Izquierda  {BLOC_BASE['izq']} esc.  ({BLOC_RANGE['izq'][0]}–{BLOC_RANGE['izq'][1]})",
        color="#D62828", fontsize=8.5, va="center")

# ─── Separador 4 ─────────────────────────────────────────────────────────────
SEP4_Y = 0.210
ax.plot([PAD_X, 1 - PAD_X], [SEP4_Y, SEP4_Y], color=SEPARATOR, lw=0.8)

# ─── Nota de cautela ─────────────────────────────────────────────────────────
CAUT_TXT = (
    "⚠  Circunscripciones pequeñas (≤4 esc.): error muestral provincial muy alto — "
    "38 de 52 circunscripciones cambian con ±5 pp en VOX  ·  "
    "La encuesta (N=800) no permite estimar voto provincial fiable"
)
ax.text(0.5, 0.170, CAUT_TXT,
        color=TEXT_MUTED, fontsize=8, ha="center", va="center",
        style="italic", zorder=5, wrap=True)

# ─── Leyenda de partidos ──────────────────────────────────────────────────────
LEG_PARTIES = ESTIMATE_2026
n_leg  = len(LEG_PARTIES)
slot_w = (1 - 2 * PAD_X) / n_leg
LEG_Y  = 0.108
for i, p in enumerate(LEG_PARTIES):
    lx = PAD_X + (i + 0.5) * slot_w
    ax.scatter([lx - 0.022], [LEG_Y], color=p["color"], s=50, zorder=6)
    ax.text(lx - 0.010, LEG_Y, p["label"],
            color=TEXT_MUTED, fontsize=8.5, va="center", zorder=6)

# ─── Footer ───────────────────────────────────────────────────────────────────
ax.text(0.5, CARD_Y0 + 0.028,
        f"mapa electoral spain  ·  swing D'Hondt provincial  ·  "
        f"{datetime.today().strftime('%d/%m/%Y')}",
        color=TEXT_MUTED, fontsize=8, ha="center", va="center", zorder=5)

# ─── Guardar ─────────────────────────────────────────────────────────────────
out_dir = Path("tweets")
out_dir.mkdir(exist_ok=True)
out = out_dir / f"estimacion_2026_{datetime.today().strftime('%Y%m%d')}.png"
plt.savefig(out, dpi=100, bbox_inches="tight",
            facecolor=BG_DARK, edgecolor="none")
plt.close(fig)
print(f"Imagen guardada: {out.resolve()}")
