"""
tweet_vox_threshold.py
Card 1200x675 px: listado de confianza de VOX por provincia.
Tres columnas: Muy Probable / Posible / Poco Probable.
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
GREEN      = "#3FB950"
YELLOW     = "#D29922"
RED        = "#F85149"
VOX_GREEN  = "#5A9A2E"

# ── Datos del análisis (vox_threshold_analysis.py) ───────────────────────────
df = pd.read_csv(Path(__file__).parent / "data" / "vox_threshold_2026.csv")

TIERS = {
    "MUY PROBABLE":  {"color": GREEN,  "symbol": "●●●●○"},
    "PROBABLE":      {"color": GREEN,  "symbol": "●●●○○"},
    "POSIBLE":       {"color": YELLOW, "symbol": "●●○○○"},
    "POCO PROBABLE": {"color": RED,    "symbol": "●○○○○"},
}
# Agrupamos MUY PROBABLE y PROBABLE en columna izq, POSIBLE en centro, POCO en derecha
# Mostraremos:  [MUY PROBABLE + PROBABLE] | [POSIBLE] | [POCO PROBABLE (top 12)]

col_a = df[df["confidence"].isin(["MUY PROBABLE","PROBABLE"])].sort_values("gap_pp").copy()
col_b = df[df["confidence"] == "POSIBLE"].sort_values("gap_pp").copy()
col_c_all = df[df["confidence"] == "POCO PROBABLE"].sort_values("gap_pp").copy()
col_c = col_c_all.head(12)  # sólo las 12 más cercanas
n_hidden = len(col_c_all) - 12

fig = plt.figure(figsize=(12, 6.75), dpi=100)
fig.patch.set_facecolor(BG_DARK)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

PAD = 0.030

# ── Fondo card ────────────────────────────────────────────────────────────────
CARD_X0, CARD_X1 = 0.015, 0.985
CARD_Y0, CARD_Y1 = 0.025, 0.975
ax.fill_betweenx([CARD_Y0, CARD_Y1], CARD_X0, CARD_X1, color=BG_CARD, zorder=1)
ax.add_patch(FancyBboxPatch(
    (CARD_X0, CARD_Y0), CARD_X1 - CARD_X0, CARD_Y1 - CARD_Y0,
    boxstyle="round,pad=0.010", facecolor="none",
    edgecolor=SEPARATOR, linewidth=1.2, zorder=2,
))

# ── Header ────────────────────────────────────────────────────────────────────
HDR_Y0, HDR_Y1 = 0.880, 0.975
ax.fill_betweenx([HDR_Y0, HDR_Y1], CARD_X0, CARD_X1, color=VOX_GREEN, zorder=3)
HDR_CY = (HDR_Y0 + HDR_Y1) / 2
ax.text(PAD + 0.020, HDR_CY,
        "VOX — ¿Dónde puede ganar (o no) un escaño?",
        color=BG_DARK, fontsize=12.5, fontweight="bold", va="center", zorder=5)
ax.text(1 - PAD - 0.015, HDR_CY,
        "Nov. 2026 · Swing 40dB + D'Hondt",
        color=BG_DARK, fontsize=9, va="center", ha="right",
        fontstyle="italic", zorder=5)

# ── Subtítulo ─────────────────────────────────────────────────────────────────
ax.text(0.5, 0.849,
        "Gap = umbral D'Hondt real − estimación 2026 · Combustible = PP×15.6% + Abstención×12.7% (40dB oct-26)",
        color=TEXT_MUTED, fontsize=8.2, ha="center", va="center")
ax.plot([PAD, 1 - PAD], [0.828, 0.828], color=SEPARATOR, lw=0.7)

# ── Tres columnas ─────────────────────────────────────────────────────────────
COL_X = [PAD + 0.008, 0.370, 0.665]
COL_W = [0.330, 0.278, 0.320]
COL_Y_TOP = 0.810
ROW_H = 0.048

def draw_column_header(ax, cx, y, label, color, n_prov, n_esc):
    ax.add_patch(FancyBboxPatch(
        (cx, y - 0.022), COL_W[0] if cx == COL_X[0] else COL_W[1] if cx == COL_X[1] else COL_W[2],
        0.042,
        boxstyle="round,pad=0.005",
        facecolor=color + "33", edgecolor=color, linewidth=1.0, zorder=4,
    ))
    col_idx = COL_X.index(cx)
    col_cx = cx + COL_W[col_idx] / 2
    ax.text(col_cx, y, label,
            color=color, fontsize=9, fontweight="bold",
            ha="center", va="center", zorder=5)
    ax.text(col_cx, y - 0.013,
            f"{n_prov} prov · {n_esc} esc estimados",
            color=TEXT_MUTED, fontsize=7, ha="center", va="center", zorder=5)


# ── Columna A: Muy Probable + Probable (verde) ────────────────────────────────
x0 = COL_X[0]
n_esc_a = int(col_a["vox_seats_26"].sum())
draw_column_header(ax, x0, COL_Y_TOP, "MUY PROBABLE / PROBABLE", GREEN, len(col_a), n_esc_a)

y = COL_Y_TOP - 0.048
for _, r in col_a.iterrows():
    conf = r["confidence"]
    color = GREEN if conf in ("MUY PROBABLE", "PROBABLE") else YELLOW
    gap_str = f"+{r['gap_pp']:.1f}pp"
    fuel_str = f"×{r['coverage']:.0f}" if r["coverage"] < 99 else ">×10"
    # Barra de fondo sutil
    bar_fill = color + "18"
    ax.add_patch(FancyBboxPatch(
        (x0, y - 0.018), COL_W[0] - 0.005, 0.036,
        boxstyle="round,pad=0.003",
        facecolor=bar_fill, edgecolor="none", zorder=3,
    ))
    ax.text(x0 + 0.008, y,
            f"{r['provincia']}", color=TEXT_WHITE, fontsize=8.2,
            fontweight="bold", va="center", zorder=5)
    ax.text(x0 + 0.008, y - 0.013,
            f"{r['escanos']}esc · {r['vox_pct_26']:.1f}% → umbral {r['umbral_pct']:.1f}%",
            color=TEXT_MUTED, fontsize=7, va="center", zorder=5)
    # Gap badge
    ax.add_patch(FancyBboxPatch(
        (x0 + COL_W[0] - 0.080, y - 0.013), 0.070, 0.028,
        boxstyle="round,pad=0.003",
        facecolor=color + "44", edgecolor=color + "88", linewidth=0.7, zorder=4,
    ))
    ax.text(x0 + COL_W[0] - 0.045, y, gap_str,
            color=color, fontsize=8, fontweight="bold", ha="center", va="center", zorder=5)
    ax.text(x0 + COL_W[0] - 0.045, y - 0.013, f"comb {fuel_str}",
            color=TEXT_MUTED, fontsize=6.5, ha="center", va="center", zorder=5)
    y -= ROW_H

# ── Columna B: Posible (amarillo) ─────────────────────────────────────────────
x0 = COL_X[1]
n_esc_b = int(col_b["vox_seats_26"].sum())
draw_column_header(ax, x0, COL_Y_TOP, "POSIBLE", YELLOW, len(col_b), n_esc_b)

y = COL_Y_TOP - 0.048
for _, r in col_b.iterrows():
    bar_fill = YELLOW + "18"
    ax.add_patch(FancyBboxPatch(
        (x0, y - 0.018), COL_W[1] - 0.005, 0.036,
        boxstyle="round,pad=0.003",
        facecolor=bar_fill, edgecolor="none", zorder=3,
    ))
    ax.text(x0 + 0.008, y,
            f"{r['provincia']}", color=TEXT_WHITE, fontsize=8.2,
            fontweight="bold", va="center", zorder=5)
    ax.text(x0 + 0.008, y - 0.013,
            f"{r['escanos']}esc · {r['vox_pct_26']:.1f}% → {r['umbral_pct']:.1f}%",
            color=TEXT_MUTED, fontsize=7, va="center", zorder=5)
    gap_str = f"+{r['gap_pp']:.1f}pp"
    ax.add_patch(FancyBboxPatch(
        (x0 + COL_W[1] - 0.080, y - 0.013), 0.070, 0.028,
        boxstyle="round,pad=0.003",
        facecolor=YELLOW + "44", edgecolor=YELLOW + "88", linewidth=0.7, zorder=4,
    ))
    ax.text(x0 + COL_W[1] - 0.045, y, gap_str,
            color=YELLOW, fontsize=8, fontweight="bold", ha="center", va="center", zorder=5)
    ax.text(x0 + COL_W[1] - 0.045, y - 0.013, f"comb ×{r['coverage']:.1f}",
            color=TEXT_MUTED, fontsize=6.5, ha="center", va="center", zorder=5)
    y -= ROW_H

# ── Columna C: Poco Probable (rojo, solo top 12) ──────────────────────────────
x0 = COL_X[2]
n_esc_c = int(col_c_all["vox_seats_26"].sum())
draw_column_header(ax, x0, COL_Y_TOP, "POCO PROBABLE  (más cercanos)", RED, len(col_c_all), n_esc_c)

y = COL_Y_TOP - 0.048
for _, r in col_c.iterrows():
    bar_fill = RED + "15"
    ax.add_patch(FancyBboxPatch(
        (x0, y - 0.018), COL_W[2] - 0.005, 0.036,
        boxstyle="round,pad=0.003",
        facecolor=bar_fill, edgecolor="none", zorder=3,
    ))
    ax.text(x0 + 0.008, y,
            f"{r['provincia']}", color=TEXT_WHITE, fontsize=8.2,
            fontweight="bold", va="center", zorder=5)
    ax.text(x0 + 0.008, y - 0.013,
            f"{r['escanos']}esc · {r['vox_pct_26']:.1f}% → {r['umbral_pct']:.1f}%",
            color=TEXT_MUTED, fontsize=7, va="center", zorder=5)
    gap_str = f"+{r['gap_pp']:.1f}pp"
    ax.add_patch(FancyBboxPatch(
        (x0 + COL_W[2] - 0.080, y - 0.013), 0.070, 0.028,
        boxstyle="round,pad=0.003",
        facecolor=RED + "33", edgecolor=RED + "66", linewidth=0.7, zorder=4,
    ))
    ax.text(x0 + COL_W[2] - 0.045, y, gap_str,
            color=RED, fontsize=8, fontweight="bold", ha="center", va="center", zorder=5)
    ax.text(x0 + COL_W[2] - 0.045, y - 0.013, f"comb ×{min(r['coverage'], 9.9):.1f}",
            color=TEXT_MUTED, fontsize=6.5, ha="center", va="center", zorder=5)
    y -= ROW_H

if n_hidden > 0:
    ax.text(x0 + COL_W[2] / 2, y + 0.012,
            f"+ {n_hidden} provincias más (gap >12pp)",
            color=RED + "99", fontsize=7.5, ha="center", va="center",
            fontstyle="italic", zorder=5)

# ── Separador y nota metodológica ─────────────────────────────────────────────
sep_y = 0.096
ax.plot([PAD, 1 - PAD], [sep_y, sep_y], color=SEPARATOR, lw=0.7)

total_esc = n_esc_a + n_esc_b + n_esc_c
note = (
    f"Swing proporcional sobre 23J real · Umbral D'Hondt = coeficiente del último escaño · "
    f"Combustible: PP×15.6% + Abs×12.7% (transferencias 40dB oct-26) · "
    f"Total estimado VOX: {total_esc} escaños"
)
ax.text(0.5, CARD_Y0 + 0.044, note,
        color=TEXT_MUTED, fontsize=7.3, ha="center", va="center", zorder=5)
ax.text(0.5, CARD_Y0 + 0.022,
        f"mapa electoral spain  ·  {datetime.today().strftime('%d/%m/%Y')}",
        color=TEXT_MUTED, fontsize=7.5, ha="center", va="center", zorder=5)

out_dir = Path("tweets")
out_dir.mkdir(exist_ok=True)
out = out_dir / f"vox_threshold_{datetime.today().strftime('%Y%m%d')}.png"
plt.savefig(out, dpi=100, bbox_inches="tight",
            facecolor=BG_DARK, edgecolor="none")
plt.close(fig)
print(f"Imagen guardada: {out.resolve()}")
