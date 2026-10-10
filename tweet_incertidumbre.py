"""
tweet_incertidumbre.py
Card 1200x675 px explicando los principios de confianza por tipo de circunscripción.
No es un gráfico de datos — es una slide metodológica/editorial.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
from pathlib import Path
from datetime import datetime

# ─── Tema ─────────────────────────────────────────────────────────────────────
BG_DARK    = "#0D1117"
BG_CARD    = "#161B22"
ACCENT     = "#F4A261"
TEXT_WHITE = "#F0F6FC"
TEXT_MUTED = "#8B949E"
SEPARATOR  = "#30363D"
GREEN      = "#3FB950"
YELLOW     = "#D29922"
RED        = "#F85149"

# ─── Datos de los tres niveles ────────────────────────────────────────────────
TIERS = [
    {
        "color":   GREEN,
        "label":   "ALTA CONFIANZA",
        "provincias": "Madrid · Barcelona · Valencia",
        "seats":   "85 escaños  (24%)",
        "n_prov":  "3 provincias  ·  16-37 esc. cada una",
        "why":     [
            "El swing de ±5pp mueve 1-3 esc. de 32-37",
            "Muestra encuesta: N≥183 por provincia",
            "D'Hondt diluye el error en muchos partidos",
        ],
        "caveat":  None,
    },
    {
        "color":   YELLOW,
        "label":   "CONFIANZA MEDIA",
        "provincias": "Alicante, Sevilla, Málaga, Murcia,\nCádiz, A Coruña, Las Palmas, Bizkaia, Baleares",
        "seats":   "~80 escaños  (23%)",
        "n_prov":  "9 provincias  ·  8-12 esc. cada una",
        "why":     [
            "Swing ±5pp mueve 1-2 escaños por provincia",
            "Muestra encuesta: N entre 32 y 55",
            "El error se puede acotar razonablemente",
        ],
        "caveat":  "Atención a VOX: en 4 de estas entra o no según ±3pp",
    },
    {
        "color":   RED,
        "label":   "INCERTIDUMBRE ALTA",
        "provincias": "40 provincias  ·  de 2 a 7 escaños",
        "seats":   "~185 escaños  (53%)",
        "n_prov":  "Incluye Burgos, León, Cuenca, Soria, Teruel...",
        "why":     [
            "Umbral D'Hondt real: 20-25% para el último esc.",
            "VOX estimado al 19%: está justo en el filo",
            "Muestra encuesta: N entre 2 y 25 personas",
        ],
        "caveat":  "38 de estas cambian resultado con ±5pp en VOX",
    },
]

# ─── Canvas ───────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(12, 6.75), dpi=100)
fig.patch.set_facecolor(BG_DARK)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

CARD_X0, CARD_X1 = 0.025, 0.975
CARD_Y0, CARD_Y1 = 0.030, 0.970
PAD = 0.040

ax.fill_betweenx([CARD_Y0, CARD_Y1], CARD_X0, CARD_X1, color=BG_CARD, zorder=1)
ax.add_patch(FancyBboxPatch(
    (CARD_X0, CARD_Y0), CARD_X1 - CARD_X0, CARD_Y1 - CARD_Y0,
    boxstyle="round,pad=0.012", facecolor="none",
    edgecolor=SEPARATOR, linewidth=1.5, zorder=2,
))

# ─── Header ───────────────────────────────────────────────────────────────────
HDR_Y0, HDR_Y1 = 0.875, 0.970
ax.fill_betweenx([HDR_Y0, HDR_Y1], CARD_X0, CARD_X1, color=ACCENT, zorder=3)
HDR_CY = (HDR_Y0 + HDR_Y1) / 2
ax.text(PAD + 0.010, HDR_CY,
        "¿Qué circunscripciones se pueden estimar con confianza?",
        color=BG_DARK, fontsize=13, fontweight="bold", va="center", zorder=5)
ax.text(1 - PAD - 0.008, HDR_CY,
        "Elecciones generales · Nov. 2026",
        color=BG_DARK, fontsize=9, va="center", ha="right",
        fontstyle="italic", zorder=5)

# ─── Subtítulo ────────────────────────────────────────────────────────────────
ax.text(0.5, 0.842,
        "El sistema D'Hondt con circunscripciones provinciales crea tres realidades muy distintas",
        color=TEXT_MUTED, fontsize=9, ha="center", va="center")

ax.plot([PAD, 1 - PAD], [0.815, 0.815], color=SEPARATOR, lw=0.8)

# ─── Tres columnas ────────────────────────────────────────────────────────────
COL_W = (1 - 2 * PAD - 0.030) / 3   # ancho de cada columna
COL_GAP = 0.015
COL_Y_TOP = 0.795
COL_Y_BOT = 0.210

for i, tier in enumerate(TIERS):
    col_x0 = PAD + i * (COL_W + COL_GAP)
    col_x1 = col_x0 + COL_W
    col_cx = (col_x0 + col_x1) / 2

    # Fondo de columna
    col_bg = tier["color"] + "18"   # ~10% opacidad hex
    ax.add_patch(FancyBboxPatch(
        (col_x0, COL_Y_BOT - 0.005), COL_W, COL_Y_TOP - COL_Y_BOT + 0.008,
        boxstyle="round,pad=0.008",
        facecolor=col_bg, edgecolor=tier["color"] + "55", linewidth=1.2, zorder=3,
    ))

    # Badge de nivel
    badge_y = COL_Y_TOP - 0.025
    ax.add_patch(FancyBboxPatch(
        (col_x0 + 0.010, badge_y - 0.020), COL_W - 0.020, 0.040,
        boxstyle="round,pad=0.005",
        facecolor=tier["color"], edgecolor="none", zorder=4,
    ))
    ax.text(col_cx, badge_y, tier["label"],
            color=BG_DARK, fontsize=9, fontweight="bold",
            ha="center", va="center", zorder=5)

    y = badge_y - 0.055
    # Escaños en juego (hero number)
    ax.text(col_cx, y, tier["seats"],
            color=tier["color"], fontsize=12, fontweight="bold",
            ha="center", va="center", zorder=5)

    y -= 0.050
    ax.text(col_cx, y, tier["n_prov"],
            color=TEXT_MUTED, fontsize=8, ha="center", va="center", zorder=5)

    y -= 0.040
    ax.plot([col_x0 + 0.015, col_x1 - 0.015], [y, y],
            color=tier["color"] + "55", lw=0.8, zorder=4)

    y -= 0.010
    # Provincias
    for line in tier["provincias"].split("\n"):
        y -= 0.032
        ax.text(col_cx, y, line,
                color=TEXT_WHITE, fontsize=8, ha="center", va="center",
                fontweight="bold", zorder=5)

    y -= 0.035
    ax.plot([col_x0 + 0.015, col_x1 - 0.015], [y, y],
            color=tier["color"] + "55", lw=0.8, zorder=4)

    # Bullets de por qué
    for bullet in tier["why"]:
        y -= 0.036
        ax.text(col_x0 + 0.018, y, "·", color=tier["color"],
                fontsize=11, va="center", zorder=5)
        ax.text(col_x0 + 0.030, y, bullet,
                color=TEXT_MUTED, fontsize=7.8, va="center", zorder=5)

    # Caveat (si existe)
    if tier["caveat"]:
        cav_y = COL_Y_BOT + 0.040
        ax.add_patch(FancyBboxPatch(
            (col_x0 + 0.010, cav_y - 0.022), COL_W - 0.020, 0.048,
            boxstyle="round,pad=0.005",
            facecolor=tier["color"] + "22", edgecolor=tier["color"] + "88",
            linewidth=0.8, zorder=4,
        ))
        ax.text(col_cx, cav_y, tier["caveat"],
                color=tier["color"], fontsize=7.5, ha="center", va="center",
                style="italic", zorder=5, wrap=True)

# ─── Separador y barra de resumen inferior ────────────────────────────────────
ax.plot([PAD, 1 - PAD], [0.195, 0.195], color=SEPARATOR, lw=0.8)

# Mini-barra visual de los tres bloques de certeza (proporcional a escaños)
BBAR_Y0 = 0.120
BBAR_H  = 0.038
BBAR_X0 = PAD + 0.005
BBAR_X1 = 1 - PAD - 0.005
bw = BBAR_X1 - BBAR_X0
tiers_seats = [85, 80, 185]
tiers_colors = [GREEN, YELLOW, RED]
tiers_labels = ["85 esc.\nalta confianza", "~80 esc.\nconfianza media", "~185 esc.\nincertidumbre alta"]
cursor = BBAR_X0
for seats, col, lbl in zip(tiers_seats, tiers_colors, tiers_labels):
    seg_w = (seats / 350) * bw - 0.003
    ax.add_patch(FancyBboxPatch(
        (cursor, BBAR_Y0), seg_w, BBAR_H,
        boxstyle="round,pad=0.003",
        facecolor=col + "88", edgecolor=col, linewidth=1.0, zorder=4,
    ))
    cx = cursor + seg_w / 2
    for j, line in enumerate(lbl.split("\n")):
        ax.text(cx, BBAR_Y0 + BBAR_H * (0.72 - j * 0.45), line,
                color=TEXT_WHITE if j == 0 else TEXT_MUTED,
                fontsize=7.5 if j == 0 else 7,
                fontweight="bold" if j == 0 else "normal",
                ha="center", va="center", zorder=5)
    cursor += seg_w + 0.003

# ─── Footer ───────────────────────────────────────────────────────────────────
ax.text(0.5, CARD_Y0 + 0.028,
        "Encuesta 40dB/El País/SER oct. 2026 (N=800)  ·  Swing D'Hondt provincial sobre 23J real  "
        "·  mapa electoral spain",
        color=TEXT_MUTED, fontsize=7.5, ha="center", va="center", zorder=5)

# ─── Guardar ──────────────────────────────────────────────────────────────────
out_dir = Path("tweets")
out_dir.mkdir(exist_ok=True)
out = out_dir / f"incertidumbre_circunscripciones_{datetime.today().strftime('%Y%m%d')}.png"
plt.savefig(out, dpi=100, bbox_inches="tight",
            facecolor=BG_DARK, edgecolor="none")
plt.close(fig)
print(f"Imagen guardada: {out.resolve()}")
