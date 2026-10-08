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

# ─── Adscripción de bloques (simplificada) ────────────────────────────────────
PARTY_BLOC = {
    "PP": "dcha", "AP": "dcha", "UCD": "dcha", "CDS": "dcha",
    "VOX": "dcha", "CS": "dcha", "C'S": "dcha", "NA+": "dcha",
    "PSOE": "izq", "PSC": "izq", "IU": "izq",
    "PODEMOS": "izq", "UP": "izq", "SUMAR": "izq",
    "MÁS PAÍS": "izq", "MAS PAIS": "izq",
    "ERC": "nac_izq", "EH BILDU": "nac_izq", "BILDU": "nac_izq",
    "BNG": "nac_izq", "CUP": "nac_izq", "AMAIUR": "nac_izq", "NC": "nac_izq",
    "PNV": "nac_cnt", "EAJ-PNV": "nac_cnt",
    "CIU": "nac_cnt", "JUNTS": "nac_cnt", "JXCAT": "nac_cnt",
    "CC": "nac_cnt", "CCA": "nac_cnt", "PAR": "nac_cnt",
    "PRC": "reg", "FORO": "reg", "FAC": "reg",
}

BLOC_LABELS = {
    "izq":     ("Izquierda fed.", "#E63946"),
    "dcha":    ("Derecha fed.",   "#457B9D"),
    "nac_izq": ("Nac. izquierda","#A8DADC"),
    "nac_cnt": ("Nac. centro",   "#F4A261"),
    "reg":     ("Regionalismo",  "#E9C46A"),
    "otros":   ("Otros",         "#6B7280"),
}

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
    "CUP":       {"label": "CUP",          "color": "#A89200"},
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


def _draw_donut(fig, parties: list[dict], total_seats: int,
                center_y_fig: float, diameter_px: int = 260) -> None:
    """
    Dibuja un donut chart en un sub-eje cuadrado (en píxeles) centrado en center_y_fig.
    """
    import math
    from matplotlib.patches import Circle, Wedge

    pie_w = diameter_px / 1200
    pie_h = diameter_px / 675
    pie_l = 0.5 - pie_w / 2
    pie_b = center_y_fig - pie_h / 2

    ax_p = fig.add_axes([pie_l, pie_b, pie_w, pie_h])
    ax_p.patch.set_visible(False)
    ax_p.set_xlim(-1.25, 1.25)
    ax_p.set_ylim(-1.25, 1.25)
    ax_p.axis("off")

    if len(parties) == 1:
        p = parties[0]
        ax_p.add_patch(Circle((0, 0), 1.0, facecolor=p["color"],
                               edgecolor=ACCENT, linewidth=3, zorder=3))
        ax_p.add_patch(Circle((0, 0), 0.46, facecolor=BG_CARD,
                               edgecolor="none", zorder=4))
        fs_num = 44 if p["seats"] < 10 else 34
        ax_p.text(0,  0.14, str(p["seats"]),
                  color=TEXT_WHITE, fontsize=fs_num, fontweight="bold",
                  ha="center", va="center", zorder=5)
        ax_p.text(0, -0.22, p["label"],
                  color=TEXT_WHITE, fontsize=13, fontweight="bold",
                  ha="center", va="center", zorder=5)
    else:
        angle = 90.0
        for i, p in enumerate(parties):
            frac  = p["seats"] / total_seats
            delta = frac * 360
            wedge = Wedge((0, 0), 1.0, angle - delta, angle,
                          width=0.50,
                          facecolor=p["color"],
                          edgecolor=BG_CARD, linewidth=2.5, zorder=3)
            ax_p.add_patch(wedge)
            if frac >= 0.10:
                mid_a  = math.radians(angle - delta / 2)
                r_lbl  = 0.75
                ax_p.text(r_lbl * math.cos(mid_a), r_lbl * math.sin(mid_a),
                          str(p["seats"]),
                          color="white", fontsize=11, fontweight="bold",
                          ha="center", va="center", zorder=5)
            angle -= delta
        # Total in center hole
        ax_p.add_patch(Circle((0, 0), 0.50, facecolor=BG_CARD,
                               edgecolor="none", zorder=4))
        ax_p.text(0,  0.14, str(total_seats),
                  color=TEXT_WHITE, fontsize=26, fontweight="bold",
                  ha="center", va="center", zorder=5)
        ax_p.text(0, -0.15, "esc.",
                  color=TEXT_MUTED, fontsize=10,
                  ha="center", va="center", zorder=5)


def generate_tweet_image(
    province: str,
    seats_str: str,
    output_dir: str = "tweets",
    custom_subtitle: str = "",
    date_str: str = "",
    mode: str = "auto",
) -> Path:
    """
    Genera la imagen (1200x675 px) y la guarda en output_dir.
    mode: "auto" (pie si <=10 escaños o 1 partido, barra si no), "pie", "bar"
    """
    parties = parse_seats(seats_str)
    if not parties:
        raise ValueError("No se pudieron parsear los escanios. Ejemplo: 'PP:13,PSOE:8,VOX:3'")

    total_seats = sum(p["seats"] for p in parties)
    if date_str == "":
        date_str = datetime.today().strftime("%d/%m/%Y")
    disclaimer = deterministic_disclaimer(province)

    # Resolve auto mode
    if mode == "auto":
        mode = "pie" if (total_seats <= 10 or len(parties) == 1) else "bar"

    # ── Canvas 1200 x 675 px ──────────────────────────────────────────────────
    fig = plt.figure(figsize=(12, 6.75), dpi=100)
    fig.patch.set_facecolor(BG_DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(BG_DARK)

    # Coordinate constants
    CARD_X0, CARD_X1 = 0.025, 0.975
    CARD_Y0, CARD_Y1 = 0.030, 0.970
    PAD_X = 0.052

    # ── Card body ─────────────────────────────────────────────────────────────
    ax.fill_betweenx([CARD_Y0, CARD_Y1], CARD_X0, CARD_X1, color=BG_CARD, zorder=1)
    card_border = FancyBboxPatch(
        (CARD_X0, CARD_Y0), CARD_X1 - CARD_X0, CARD_Y1 - CARD_Y0,
        boxstyle="round,pad=0.012", facecolor="none",
        edgecolor=SEPARATOR, linewidth=1.5, zorder=2,
    )
    ax.add_patch(card_border)

    # ── Header strip (amber) ──────────────────────────────────────────────────
    HDR_Y0, HDR_Y1 = 0.858, 0.970
    ax.fill_betweenx([HDR_Y0, HDR_Y1], CARD_X0, CARD_X1, color=ACCENT, zorder=3)
    HDR_CY = (HDR_Y0 + HDR_Y1) / 2
    ax.text(PAD_X + 0.01, HDR_CY, "PRONOSTICO ELECTORAL",
            color=BG_DARK, fontsize=14, fontweight="bold", va="center", zorder=5)
    ax.text(1 - PAD_X - 0.01, HDR_CY, date_str,
            color=BG_DARK, fontsize=11, va="center", ha="right",
            fontstyle="italic", zorder=5)

    # ── Province name ─────────────────────────────────────────────────────────
    prov_fs = max(28, min(44, int(44 - max(0, len(province) - 5) * 1.8)))
    ax.text(0.5, 0.775, province.upper(),
            color=TEXT_WHITE, fontsize=prov_fs, fontweight="bold",
            ha="center", va="center", zorder=5)

    # ── Seats info line ───────────────────────────────────────────────────────
    # Note: "escanos" avoids potential encoding issues; accent handled via unicode escape
    _esc = "escaño" if total_seats == 1 else "escaños"
    ax.text(0.5, 0.710,
            f"{total_seats} {_esc} en juego",
            color=ACCENT, fontsize=13.5, ha="center", va="center", zorder=5)

    # ── Separator ─────────────────────────────────────────────────────────────
    SEP1_Y = 0.672
    ax.plot([PAD_X, 1 - PAD_X], [SEP1_Y, SEP1_Y],
            color=SEPARATOR, linewidth=0.8, zorder=4)

    # ══════════════════════════════════════════════════════════════════════════
    # MODO PIE: donut chart
    # ══════════════════════════════════════════════════════════════════════════
    if mode == "pie":
        # Choose donut size: larger for single party
        diam_px = 268 if len(parties) == 1 else 240
        # Center donut vertically in content area (below sep1, above legend)
        # Donut height in fig coords:
        dh = diam_px / 675
        # Place center so top of donut is just below sep1
        PIE_CENTER_Y_FIG = SEP1_Y - dh / 2 - 0.010

        _draw_donut(fig, parties, total_seats, PIE_CENTER_Y_FIG, diam_px)

        # Donut bottom in fig coords
        pie_bottom_y = PIE_CENTER_Y_FIG - dh / 2

        # Legend (skipped if single party — info is already inside the donut)
        if len(parties) > 1:
            n     = len(parties)
            cols  = min(n, 4)
            rows  = (n + cols - 1) // cols
            col_w = (1 - 2 * PAD_X) / cols
            row_h = 0.082
            LEG_Y = pie_bottom_y - 0.040

            for i, p in enumerate(parties):
                col = i % cols
                row = i // cols
                lx  = PAD_X + col * col_w
                ly  = LEG_Y - row * row_h
                pct = round(p["seats"] / total_seats * 100)
                ax.text(lx + 0.013, ly, "■",
                        color=p["color"], fontsize=13, ha="center", va="center", zorder=5)
                ax.text(lx + 0.033, ly,
                        f"{p['label']}  {p['seats']} esc. ({pct}%)",
                        color=ACCENT if i == 0 else TEXT_MUTED,
                        fontsize=10.5, va="center", zorder=5,
                        fontweight="bold" if i == 0 else "normal")

            leg_end_y = LEG_Y - rows * row_h + row_h * 0.5
        else:
            leg_end_y = pie_bottom_y - 0.020

        # Separator + bloc summary (only if more than 1 party)
        if len(parties) > 1:
            SEP2_Y = leg_end_y - 0.025
            ax.plot([PAD_X, 1 - PAD_X], [SEP2_Y, SEP2_Y],
                    color=SEPARATOR, linewidth=0.8, zorder=4)

            bloc_seats: dict[str, int] = {}
            for p in parties:
                bloc = PARTY_BLOC.get(p["sigla"].upper(), "otros")
                bloc_seats[bloc] = bloc_seats.get(bloc, 0) + p["seats"]
            sorted_blocs = sorted(bloc_seats.items(), key=lambda x: x[1], reverse=True)[:3]
            majority = total_seats // 2 + 1
            BLOC_Y = SEP2_Y - 0.045
            n_blocs = len(sorted_blocs)
            for j, (bkey, bseats) in enumerate(sorted_blocs):
                blabel, bcolor = BLOC_LABELS.get(bkey, BLOC_LABELS["otros"])
                bx = PAD_X + j * (1 - 2 * PAD_X) / max(n_blocs, 1)
                ax.text(bx + 0.012, BLOC_Y, "■", color=bcolor, fontsize=11,
                        ha="center", va="center", zorder=5)
                ax.text(bx + 0.030, BLOC_Y, f"{blabel}  {bseats} esc.",
                        color=TEXT_MUTED, fontsize=9, va="center", zorder=5)
            ax.text(0.5, BLOC_Y - 0.045,
                    f"Mayoría absoluta: {majority} escaños",
                    color=TEXT_MUTED, fontsize=9, ha="center", va="center",
                    fontstyle="italic", zorder=5)
            content_bottom_y = BLOC_Y - 0.090
        else:
            content_bottom_y = leg_end_y - 0.020

        # Separator before footer text
        SEPF_Y = max(content_bottom_y, CARD_Y0 + 0.160)
        ax.plot([PAD_X, 1 - PAD_X], [SEPF_Y, SEPF_Y],
                color=SEPARATOR, linewidth=0.8, zorder=4)

        footer_y = CARD_Y0 + 0.038
        disc_y   = footer_y + 0.060
        sub_y    = disc_y + 0.060

        if custom_subtitle:
            ax.text(0.5, sub_y, f'"{custom_subtitle}"',
                    color=TEXT_WHITE, fontsize=12, ha="center", va="center",
                    fontstyle="italic", fontweight="bold", zorder=5)

        ax.text(0.5, disc_y, disclaimer,
                color=TEXT_MUTED, fontsize=9, ha="center", va="center",
                fontstyle="italic", zorder=5)
        ax.text(0.5, footer_y, "mapa electoral spain",
                color=TEXT_MUTED, fontsize=8.5, ha="center", va="center", zorder=5)

    # ══════════════════════════════════════════════════════════════════════════
    # MODO BAR: barra horizontal (comportamiento original)
    # ══════════════════════════════════════════════════════════════════════════
    else:
        BAR_Y0 = 0.490
        BAR_H  = 0.158
        BAR_X0, BAR_X1 = PAD_X, 1 - PAD_X
        bar_w = BAR_X1 - BAR_X0
        gap   = 0.003

        cursor = BAR_X0
        segments: list[dict] = []
        for p in parties:
            seg_w = max((p["seats"] / total_seats) * bar_w - gap, 0.002)
            segments.append({**p, "x": cursor, "w": seg_w})
            cursor += seg_w + gap

        for i, seg in enumerate(segments):
            ec = ACCENT if i == 0 else "none"
            lw = 2.5    if i == 0 else 0
            ax.add_patch(FancyBboxPatch(
                (seg["x"], BAR_Y0), seg["w"], BAR_H,
                boxstyle="round,pad=0.004",
                facecolor=seg["color"], edgecolor=ec, linewidth=lw, zorder=5,
            ))
            cx  = seg["x"] + seg["w"] / 2
            pct = seg["seats"] / total_seats
            if pct >= 0.055:
                ax.text(cx, BAR_Y0 + BAR_H * 0.62, str(seg["seats"]),
                        color="white", fontsize=14, fontweight="bold",
                        ha="center", va="center", zorder=6)
            if i == 0 and pct >= 0.12:
                ax.text(cx, BAR_Y0 + BAR_H * 0.28, "GANADOR",
                        color="white", fontsize=7.5, fontweight="bold",
                        ha="center", va="center", zorder=6, alpha=0.85)

        n    = len(parties)
        cols = min(n, 4)
        rows = (n + cols - 1) // cols
        col_w  = (1 - 2 * PAD_X) / cols
        row_h  = 0.098
        LEG_ROW0_CY = BAR_Y0 - 0.052

        for i, p in enumerate(parties):
            col = i % cols
            row = i // cols
            lx  = PAD_X + col * col_w
            ly  = LEG_ROW0_CY - row * row_h
            pct = round(p["seats"] / total_seats * 100)
            is_winner = (i == 0)
            ax.text(lx + 0.013, ly, "■",
                    color=p["color"], fontsize=15, ha="center", va="center", zorder=5)
            ax.text(lx + 0.033, ly,
                    f"{p['label']}  {p['seats']} esc. ({pct}%)",
                    color=ACCENT if is_winner else TEXT_MUTED,
                    fontsize=11.5, va="center", zorder=5,
                    fontweight="bold" if is_winner else "normal")

        leg_bottom_y = LEG_ROW0_CY - rows * row_h + row_h * 0.5
        SEP2_Y = leg_bottom_y - 0.028
        ax.plot([PAD_X, 1 - PAD_X], [SEP2_Y, SEP2_Y],
                color=SEPARATOR, linewidth=0.8, zorder=4)

        bloc_seats_b: dict[str, int] = {}
        for p in parties:
            bloc = PARTY_BLOC.get(p["sigla"].upper(), "otros")
            bloc_seats_b[bloc] = bloc_seats_b.get(bloc, 0) + p["seats"]
        sorted_blocs_b = sorted(bloc_seats_b.items(), key=lambda x: x[1], reverse=True)[:3]
        majority_b = total_seats // 2 + 1
        BLOC_Y = SEP2_Y - 0.045
        for j, (bkey, bseats) in enumerate(sorted_blocs_b):
            blabel, bcolor = BLOC_LABELS.get(bkey, BLOC_LABELS["otros"])
            bx = PAD_X + j * (1 - 2 * PAD_X) / max(len(sorted_blocs_b), 1)
            ax.text(bx + 0.012, BLOC_Y, "■", color=bcolor, fontsize=12,
                    ha="center", va="center", zorder=5)
            ax.text(bx + 0.030, BLOC_Y, f"{blabel}  {bseats} esc.",
                    color=TEXT_MUTED, fontsize=9.5, va="center", zorder=5)
        MAJ_Y = BLOC_Y - 0.048
        ax.text(0.5, MAJ_Y, f"Mayoría absoluta: {majority_b} escaños",
                color=TEXT_MUTED, fontsize=9, ha="center", va="center",
                fontstyle="italic", zorder=5)

        SEP3_Y = MAJ_Y - 0.040
        ax.plot([PAD_X, 1 - PAD_X], [SEP3_Y, SEP3_Y],
                color=SEPARATOR, linewidth=0.8, zorder=4)

        footer_y = CARD_Y0 + 0.038
        disc_y   = footer_y + 0.062
        if custom_subtitle:
            ax.text(0.5, disc_y + 0.062, f'"{custom_subtitle}"',
                    color=TEXT_WHITE, fontsize=11, ha="center", va="center",
                    fontstyle="italic", zorder=5)
        ax.text(0.5, disc_y, disclaimer,
                color=TEXT_MUTED, fontsize=9, ha="center", va="center",
                fontstyle="italic", zorder=5)
        ax.text(0.5, footer_y, "mapa electoral spain",
                color=TEXT_MUTED, fontsize=8.5, ha="center", va="center", zorder=5)

    # ── Save ──────────────────────────────────────────────────────────────────
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
    parser.add_argument("--pie",  dest="mode", action="store_const", const="pie",  help="Forzar modo tarta")
    parser.add_argument("--bar",  dest="mode", action="store_const", const="bar",  help="Forzar modo barra")
    parser.add_argument("--list-parties", action="store_true", help="Lista partidos disponibles")
    parser.set_defaults(mode="auto")

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
        mode=args.mode,
    )


if __name__ == "__main__":
    main()
