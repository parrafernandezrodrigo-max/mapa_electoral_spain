#!/usr/bin/env python3
"""
tweet_gen.py – Generador de imagen para Twitter
Pronóstico Electoral por Circunscripción

Uso:
  python tweet_gen.py "Madrid" "PP:13,PSOE:8,VOX:3,SUMAR:2"
  python tweet_gen.py "Barcelona" "PSOE:5,ERC:4,JUNTS:4,PP:2,SUMAR:2,CUP:1"
  python tweet_gen.py --list-parties

La imagen se guarda en tweets/ con el nombre provincia_fecha.png
"""

import sys
import argparse
import hashlib
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# ─── Colores oficiales de partidos ────────────────────────────────────────────
PARTY_CONFIG = {
    # Derecha federal
    "PP":        {"label": "PP",           "color": "#1B4F8A"},
    "AP":        {"label": "AP",           "color": "#1B4F8A"},
    "UCD":       {"label": "UCD",          "color": "#5B8DB8"},
    "CDS":       {"label": "CDS",          "color": "#5B8DB8"},
    "VOX":       {"label": "Vox",          "color": "#5A9A2E"},
    "CS":        {"label": "Ciudadanos",   "color": "#F57C00"},
    "C'S":       {"label": "Ciudadanos",   "color": "#F57C00"},
    "NA+":       {"label": "Navarra Suma", "color": "#1B4F8A"},
    # Izquierda federal
    "PSOE":      {"label": "PSOE",         "color": "#D62828"},
    "PSC":       {"label": "PSC",          "color": "#D62828"},
    "PSDEG":     {"label": "PSdeG",        "color": "#D62828"},
    "IU":        {"label": "IU",           "color": "#B5010B"},
    "UP":        {"label": "Unidas P.",    "color": "#7B2D8B"},
    "PODEMOS":   {"label": "Podemos",      "color": "#7B2D8B"},
    "SUMAR":     {"label": "Sumar",        "color": "#C0226E"},
    "MÁS PAÍS":  {"label": "Más País",     "color": "#3DAA7B"},
    "MAS PAIS":  {"label": "Más País",     "color": "#3DAA7B"},
    # Nacionalismo izquierda
    "ERC":       {"label": "ERC",          "color": "#E8C42E"},
    "EH BILDU":  {"label": "EH Bildu",     "color": "#3D9970"},
    "BILDU":     {"label": "EH Bildu",     "color": "#3D9970"},
    "BNG":       {"label": "BNG",          "color": "#52B8D0"},
    "CUP":       {"label": "CUP",          "color": "#E8C42E"},
    "AMAIUR":    {"label": "Amaiur",       "color": "#3D9970"},
    "NC":        {"label": "Nueva Canarias","color":"#52B8D0"},
    # Nacionalismo centro
    "PNV":       {"label": "PNV",          "color": "#257AC7"},
    "EAJ-PNV":   {"label": "PNV",          "color": "#257AC7"},
    "CIU":       {"label": "CiU",          "color": "#18437A"},
    "JUNTS":     {"label": "Junts",        "color": "#003082"},
    "JXCAT":     {"label": "JxCat",        "color": "#003082"},
    "CC":        {"label": "CC",           "color": "#F4A261"},
    "CCA":       {"label": "CC",           "color": "#F4A261"},
    "PAR":       {"label": "PAR",          "color": "#D4A017"},
    # Regionalismo
    "PRC":       {"label": "PRC",          "color": "#E9C46A"},
    "FORO":      {"label": "Foro",         "color": "#C97D4E"},
    "FAC":       {"label": "Foro",         "color": "#C97D4E"},
    # Genérico
    "OTROS":     {"label": "Otros",        "color": "#6B7280"},
    "OTHER":     {"label": "Otros",        "color": "#6B7280"},
}

DISCLAIMERS = [
    "Modelo predictivo basado en datos reales y corazonadas™",
    "Margen de error: ±algún escaño. O dos.",
    "Si falla, fue un ejercicio puramente académico.",
    "Calculado con D'Hondt y una pizca de fe electoral",
    "Las encuestas mienten; éste también podría",
    "Pronóstico sin responsabilidad electoral ni moral",
    "Basado en datos oficiales del Ministerio del Interior™",
    "Más fiable que el CIS (esto es relativo)",
    "No apto para apostar. En serio.",
    "Garantizado hasta que abran las urnas",
]

WINNER_TAGS = ["★ GANADOR", "★ 1.er clasificado", "★ El favorito", "★ El que manda"]

# ─── Colores de fondo / tema ───────────────────────────────────────────────────
BG_DARK    = "#0D1117"
BG_CARD    = "#161B22"
ACCENT     = "#F4A261"
TEXT_WHITE = "#F0F6FC"
TEXT_MUTED = "#8B949E"
SEPARATOR  = "#30363D"


def parse_seats(seats_str: str) -> list[dict]:
    """Parsea 'PP:13,PSOE:8,VOX:3' → lista de dicts ordenada por escaños desc."""
    result = []
    for token in seats_str.split(","):
        token = token.strip()
        if ":" not in token:
            continue
        parts = token.split(":", 1)
        sigla = parts[0].strip().upper()
        try:
            seats = int(parts[1].strip())
        except ValueError:
            print(f"  ⚠ Ignorando token inválido: {token!r}", file=sys.stderr)
            continue
        cfg = PARTY_CONFIG.get(sigla, {"label": sigla.title(), "color": "#6B7280"})
        result.append({"sigla": sigla, "label": cfg["label"], "color": cfg["color"], "seats": seats})
    return sorted(result, key=lambda x: x["seats"], reverse=True)


def deterministic_disclaimer(province: str) -> str:
    idx = int(hashlib.md5(province.encode()).hexdigest(), 16) % len(DISCLAIMERS)
    return DISCLAIMERS[idx]


def winner_tag(province: str) -> str:
    idx = int(hashlib.md5(province.encode()).hexdigest(), 16) % len(WINNER_TAGS)
    return WINNER_TAGS[idx]


def generate_tweet_image(
    province: str,
    seats_str: str,
    output_dir: str = "tweets",
    custom_subtitle: str = "",
    date_str: str = "",
) -> Path:
    """
    Genera la imagen y la guarda en output_dir.
    Devuelve el Path de la imagen creada.
    """
    parties = parse_seats(seats_str)
    if not parties:
        raise ValueError("No se pudieron parsear los escaños. Ejemplo: 'PP:13,PSOE:8,VOX:3'")

    total_seats = sum(p["seats"] for p in parties)
    if date_str == "":
        date_str = datetime.today().strftime("%d/%m/%Y")
    disclaimer = deterministic_disclaimer(province)
    wtag       = winner_tag(province)

    # ── Canvas 1200 × 675 px ───────────────────────────────────────────────────
    W, H = 12, 6.75
    fig = plt.figure(figsize=(W, H), dpi=100)
    fig.patch.set_facecolor(BG_DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(BG_DARK)

    # ── Layout: positions calculated top → bottom ──────────────────────────────
    # fixed anchor points
    CARD_X0, CARD_X1 = 0.025, 0.975
    CARD_Y0, CARD_Y1 = 0.030, 0.970
    PAD_X = 0.050   # left/right text margin inside card

    # Header strip
    HDR_Y0, HDR_Y1 = 0.855, 0.970
    ax.fill_betweenx([HDR_Y0, HDR_Y1], CARD_X0, CARD_X1, color=ACCENT, zorder=3)

    ax.text(PAD_X + 0.01, (HDR_Y0 + HDR_Y1) / 2,
            "PRONOSTICO ELECTORAL",
            color=BG_DARK, fontsize=14, fontweight="bold", va="center", zorder=5)
    ax.text(1 - PAD_X - 0.01, (HDR_Y0 + HDR_Y1) / 2, date_str,
            color=BG_DARK, fontsize=11, va="center", ha="right", zorder=5,
            fontstyle="italic")

    # Card background (drawn after header so header clips to card bounds)
    card = FancyBboxPatch(
        (CARD_X0, CARD_Y0), CARD_X1 - CARD_X0, CARD_Y1 - CARD_Y0,
        boxstyle="round,pad=0.012",
        facecolor="none", edgecolor=SEPARATOR, linewidth=1.5, zorder=2,
    )
    ax.add_patch(card)
    ax.fill_betweenx([CARD_Y0, HDR_Y0], CARD_X0, CARD_X1, color=BG_CARD, zorder=1)

    # Province name (adaptive font size)
    prov_fontsize = max(26, min(42, int(42 - max(0, len(province) - 6) * 1.8)))
    ax.text(0.5, 0.785, province.upper(),
            color=TEXT_WHITE, fontsize=prov_fontsize, fontweight="bold",
            ha="center", va="center", zorder=5)
    ax.text(0.5, 0.718,
            f"{total_seats} escanos en juego",
            color=ACCENT, fontsize=13, ha="center", va="center", zorder=5)

    # Separator under province
    SEP1_Y = 0.685
    ax.plot([PAD_X, 1 - PAD_X], [SEP1_Y, SEP1_Y],
            color=SEPARATOR, linewidth=1, zorder=4)

    # ── Seat bar ───────────────────────────────────────────────────────────────
    BAR_Y0, BAR_H = 0.575, 0.090
    BAR_X0, BAR_X1 = PAD_X, 1 - PAD_X
    bar_w = BAR_X1 - BAR_X0
    gap   = 0.0025

    cursor = BAR_X0
    segments = []
    for p in parties:
        seg_w = (p["seats"] / total_seats) * bar_w - gap
        segments.append({**p, "x": cursor, "w": max(seg_w, 0.001)})
        cursor += seg_w + gap

    for seg in segments:
        fancy = FancyBboxPatch(
            (seg["x"], BAR_Y0), seg["w"], BAR_H,
            boxstyle="round,pad=0.004",
            facecolor=seg["color"], edgecolor="none", zorder=5,
        )
        ax.add_patch(fancy)
        cx = seg["x"] + seg["w"] / 2
        if seg["seats"] / total_seats >= 0.07:
            ax.text(cx, BAR_Y0 + BAR_H / 2, str(seg["seats"]),
                    color="white", fontsize=12, fontweight="bold",
                    ha="center", va="center", zorder=6)

    # ── Legend ─────────────────────────────────────────────────────────────────
    n    = len(parties)
    cols = min(n, 4)
    rows = (n + cols - 1) // cols
    col_w = (1 - 2 * PAD_X) / cols
    row_h = 0.072

    LEG_Y_TOP = BAR_Y0 - 0.035   # start just below the bar

    for i, p in enumerate(parties):
        col = i % cols
        row = i // cols
        lx  = PAD_X + col * col_w
        ly  = LEG_Y_TOP - row * row_h

        pct = round(p["seats"] / total_seats * 100)
        is_winner = (i == 0)
        label_color = TEXT_WHITE if is_winner else TEXT_MUTED
        weight = "bold" if is_winner else "normal"

        # Colored square marker (text "■" avoids aspect-ratio circle distortion)
        ax.text(lx + 0.012, ly, "■",
                color=p["color"], fontsize=13, ha="center", va="center", zorder=5)

        badge = f"  {wtag}" if is_winner else ""
        ax.text(lx + 0.030, ly,
                f"{p['label']}   {p['seats']} esc. ({pct}%){badge}",
                color=label_color, fontsize=10.5, va="center", zorder=5,
                fontweight=weight)

    # ── Bottom content ─────────────────────────────────────────────────────────
    SEP2_Y = LEG_Y_TOP - rows * row_h - 0.020
    ax.plot([PAD_X, 1 - PAD_X], [SEP2_Y, SEP2_Y],
            color=SEPARATOR, linewidth=1, zorder=4)

    if custom_subtitle:
        ax.text(0.5, SEP2_Y - 0.038, f'"{custom_subtitle}"',
                color=TEXT_WHITE, fontsize=11, ha="center", va="center",
                fontstyle="italic", zorder=5)
        disc_y = SEP2_Y - 0.082
    else:
        disc_y = SEP2_Y - 0.038

    ax.text(0.5, disc_y, disclaimer,
            color=TEXT_MUTED, fontsize=9, ha="center", va="center",
            fontstyle="italic", zorder=5)

    ax.text(0.5, CARD_Y0 + 0.025, "mapa electoral spain",
            color=TEXT_MUTED, fontsize=8, ha="center", va="center", zorder=5)

    # ── Save ───────────────────────────────────────────────────────────────────
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_name = province.lower().replace(" ", "_").replace("/", "-")
    date_tag  = datetime.today().strftime("%Y%m%d")
    out_path  = out_dir / f"{safe_name}_{date_tag}.png"

    plt.savefig(out_path, dpi=100, bbox_inches="tight",
                facecolor=BG_DARK, edgecolor="none")
    plt.close(fig)
    print(f"  Imagen guardada: {out_path}")
    return out_path


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Genera imagen de pronóstico electoral para Twitter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Ejemplos:
  python tweet_gen.py "Madrid" "PP:13,PSOE:8,VOX:3,SUMAR:2"
  python tweet_gen.py "Barcelona" "PSOE:5,ERC:4,JUNTS:4,PP:2,SUMAR:2,CUP:1" -s "Cataluña decide"
  python tweet_gen.py --list-parties
""",
    )
    parser.add_argument("province", nargs="?", help="Nombre de la circunscripción")
    parser.add_argument("seats",    nargs="?", help="Escaños: PARTIDO:N,PARTIDO:N,...")
    parser.add_argument("-s", "--subtitle", default="", help="Texto personalizado (opcional)")
    parser.add_argument("-d", "--date",     default="", help="Fecha personalizada (opcional)")
    parser.add_argument("-o", "--output",   default="tweets", help="Directorio de salida")
    parser.add_argument("--list-parties", action="store_true", help="Lista partidos disponibles")

    args = parser.parse_args()

    if args.list_parties:
        print("\nPartidos disponibles (sigla → etiqueta):\n")
        for sigla, cfg in sorted(PARTY_CONFIG.items()):
            print(f"  {sigla:<12} → {cfg['label']}")
        print()
        return

    if not args.province or not args.seats:
        parser.print_help()
        sys.exit(1)

    generate_tweet_image(
        province=args.province,
        seats_str=args.seats,
        output_dir=args.output,
        custom_subtitle=args.subtitle,
        date_str=args.date,
    )


if __name__ == "__main__":
    main()
