---
title: Estimador provincial 2026
---

<div style="text-align:center;margin:1.5rem 0 1.5rem">
  <h1 style="font-size:2rem;font-weight:800;margin:0;line-height:1.1">Estimador provincial 2026</h1>
  <p style="font-size:1.1rem;opacity:.65;margin:.4rem 0 0">Estima el resultado en cada provincia · D'Hondt con barrera 3%</p>
</div>

<p style="max-width:700px;font-size:.9em;line-height:1.6;margin:0 0 1.4rem;opacity:.75">
  Ve provincia a provincia ajustando los porcentajes de voto. La banda de color bajo cada slider muestra el
  rango histórico [mín–máx] del partido en esa circunscripción en las 4 últimas elecciones generales.
  Al terminar las 52 provincias verás el resultado nacional agregado.
</p>

```js
import * as d3 from "npm:d3";
const results     = await FileAttachment("data/summary_province.json").json();
const bloquesMeta = await FileAttachment("data/bloques_meta.json").json();
```

```js
const BASE_ELEC     = "202307";
const REF_ELECTIONS = ["201606", "201904", "201911", "202307"];

const COLORS = {
  ...Object.fromEntries(Object.entries(bloquesMeta).map(([k, v]) => [k, v.color])),
  otros: "#999",
};
const BLOQUES_ORDER = Object.keys(bloquesMeta);
const SEATS_2026    = { "11": -1, "28": +1 };
const convData      = results[BASE_ELEC] ?? {};

const provList = Object.entries(convData)
  .map(([cp, p]) => ({ cp, nombre: p.nombre }))
  .sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));

// Precompute reference ranges: refRanges[cp][siglas] = { min, max }
const refRanges = {};
for (const { cp } of provList) {
  refRanges[cp] = {};
  for (const elecId of REF_ELECTIONS) {
    const pData = results[elecId]?.[cp];
    if (!pData) continue;
    const vc = pData.votos_candidaturas;
    if (!vc) continue;
    const allP = [...(pData.partidos_con_escano ?? []), ...(pData.partidos_sin_escano ?? [])];
    for (const party of allP) {
      const pct = party.votos / vc * 100;
      if (!refRanges[cp][party.siglas]) {
        refRanges[cp][party.siglas] = { min: pct, max: pct };
      } else {
        refRanges[cp][party.siglas].min = Math.min(refRanges[cp][party.siglas].min, pct);
        refRanges[cp][party.siglas].max = Math.max(refRanges[cp][party.siglas].max, pct);
      }
    }
  }
}

// 2023 real national baseline (for delta comparison)
const real2023ByBloc  = {};
const real2023ByParty = {};
for (const { cp } of provList) {
  for (const [blq, n] of Object.entries(convData[cp].escanos_por_bloque ?? {})) {
    real2023ByBloc[blq] = (real2023ByBloc[blq] ?? 0) + n;
  }
  for (const party of (convData[cp].partidos_con_escano ?? [])) {
    if (party.escanos_dhondt > 0)
      real2023ByParty[party.siglas] = (real2023ByParty[party.siglas] ?? 0) + party.escanos_dhondt;
  }
}
```

```js
// ── Media de encuestas ────────────────────────────────────────────────
const encuestaRefEl = (() => {
  const DATOS = [
    { s: "PP",        pct: 31.8, bloque: "dcha_federal" },
    { s: "PSOE",      pct: 26.7, bloque: "izq_federal"  },
    { s: "Vox",       pct: 18.7, bloque: "dcha_federal" },
    { s: "Sumar",     pct:  5.7, bloque: "izq_federal"  },
    { s: "Podemos",   pct:  3.1, bloque: "izq_federal"  },
    { s: "ERC",       pct:  2.0, bloque: "nac_izq"      },
    { s: "SALF",      pct:  1.9, bloque: null            },
    { s: "EH Bildu",  pct:  1.4, bloque: "nac_izq"      },
    { s: "Junts",     pct:  1.1, bloque: "nac_centro"   },
    { s: "PNV",       pct:  1.1, bloque: "nac_centro"   },
    { s: "AA",        pct:  1.1, bloque: "nac_izq"      },
    { s: "BNG",       pct:  1.0, bloque: "nac_izq"      },
    { s: "CC",        pct:  0.3, bloque: "regionalismo" },
    { s: "UPN",       pct:  0.2, bloque: "regionalismo" },
  ];
  const div = document.createElement("div");
  div.style.cssText = "max-width:760px;margin:.8rem 0 1.2rem;padding:.55rem .9rem;background:rgba(0,0,0,.025);border-radius:6px;border:1px solid rgba(0,0,0,.07)";
  const hdr = document.createElement("div");
  hdr.style.cssText = "font-size:.73em;opacity:.5;margin-bottom:.5rem";
  hdr.innerHTML = "<b>Media de encuestas</b> · Ponderado PollCheck · sept. 2026 · <a href=\"https://electomania.es\" target=\"_blank\" style=\"color:inherit;text-decoration:underline\">electomania.es</a>";
  div.appendChild(hdr);
  const chips = document.createElement("div");
  chips.style.cssText = "display:flex;flex-wrap:wrap;gap:5px";
  for (const d of DATOS) {
    const col  = d.bloque ? (COLORS[d.bloque] ?? "#999") : "#999";
    const chip = document.createElement("span");
    chip.style.cssText = `font-size:.78em;font-weight:700;padding:2px 9px;border-radius:20px;background:${col}22;border:1px solid ${col}66;white-space:nowrap`;
    chip.textContent = `${d.s} ${d.pct.toFixed(1).replace(".", ",")}%`;
    chips.appendChild(chip);
  }
  div.appendChild(chips);
  return div;
})();
display(encuestaRefEl);
```

```js
const mainEl = (() => {
  const THRESHOLD = 0.01;
  const OTROS_ID  = "__otros__";
  const BLANCO_ID = "__blancos__";

  const extraParties = [];
  let nuevoCount = 0;
  const provState = {};
  let currentIdx  = 0;
  let showSummary = false;

  // ── D'Hondt ──────────────────────────────────────────────────────
  function dhondt(candidates, seats) {
    if (!seats || !candidates.length) return {};
    const q = [];
    for (const c of candidates)
      for (let d = 1; d <= seats; d++) q.push({ id: c.id, q: c.votes / d });
    q.sort((a, b) => b.q - a.q);
    const out = {};
    for (const { id } of q.slice(0, seats)) out[id] = (out[id] ?? 0) + 1;
    return out;
  }

  function getEntries(cp) {
    const p  = convData[cp];
    const vc = p.votos_candidaturas;
    const allParties = [...(p.partidos_con_escano ?? []), ...(p.partidos_sin_escano ?? [])];
    const shown      = allParties.filter(q => q.votos / vc >= THRESHOLD);
    const otrosVotos = allParties.filter(q => q.votos / vc < THRESHOLD).reduce((s, q) => s + q.votos, 0);
    return [
      ...shown.map(q => ({
        id: q.siglas, label: q.siglas, denominacion: q.denominacion,
        bloque: q.bloque, escanos2023: q.escanos_dhondt ?? 0,
        isBlancos: false, isOtros: false, isNuevo: false, initPct: q.votos / vc * 100,
      })),
      ...(otrosVotos > 0 ? [{
        id: OTROS_ID, label: "Otros",
        denominacion: `Partidos con <1% (${allParties.filter(q => q.votos / vc < THRESHOLD).length})`,
        bloque: "otros", escanos2023: 0,
        isBlancos: false, isOtros: true, isNuevo: false, initPct: otrosVotos / vc * 100,
      }] : []),
      ...extraParties.map(ep => ({
        id: ep.id, label: ep.label, denominacion: "",
        bloque: ep.bloque ?? null, escanos2023: 0,
        isBlancos: false, isOtros: false, isNuevo: true, initPct: 0,
      })),
      {
        id: BLANCO_ID, label: "En blanco", denominacion: "Excluidos del D'Hondt",
        bloque: null, escanos2023: 0,
        isBlancos: true, isOtros: false, isNuevo: false, initPct: 0,
      },
    ];
  }

  function getState(cp) {
    const entries = getEntries(cp);
    if (!provState[cp]) {
      provState[cp] = entries.map(e => e.initPct);
    } else {
      while (provState[cp].length < entries.length)
        provState[cp].splice(provState[cp].length - 1, 0, 0);
    }
    return provState[cp];
  }

  function runDhondtProv(cp) {
    const p         = convData[cp];
    const seats2023 = p.seats_total;
    const seats2026 = seats2023 + (SEATS_2026[cp] ?? 0);
    const entries   = getEntries(cp);
    const pcts      = getState(cp);
    const totalValid = pcts.reduce((s, v) => s + v, 0);
    const threshold  = totalValid * 0.03;
    const cands = entries
      .map((e, i) => ({ e, i }))
      .filter(({ e }) => !e.isBlancos)
      .filter(({ i }) => pcts[i] >= threshold)
      .map(({ e, i }) => ({ id: e.id, votes: pcts[i] }));
    return { sim: dhondt(cands, seats2026), entries, seats2026, seats2023 };
  }

  // ── Projection (estimated provs + 2023 for unvisited) ────────────
  function getProjection() {
    const byBloc  = {};
    const byParty = {};
    let total = 0;
    let estimatedCount = 0;

    for (const { cp } of provList) {
      if (provState[cp]) {
        // Use live estimate
        estimatedCount++;
        const { sim, entries, seats2026 } = runDhondtProv(cp);
        total += seats2026;
        for (const [id, n] of Object.entries(sim)) {
          byParty[id] = (byParty[id] ?? 0) + n;
          const entry = entries.find(e => e.id === id);
          const blq   = entry?.bloque ?? "otros";
          byBloc[blq] = (byBloc[blq] ?? 0) + n;
        }
      } else {
        // Use 2023 real
        const p = convData[cp];
        total += p.seats_total + (SEATS_2026[cp] ?? 0);
        for (const [blq, n] of Object.entries(p.escanos_por_bloque ?? {})) {
          byBloc[blq] = (byBloc[blq] ?? 0) + n;
        }
        for (const party of (p.partidos_con_escano ?? [])) {
          if (party.escanos_dhondt > 0)
            byParty[party.siglas] = (byParty[party.siglas] ?? 0) + party.escanos_dhondt;
        }
      }
    }
    return { byBloc, byParty, total, estimatedCount };
  }

  // ── Seat bar helper ───────────────────────────────────────────────
  function buildSeatBar(label, escByBlock, seats, opacity) {
    const cont = document.createElement("div");
    cont.style.cssText = "flex:1";
    const lbl = document.createElement("div");
    lbl.style.cssText = "font-size:.7em;opacity:.5;font-weight:600;margin-bottom:3px";
    lbl.textContent = label;
    cont.appendChild(lbl);
    const bar = document.createElement("div");
    bar.style.cssText = "display:flex;height:26px;border-radius:4px;overflow:hidden;gap:1px;background:#eee";
    const sorted = Object.entries(escByBlock)
      .filter(([, n]) => n > 0)
      .sort(([a], [b]) => BLOQUES_ORDER.indexOf(a) - BLOQUES_ORDER.indexOf(b));
    let placed = 0;
    for (const [blq, n] of sorted) {
      placed += n;
      const seg = document.createElement("div");
      seg.style.cssText = `flex:${n};background:${COLORS[blq] ?? "#999"};opacity:${opacity};display:flex;align-items:center;justify-content:center`;
      if (n / seats > 0.06) {
        const t = document.createElement("span");
        t.style.cssText = "font-size:9px;color:#fff;font-weight:700;pointer-events:none";
        t.textContent = n;
        seg.appendChild(t);
      }
      seg.title = `${bloquesMeta[blq]?.label ?? blq}: ${n} esc`;
      bar.appendChild(seg);
    }
    if (placed < seats) {
      const rem = document.createElement("div");
      rem.style.cssText = `flex:${seats - placed};background:#ddd`;
      bar.appendChild(rem);
    }
    cont.appendChild(bar);
    return cont;
  }

  // ── Tooltip ───────────────────────────────────────────────────────
  const tooltip = document.createElement("div");
  tooltip.style.cssText = "position:fixed;z-index:9999;background:#fff;border:1px solid #ddd;border-radius:8px;padding:10px 14px;font-size:.78em;box-shadow:0 4px 16px rgba(0,0,0,.18);pointer-events:none;display:none;min-width:220px;max-width:320px;line-height:1.5";
  document.body.appendChild(tooltip);

  function posTooltip(evt) {
    const x = evt.clientX + 14;
    const y = evt.clientY - 8;
    tooltip.style.left = Math.min(x, window.innerWidth  - tooltip.offsetWidth  - 12) + "px";
    tooltip.style.top  = Math.max(8, Math.min(y, window.innerHeight - tooltip.offsetHeight - 12)) + "px";
  }

  function buildTooltipContent(byBloc, byParty) {
    const { estimatedCount } = getProjection();
    let html = `<div style="font-weight:700;margin-bottom:6px;font-size:.9em">Proyección acumulada<br><span style="font-weight:400;opacity:.55;font-size:.88em">${estimatedCount} prov. estimadas · ${provList.length - estimatedCount} en 2023</span></div>`;
    html += `<div style="border-top:1px solid #eee;margin-bottom:6px;padding-top:6px">`;

    for (const blq of BLOQUES_ORDER) {
      const n = byBloc[blq] ?? 0;
      if (!n) continue;
      const real = real2023ByBloc[blq] ?? 0;
      const d    = n - real;
      const col  = COLORS[blq] ?? "#999";
      const lbl  = bloquesMeta[blq]?.label ?? blq;
      const dStr = d === 0 ? "=" : (d > 0 ? `+${d}` : `${d}`);
      const dCol = d > 0 ? "#2E7D32" : d < 0 ? "#C62828" : "#888";
      html += `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
        <span style="display:flex;align-items:center;gap:5px"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${col}"></span><b>${lbl}</b></span>
        <span>${n} esc <span style="color:${dCol};font-weight:700">(${dStr})</span></span>
      </div>`;

      // Parties in this bloc
      const partiesInBloc = Object.entries(byParty)
        .filter(([id]) => !id.startsWith("__"))
        .filter(([id]) => {
          for (const { cp } of provList) {
            const entry = (convData[cp].partidos_con_escano ?? []).find(e => e.siglas === id);
            if (entry?.bloque === blq) return true;
          }
          // also check extra parties
          const ep = extraParties.find(x => x.id === id);
          if (ep?.bloque === blq) return true;
          return false;
        })
        .sort((a, b) => b[1] - a[1]);

      for (const [id, pn] of partiesInBloc) {
        const pr = real2023ByParty[id] ?? 0;
        const pd = pn - pr;
        const pdStr = pd === 0 ? "=" : (pd > 0 ? `+${pd}` : `${pd}`);
        const pdCol = pd > 0 ? "#2E7D32" : pd < 0 ? "#C62828" : "#888";
        html += `<div style="display:flex;justify-content:space-between;padding-left:14px;opacity:.8;font-size:.93em">
          <span>${id}</span>
          <span>${pn} <span style="color:${pdCol}">(${pdStr})</span></span>
        </div>`;
      }
    }
    html += `</div>`;

    // Totals
    const totalEst = Object.values(byBloc).reduce((s, v) => s + v, 0);
    const total2023 = Object.values(real2023ByBloc).reduce((s, v) => s + v, 0);
    const maj = Math.ceil(totalEst / 2) + 1;
    html += `<div style="border-top:1px solid #eee;padding-top:6px;opacity:.7">Total: <b>${totalEst}</b> · Mayoría abs.: <b>${maj}</b></div>`;
    return html;
  }

  // ── Running tally bar ─────────────────────────────────────────────
  const tallyWrap = document.createElement("div");
  tallyWrap.style.cssText = "max-width:780px;margin-bottom:1rem;padding:.7rem .9rem;border:1px solid #e0e0e0;border-radius:8px;background:var(--theme-background-alt,#fff)";

  function renderTally() {
    tallyWrap.innerHTML = "";
    const { byBloc, byParty, total, estimatedCount } = getProjection();

    const hdr = document.createElement("div");
    hdr.style.cssText = "display:flex;justify-content:space-between;align-items:center;margin-bottom:.45rem";
    const lbl = document.createElement("span");
    lbl.style.cssText = "font-size:.72em;font-weight:700;opacity:.5;letter-spacing:.04em";
    lbl.textContent = "RECUENTO ACUMULADO";
    hdr.appendChild(lbl);
    const sub = document.createElement("span");
    sub.style.cssText = "font-size:.7em;opacity:.4";
    sub.textContent = `${estimatedCount} estimadas · ${provList.length - estimatedCount} en 2023`;
    hdr.appendChild(sub);
    tallyWrap.appendChild(hdr);

    // Bloc bar
    const bar = document.createElement("div");
    bar.style.cssText = "display:flex;height:28px;border-radius:5px;overflow:hidden;gap:1px;background:#eee;cursor:default";

    const sorted = Object.entries(byBloc)
      .filter(([, n]) => n > 0)
      .sort(([a], [b]) => BLOQUES_ORDER.indexOf(a) - BLOQUES_ORDER.indexOf(b));

    for (const [blq, n] of sorted) {
      const col  = COLORS[blq] ?? "#999";
      const real = real2023ByBloc[blq] ?? 0;
      const d    = n - real;
      const seg  = document.createElement("div");
      seg.style.cssText = `flex:${n};background:${col};display:flex;align-items:center;justify-content:center;position:relative`;

      if (n / total > 0.05) {
        const t = document.createElement("span");
        t.style.cssText = "font-size:9px;color:#fff;font-weight:700;pointer-events:none;user-select:none";
        t.textContent = n;
        seg.appendChild(t);
      }

      seg.addEventListener("mouseenter", (evt) => {
        const { byBloc: bb, byParty: bp } = getProjection();
        tooltip.innerHTML = buildTooltipContent(bb, bp);
        tooltip.style.display = "";
        posTooltip(evt);
      });
      seg.addEventListener("mousemove", posTooltip);
      seg.addEventListener("mouseleave", () => { tooltip.style.display = "none"; });
      bar.appendChild(seg);
    }
    tallyWrap.appendChild(bar);

    // Bloc labels row
    const labelsRow = document.createElement("div");
    labelsRow.style.cssText = "display:flex;gap:10px;flex-wrap:wrap;margin-top:.4rem";
    for (const [blq, n] of sorted) {
      const col  = COLORS[blq] ?? "#999";
      const real = real2023ByBloc[blq] ?? 0;
      const d    = n - real;
      const dStr = d === 0 ? "=" : (d > 0 ? `+${d}` : `${d}`);
      const dCol = d > 0 ? "#2E7D32" : d < 0 ? "#C62828" : "#888";
      const chip = document.createElement("span");
      chip.style.cssText = "font-size:.72em;display:flex;align-items:center;gap:4px";
      chip.innerHTML = `<span style="width:8px;height:8px;border-radius:2px;background:${col};display:inline-block"></span><b>${n}</b> ${bloquesMeta[blq]?.label ?? blq} <span style="color:${dCol};font-weight:700">(${dStr})</span>`;
      labelsRow.appendChild(chip);
    }
    tallyWrap.appendChild(labelsRow);
  }

  // ── Root DOM ──────────────────────────────────────────────────────
  const wrap = document.createElement("div");
  wrap.style.cssText = "max-width:780px";
  wrap.appendChild(tallyWrap);
  const progressWrap = document.createElement("div");
  progressWrap.style.cssText = "margin-bottom:1.2rem";
  wrap.appendChild(progressWrap);
  const cardWrap    = document.createElement("div");
  wrap.appendChild(cardWrap);
  const summaryWrap = document.createElement("div");
  summaryWrap.style.display = "none";
  wrap.appendChild(summaryWrap);

  // ── Progress ──────────────────────────────────────────────────────
  function renderProgress() {
    progressWrap.innerHTML = "";
    const row = document.createElement("div");
    row.style.cssText = "display:flex;align-items:center;gap:12px;margin-bottom:.45rem;flex-wrap:wrap";
    if (showSummary) {
      const label = document.createElement("span");
      label.style.cssText = "font-size:.82em;opacity:.6;white-space:nowrap";
      label.textContent = `${provList.length} / ${provList.length} provincias completadas`;
      row.appendChild(label);
    } else {
      const label = document.createElement("span");
      label.style.cssText = "font-size:.82em;opacity:.6;white-space:nowrap";
      label.textContent = `Provincia ${currentIdx + 1} de ${provList.length}`;
      row.appendChild(label);
      const jumpSel = document.createElement("select");
      jumpSel.style.cssText = "font-size:.82em;border:1px solid #ddd;border-radius:4px;padding:2px 8px;cursor:pointer;background:var(--theme-background-alt,#fff);max-width:220px";
      for (let i = 0; i < provList.length; i++) {
        const opt = document.createElement("option");
        opt.value = i;
        opt.textContent = provList[i].nombre;
        if (i === currentIdx) opt.selected = true;
        jumpSel.appendChild(opt);
      }
      jumpSel.addEventListener("change", () => {
        currentIdx = +jumpSel.value;
        showSummary = false;
        renderProgress();
        renderCard();
        window.scrollTo(0, 0);
      });
      row.appendChild(jumpSel);
    }
    progressWrap.appendChild(row);
    const track = document.createElement("div");
    track.style.cssText = "height:4px;background:#e0e0e0;border-radius:2px;overflow:hidden";
    const fill = document.createElement("div");
    fill.style.cssText = `height:100%;width:${showSummary ? 100 : (currentIdx / provList.length * 100)}%;background:#457B9D;border-radius:2px;transition:width .3s`;
    track.appendChild(fill);
    progressWrap.appendChild(track);
  }

  // ── Province card ─────────────────────────────────────────────────
  function renderCard() {
    cardWrap.innerHTML = "";
    summaryWrap.style.display = "none";
    if (showSummary) { renderSummary(); return; }

    const { cp, nombre } = provList[currentIdx];
    const p         = convData[cp];
    const vc        = p.votos_candidaturas;
    const seats2023 = p.seats_total;
    const seatsDelta = SEATS_2026[cp] ?? 0;
    const seats2026 = seats2023 + seatsDelta;
    const entries   = getEntries(cp);
    const pcts      = getState(cp);   // initialises provState[cp]
    const ranges    = refRanges[cp] ?? {};

    const card = document.createElement("div");
    card.style.cssText = "border:1px solid #e0e0e0;border-radius:10px;padding:1.2rem 1.4rem;background:var(--theme-background-alt,#fff)";

    // Card header
    const cardHdr = document.createElement("div");
    cardHdr.style.cssText = "display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.6rem;flex-wrap:wrap;gap:6px";
    const cardTitle = document.createElement("div");
    const provName = document.createElement("div");
    provName.style.cssText = "font-size:1.15rem;font-weight:800;margin-bottom:2px";
    provName.textContent = nombre;
    cardTitle.appendChild(provName);
    const provMeta = document.createElement("div");
    provMeta.style.cssText = "font-size:.78em;opacity:.5";
    provMeta.textContent = `${seats2026} escaños · ${vc.toLocaleString("es-ES")} votos en 2023`;
    cardTitle.appendChild(provMeta);
    cardHdr.appendChild(cardTitle);
    if (seatsDelta !== 0) {
      const badge = document.createElement("span");
      badge.style.cssText = "font-size:.75em;background:#FFF3CD;border:1px solid #FFC107;border-radius:4px;padding:2px 8px;font-weight:600;align-self:center";
      badge.textContent = `${seatsDelta > 0 ? "+" : ""}${seatsDelta} escaño (ajuste 2026)`;
      cardHdr.appendChild(badge);
    }
    card.appendChild(cardHdr);

    // ── Último escaño 2023 ────────────────────────────────────────
    if (p.partido_ultimo_escano) {
      const lastRow = document.createElement("div");
      lastRow.style.cssText = "font-size:.78em;margin-bottom:.7rem;padding:.35rem .7rem;background:rgba(0,0,0,.03);border-radius:5px;border-left:3px solid #bbb;display:flex;align-items:center;gap:8px";

      const icon = document.createElement("span");
      icon.textContent = "🏁";
      icon.style.cssText = "font-size:1em";
      lastRow.appendChild(icon);

      const txt = document.createElement("span");
      const lastParty = p.partido_ultimo_escano;
      // Find bloque for color
      const lastEntry = (p.partidos_con_escano ?? []).find(e => e.siglas === lastParty);
      const lastCol   = lastEntry?.bloque ? (COLORS[lastEntry.bloque] ?? "#999") : "#999";
      const barrPct   = p.barrera_real_pct != null ? p.barrera_real_pct.toFixed(1) : "—";

      txt.innerHTML = `<b>Último escaño 2023:</b> <span style="color:${lastCol};font-weight:700">${lastParty}</span> con <b>${barrPct}%</b>`;
      lastRow.appendChild(txt);

      const hint = document.createElement("span");
      hint.style.cssText = "opacity:.45;font-size:.9em";
      hint.textContent = `(barrera real de la circunscripción)`;
      lastRow.appendChild(hint);

      card.appendChild(lastRow);
    }

    // Seat bars
    const barWrap = document.createElement("div");
    barWrap.style.cssText = "display:flex;gap:12px;margin-bottom:.8rem";
    card.appendChild(barWrap);

    // Total counter
    const totalEl = document.createElement("div");
    totalEl.style.cssText = "font-size:.82em;font-weight:600;padding:4px 10px;border-radius:5px;margin-bottom:.7rem;display:inline-block";
    card.appendChild(totalEl);

    // Grid container
    const gridWrap = document.createElement("div");
    card.appendChild(gridWrap);

    // Add party + reset buttons
    const btnsRow = document.createElement("div");
    btnsRow.style.cssText = "margin-top:.7rem;display:flex;gap:8px;flex-wrap:wrap";

    const addBtn = document.createElement("button");
    addBtn.textContent = "+ Añadir partido";
    addBtn.style.cssText = "font-size:.78em;border:1px dashed #aaa;border-radius:5px;padding:4px 13px;cursor:pointer;background:transparent;opacity:.7";
    addBtn.addEventListener("click", () => {
      nuevoCount++;
      extraParties.push({ id: `__nuevo_${nuevoCount}__`, label: `Nuevo ${nuevoCount}`, bloque: null });
      for (const cp2 of Object.keys(provState))
        provState[cp2].splice(provState[cp2].length - 1, 0, 0);
      rebuildGrid(); updateCard();
    });
    btnsRow.appendChild(addBtn);

    const resetProvBtn = document.createElement("button");
    resetProvBtn.textContent = "↺ Restablecer";
    resetProvBtn.style.cssText = "font-size:.78em;border:1px solid #ddd;border-radius:5px;padding:4px 12px;cursor:pointer;background:transparent;opacity:.6";
    resetProvBtn.addEventListener("click", () => {
      getEntries(cp).forEach((e, i) => { pcts[i] = e.initPct; });
      rebuildGrid(); updateCard();
    });
    btnsRow.appendChild(resetProvBtn);
    card.appendChild(btnsRow);

    // Navigation
    const navRow = document.createElement("div");
    navRow.style.cssText = "display:flex;justify-content:space-between;align-items:center;margin-top:1rem;padding-top:.8rem;border-top:1px solid #f0f0f0;gap:8px";
    const prevBtn = document.createElement("button");
    prevBtn.textContent = "← Anterior";
    prevBtn.disabled = currentIdx === 0;
    prevBtn.style.cssText = `font-size:.85em;border:1px solid #ddd;border-radius:5px;padding:6px 16px;cursor:pointer;background:transparent;opacity:${currentIdx === 0 ? ".3" : "1"}`;
    prevBtn.addEventListener("click", () => { currentIdx--; renderProgress(); renderCard(); window.scrollTo(0,0); });
    const isLast = currentIdx === provList.length - 1;
    const nextBtn = document.createElement("button");
    nextBtn.textContent = isLast ? "Ver resultados nacionales →" : "Siguiente provincia →";
    nextBtn.style.cssText = `font-size:.85em;border:none;border-radius:5px;padding:7px 18px;cursor:pointer;background:${isLast ? "#2E7D32" : "#457B9D"};color:#fff;font-weight:600`;
    nextBtn.addEventListener("click", () => {
      if (isLast) { showSummary = true; renderProgress(); renderCard(); window.scrollTo(0,0); }
      else { currentIdx++; renderProgress(); renderCard(); window.scrollTo(0,0); }
    });
    navRow.appendChild(prevBtn);
    navRow.appendChild(nextBtn);
    card.appendChild(navRow);
    cardWrap.appendChild(card);

    // ── Grid builder ──────────────────────────────────────────────
    function rebuildGrid() {
      gridWrap.innerHTML = "";
      const ents = getEntries(cp);
      const ps   = getState(cp);
      const grid = document.createElement("div");
      grid.style.cssText = "display:grid;grid-template-columns:minmax(70px,150px) 60px 1fr 40px 40px 34px 22px;align-items:start;column-gap:8px;row-gap:3px";
      gridWrap.appendChild(grid);

      for (const [txt, align] of [
        ["Partido","left"],["% voto","right"],
        ["Slider  ·  banda = rango histórico 4 últ. elecciones","left"],
        ["2023","center"],["Est.","center"],["Δ","center"],["",""]
      ]) {
        const h = document.createElement("div");
        h.style.cssText = `font-size:.65em;opacity:.4;font-weight:600;border-bottom:1px solid #e0e0e0;padding-bottom:3px;text-align:${align}`;
        h.textContent = txt;
        grid.appendChild(h);
      }

      ents.forEach((e, i) => {
        const col = e.bloque ? (COLORS[e.bloque] ?? "#999") : "#ccc";
        const ref = (!e.isBlancos && !e.isOtros && !e.isNuevo) ? (ranges[e.id] ?? null) : null;

        // Name
        const nameCell = document.createElement("div");
        nameCell.style.cssText = "display:flex;align-items:center;gap:5px;overflow:hidden;padding-top:7px";
        const dot = document.createElement("span");
        dot.style.cssText = `width:8px;height:8px;border-radius:50%;background:${col};flex-shrink:0`;
        nameCell.appendChild(dot);
        if (e.isNuevo) {
          const inp = document.createElement("input");
          inp.type = "text"; inp.value = e.label; inp.placeholder = "Nombre";
          inp.style.cssText = "font-size:.8em;font-weight:700;border:none;border-bottom:1px solid #ccc;background:transparent;width:100%;min-width:0;outline:none";
          inp.addEventListener("input", () => { e.label = inp.value; const ep = extraParties.find(x => x.id === e.id); if (ep) ep.label = inp.value; });
          nameCell.appendChild(inp);
        } else {
          const nm = document.createElement("span");
          nm.style.cssText = "font-size:.8em;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis";
          nm.textContent = e.label; nm.title = e.denominacion ?? "";
          nameCell.appendChild(nm);
        }
        grid.appendChild(nameCell);

        // % input
        const numInp = document.createElement("input");
        numInp.type = "number"; numInp.min = "0"; numInp.max = "100"; numInp.step = "0.1";
        numInp.value = ps[i].toFixed(1);
        numInp.style.cssText = "width:100%;font-size:.8em;border:1px solid #e0e0e0;border-radius:3px;padding:2px 4px;text-align:right;box-sizing:border-box;margin-top:5px";
        const numCell = document.createElement("div");
        numCell.appendChild(numInp);
        grid.appendChild(numCell);

        // Slider + band
        const sliderCol = document.createElement("div");
        sliderCol.style.cssText = "display:flex;flex-direction:column;padding-top:4px";
        const slider = document.createElement("input");
        slider.type = "range"; slider.min = "0"; slider.max = "100"; slider.step = "0.1";
        slider.value = ps[i].toFixed(1);
        slider.style.cssText = `width:100%;accent-color:${e.isBlancos ? "#aaa" : col};margin:0 0 2px`;
        sliderCol.appendChild(slider);

        if (ref) {
          const bLeft  = Math.min(ref.min, ref.max);
          const bRight = Math.max(ref.min, ref.max);
          const bWidth = bRight - bLeft;
          const refTrack = document.createElement("div");
          refTrack.style.cssText = "position:relative;height:7px;margin:0 0 2px";
          const trackBg = document.createElement("div");
          trackBg.style.cssText = "position:absolute;top:50%;transform:translateY(-50%);left:0;right:0;height:2px;background:#e8e8e8;border-radius:1px";
          refTrack.appendChild(trackBg);
          const band = document.createElement("div");
          band.style.cssText = `position:absolute;top:50%;transform:translateY(-50%);left:${bLeft}%;width:${Math.max(bWidth, 0.5)}%;height:5px;background:${col}44;border:1px solid ${col}77;border-radius:2px`;
          band.title = `Rango histórico: ${bLeft.toFixed(1)}% – ${bRight.toFixed(1)}%`;
          refTrack.appendChild(band);
          const mkTick = (pct) => { const t = document.createElement("div"); t.style.cssText = `position:absolute;top:0;left:${pct}%;transform:translateX(-50%);height:7px;width:1.5px;background:${col}99`; return t; };
          refTrack.appendChild(mkTick(bLeft)); refTrack.appendChild(mkTick(bRight));
          sliderCol.appendChild(refTrack);
          const labelsRow = document.createElement("div");
          labelsRow.style.cssText = "position:relative;height:11px;margin-bottom:1px";
          const mkLbl = (pct, txt) => { const l = document.createElement("span"); l.style.cssText = `position:absolute;font-size:.58em;opacity:.4;left:${Math.max(1,Math.min(pct,94))}%;transform:translateX(-50%);white-space:nowrap`; l.textContent = txt; return l; };
          labelsRow.appendChild(mkLbl(bLeft, bLeft.toFixed(1)+"%"));
          if (bWidth > 4) labelsRow.appendChild(mkLbl(bRight, bRight.toFixed(1)+"%"));
          sliderCol.appendChild(labelsRow);
        }
        grid.appendChild(sliderCol);

        // 2023 seats
        const s23 = document.createElement("div");
        s23.style.cssText = "text-align:center;font-size:.8em;opacity:.45;padding-top:7px";
        s23.textContent = (e.isBlancos || e.isOtros || e.isNuevo) ? "—" : e.escanos2023;
        grid.appendChild(s23);

        // Sim seats
        const sSim = document.createElement("div");
        sSim.style.cssText = "text-align:center;font-size:.8em;font-weight:700;padding-top:7px";
        sSim.className = "seats-sim";
        grid.appendChild(sSim);

        // Delta
        const dEl = document.createElement("div");
        dEl.style.cssText = "text-align:center;font-size:.8em;font-weight:700;padding-top:7px";
        dEl.className = "seats-delta";
        grid.appendChild(dEl);

        // Action btn
        const btn = document.createElement("button");
        btn.style.cssText = "font-size:.72em;border:none;background:transparent;cursor:pointer;opacity:.3;padding:1px 3px;margin-top:6px";
        if (e.isNuevo) {
          btn.textContent = "✕"; btn.title = "Eliminar partido";
          btn.addEventListener("click", () => {
            const idx = extraParties.findIndex(x => x.id === e.id);
            if (idx !== -1) extraParties.splice(idx, 1);
            for (const cp2 of Object.keys(provState)) {
              const ents2 = getEntries(cp2);
              const eIdx  = ents2.findIndex(x => x.id === e.id);
              if (eIdx !== -1) provState[cp2].splice(eIdx, 1);
            }
            rebuildGrid(); updateCard();
          });
        } else {
          btn.textContent = "↺"; btn.title = "Restablecer a 2023";
          btn.addEventListener("click", () => { ps[i] = e.initPct; slider.value = ps[i].toFixed(1); numInp.value = ps[i].toFixed(1); updateCard(); });
        }
        grid.appendChild(btn);

        slider.addEventListener("input",  () => { ps[i] = +slider.value; numInp.value = ps[i].toFixed(1); updateCard(); });
        numInp.addEventListener("change", () => { ps[i] = Math.max(0, Math.min(100, +numInp.value)); slider.value = ps[i].toFixed(1); updateCard(); });
      });
    }

    // ── Update ────────────────────────────────────────────────────
    function updateCard() {
      const { sim, entries: ents, seats2026: s6, seats2023: s3 } = runDhondtProv(cp);
      const total = pcts.reduce((s, v) => s + v, 0);
      const diff  = total - 100;
      const ok    = Math.abs(diff) < 0.1;
      if (ok)        { totalEl.textContent = "Total: 100% ✓"; totalEl.style.background = "#E8F5E9"; totalEl.style.color = "#2E7D32"; }
      else if (diff > 0) { totalEl.textContent = `Total: ${total.toFixed(1)}% — exceso ${diff.toFixed(1)}%`; totalEl.style.background = "#FFEBEE"; totalEl.style.color = "#C62828"; }
      else           { totalEl.textContent = `Total: ${total.toFixed(1)}% — falta ${(-diff).toFixed(1)}%`; totalEl.style.background = "#FFF8E1"; totalEl.style.color = "#E65100"; }

      const simCells   = gridWrap.querySelectorAll(".seats-sim");
      const deltaCells = gridWrap.querySelectorAll(".seats-delta");
      ents.forEach((e2, idx) => {
        const simS = e2.isBlancos ? null : (sim[e2.id] ?? 0);
        if (simCells[idx])   simCells[idx].textContent = simS === null ? "—" : simS;
        if (deltaCells[idx]) {
          if (simS === null || e2.isOtros) { deltaCells[idx].textContent = "—"; deltaCells[idx].style.color = "#aaa"; }
          else {
            const d = simS - e2.escanos2023;
            deltaCells[idx].textContent = d === 0 ? "=" : (d > 0 ? "+" + d : String(d));
            deltaCells[idx].style.color = d > 0 ? "#2E7D32" : d < 0 ? "#C62828" : "#888";
          }
        }
      });

      barWrap.innerHTML = "";
      const realByBlock = {};
      for (const [blq, n] of Object.entries(convData[cp].escanos_por_bloque ?? {})) if (n > 0) realByBlock[blq] = n;
      const simByBlock = {};
      for (const [id, n] of Object.entries(sim)) {
        const entry = ents.find(e2 => e2.id === id);
        simByBlock[entry?.bloque ?? "otros"] = (simByBlock[entry?.bloque ?? "otros"] ?? 0) + n;
      }
      barWrap.appendChild(buildSeatBar(`Real 2023 (${s3} esc)`, realByBlock, s3, 0.72));
      barWrap.appendChild(buildSeatBar(`Estimado 2026 (${s6} esc)`, simByBlock, s6, 0.92));

      // Update running tally
      renderTally();
    }

    rebuildGrid();
    updateCard();
  }

  // ── Summary ───────────────────────────────────────────────────────
  function renderSummary() {
    summaryWrap.style.display = "";
    summaryWrap.innerHTML = "";

    const totalSeats       = {};
    const totalByBloc      = {};
    const seats2023ByParty = {};
    let totalSeatsCount    = 0;
    let totalReal2023      = 0;
    const real2023ByBlocSum = {};

    for (const { cp } of provList) {
      const { sim, entries, seats2026 } = runDhondtProv(cp);
      totalSeatsCount += seats2026;
      for (const [blq, n] of Object.entries(convData[cp].escanos_por_bloque ?? {})) {
        real2023ByBlocSum[blq] = (real2023ByBlocSum[blq] ?? 0) + n;
        totalReal2023 += n;
      }
      for (const party of (convData[cp].partidos_con_escano ?? [])) {
        if (party.escanos_dhondt > 0)
          seats2023ByParty[party.siglas] = (seats2023ByParty[party.siglas] ?? 0) + party.escanos_dhondt;
      }
      for (const [id, n] of Object.entries(sim)) {
        totalSeats[id] = (totalSeats[id] ?? 0) + n;
        const entry = entries.find(e => e.id === id);
        const blq   = entry?.bloque ?? "otros";
        totalByBloc[blq] = (totalByBloc[blq] ?? 0) + n;
      }
    }

    const maj = Math.ceil(totalSeatsCount / 2) + 1;

    const hdr = document.createElement("div");
    hdr.style.cssText = "margin-bottom:1.2rem";
    const h2 = document.createElement("h2");
    h2.style.cssText = "font-size:1.4rem;font-weight:800;margin:0 0 .3rem";
    h2.textContent = "Resultado nacional estimado";
    hdr.appendChild(h2);
    const sub = document.createElement("p");
    sub.style.cssText = "font-size:.85em;opacity:.6;margin:0";
    sub.textContent = `${totalSeatsCount} escaños totales · Mayoría absoluta: ${maj}`;
    hdr.appendChild(sub);
    summaryWrap.appendChild(hdr);

    const natBars = document.createElement("div");
    natBars.style.cssText = "display:flex;gap:12px;margin-bottom:1rem";
    natBars.appendChild(buildSeatBar(`Real 2023 (${totalReal2023} esc)`, real2023ByBlocSum, totalReal2023, 0.72));
    natBars.appendChild(buildSeatBar(`Estimado 2026 (${totalSeatsCount} esc)`, totalByBloc, totalSeatsCount, 0.92));
    summaryWrap.appendChild(natBars);

    const majRow = document.createElement("div");
    majRow.style.cssText = "font-size:.83em;margin-bottom:1.2rem;padding:.5rem .9rem;background:var(--theme-background-alt,#f8f9fa);border-radius:6px;border:1px solid #e0e0e0;display:flex;flex-wrap:wrap;gap:12px";
    const leftSeats  = ["izq_federal","nac_izq"].reduce((s, b) => s + (totalByBloc[b] ?? 0), 0);
    const rightSeats = ["dcha_federal"].reduce((s, b) => s + (totalByBloc[b] ?? 0), 0);
    majRow.innerHTML = `<b>Mayoría absoluta:</b> ${maj} &nbsp;·&nbsp; <span style="color:${COLORS.izq_federal}"><b>Izq. federal:</b> ${leftSeats}</span> &nbsp;·&nbsp; <span style="color:${COLORS.dcha_federal}"><b>Dcha. federal:</b> ${rightSeats}</span>`;
    summaryWrap.appendChild(majRow);

    const tableHdr = document.createElement("div");
    tableHdr.style.cssText = "font-size:.78em;font-weight:700;opacity:.45;margin-bottom:.5rem;letter-spacing:.05em";
    tableHdr.textContent = "ESCAÑOS POR PARTIDO";
    summaryWrap.appendChild(tableHdr);

    const table = document.createElement("div");
    table.style.cssText = "display:grid;grid-template-columns:minmax(80px,180px) 60px 60px 50px;column-gap:10px;row-gap:4px;font-size:.83em;max-width:430px";
    for (const [txt, align] of [["Partido",""],["2023","center"],["Est. 2026","center"],["Δ","center"]]) {
      const h = document.createElement("div");
      h.style.cssText = `font-weight:600;opacity:.4;text-align:${align};border-bottom:1px solid #eee;padding-bottom:3px`;
      h.textContent = txt;
      table.appendChild(h);
    }
    for (const [id, n] of Object.entries(totalSeats).filter(([id]) => !id.startsWith("__")).sort((a, b) => b[1] - a[1])) {
      let bloque = "otros";
      for (const { cp } of provList) {
        const entry = getEntries(cp).find(e => e.id === id);
        if (entry?.bloque) { bloque = entry.bloque; break; }
      }
      const col   = COLORS[bloque] ?? "#999";
      const real  = seats2023ByParty[id] ?? 0;
      const delta = n - real;
      const nameDiv = document.createElement("div");
      nameDiv.style.cssText = "display:flex;align-items:center;gap:6px";
      const dot2 = document.createElement("span");
      dot2.style.cssText = `width:7px;height:7px;border-radius:50%;background:${col};flex-shrink:0`;
      nameDiv.appendChild(dot2);
      nameDiv.appendChild(Object.assign(document.createElement("span"), { textContent: id }));
      table.appendChild(nameDiv);
      const r = document.createElement("div"); r.style.cssText = "text-align:center;opacity:.5"; r.textContent = real || "—"; table.appendChild(r);
      const s = document.createElement("div"); s.style.cssText = "text-align:center;font-weight:700"; s.textContent = n; table.appendChild(s);
      const d = document.createElement("div");
      d.style.cssText = `text-align:center;font-weight:700;color:${delta > 0 ? "#2E7D32" : delta < 0 ? "#C62828" : "#888"}`;
      d.textContent = delta === 0 ? "=" : (delta > 0 ? "+" + delta : String(delta));
      table.appendChild(d);
    }
    summaryWrap.appendChild(table);

    const backBtn = document.createElement("button");
    backBtn.textContent = "← Volver a provincias";
    backBtn.style.cssText = "margin-top:1.5rem;font-size:.85em;border:1px solid #ddd;border-radius:5px;padding:7px 18px;cursor:pointer;background:transparent";
    backBtn.addEventListener("click", () => { showSummary = false; currentIdx = provList.length - 1; summaryWrap.style.display = "none"; renderProgress(); renderCard(); });
    summaryWrap.appendChild(backBtn);
  }

  renderTally();
  renderProgress();
  renderCard();
  return wrap;
})();
display(mainEl);
```

---

> **Nota metodológica.** Base de partida: resultado oficial Jul 2023 por circunscripción. La banda bajo cada slider muestra el rango \[mín–máx\] de voto del partido en esa provincia en las 4 últimas elecciones generales (Jun 2016, Abr 2019, Nov 2019, Jul 2023). El recuento acumulado combina las provincias ya estimadas con los resultados reales de 2023 para las restantes. Barrera legal del 3% provincial (LOREG art. 163). Escaños de Cádiz (−1) y Madrid (+1) actualizados al ajuste poblacional de 2026.
