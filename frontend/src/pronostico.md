---
title: Simulador electoral 2026
---

<div style="text-align:center;margin:1.5rem 0 1.5rem">
  <h1 style="font-size:2rem;font-weight:800;margin:0;line-height:1.1">Simulador electoral 2026</h1>
  <p style="font-size:1.1rem;opacity:.65;margin:.4rem 0 0">¿Cómo afecta el reparto de voto a los escaños? · Por provincia</p>
</div>

<p style="max-width:700px;font-size:.9em;line-height:1.6;margin:0 0 1.4rem;opacity:.75">
  Los sliders parten del resultado real de Jul 2023. Muévelos libremente — el contador muestra cuánto
  queda por asignar para llegar al 100%. Los votos en blanco se excluyen del reparto D'Hondt.
  "Otros" agrupa los partidos que obtuvieron menos del 1% en esa provincia.
</p>

```js
import * as d3 from "npm:d3";
const results     = await FileAttachment("data/summary_province.json").json();
const bloquesMeta = await FileAttachment("data/bloques_meta.json").json();
```

```js
const ELEC_ID  = "202307";
const convData = results[ELEC_ID] ?? {};

const COLORS = {
  ...Object.fromEntries(Object.entries(bloquesMeta).map(([k, v]) => [k, v.color])),
  otros: "#999",
};
const BLOQUES_ORDER = Object.keys(bloquesMeta);

// Cambios de escaños para las elecciones de 2026 (ajuste poblacional)
const SEATS_2026 = { "11": -1, "28": +1 }; // Cádiz -1, Madrid +1

const provOptions = Object.entries(convData)
  .map(([cp, p]) => ({ cp, nombre: p.nombre }))
  .sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));

const provInput = Inputs.select(provOptions, {
  label: "Provincia",
  format: d => d.nombre,
  value: provOptions.find(d => d.cp === "42") ?? provOptions[0],
});
const selectedProv = Generators.input(provInput);
```

${provInput}

```js
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
```

```js
const simEl = (() => {
  const p = convData[selectedProv.cp];
  if (!p) return document.createElement("div");

  const vc         = p.votos_candidaturas;
  const seats2023  = p.seats_total;
  const seatsDelta = SEATS_2026[selectedProv.cp] ?? 0;
  const seats2026  = seats2023 + seatsDelta;

  const THRESHOLD  = 0.01;
  const allParties = [...(p.partidos_con_escano ?? []), ...(p.partidos_sin_escano ?? [])];
  const shown      = allParties.filter(q => q.votos / vc >= THRESHOLD);
  const otrosVotos = allParties.filter(q => q.votos / vc < THRESHOLD).reduce((s, q) => s + q.votos, 0);

  const OTROS_ID  = "__otros__";
  const BLANCO_ID = "__blancos__";

  // Mutable entries array — can grow when user adds new parties
  const entries = [
    ...shown.map(q => ({
      id: q.siglas, label: q.siglas, denominacion: q.denominacion,
      bloque: q.bloque, escanos2023: q.escanos_dhondt ?? 0,
      isBlancos: false, isNuevo: false, isOtros: false,
      initPct: q.votos / vc * 100,
    })),
    ...(otrosVotos > 0 ? [{
      id: OTROS_ID, label: "Otros", denominacion: `Partidos con <1% (${allParties.filter(q => q.votos/vc < THRESHOLD).length} partidos)`,
      bloque: "otros", escanos2023: 0, isBlancos: false, isNuevo: false, isOtros: true,
      initPct: otrosVotos / vc * 100,
    }] : []),
    { id: BLANCO_ID, label: "En blanco", denominacion: "Excluidos del reparto D'Hondt · parten de 0% (la base son votos a candidaturas)",
      bloque: null, escanos2023: 0, isBlancos: true, isNuevo: false, isOtros: false,
      initPct: 0 },
  ];

  const pcts = entries.map(e => e.initPct);
  let nuevoCount = 0;

  function addParty() {
    nuevoCount++;
    entries.push({
      id: `__nuevo_${nuevoCount}__`, label: `Nuevo partido ${nuevoCount}`, denominacion: "",
      bloque: null, escanos2023: 0, isBlancos: false, isNuevo: true, isOtros: false,
      initPct: 0,
    });
    pcts.push(0);
    rebuildGrid();
    updateAll();
  }

  function removeParty(i) {
    entries.splice(i, 1);
    pcts.splice(i, 1);
    rebuildGrid();
    updateAll();
  }

  // D'Hondt: runs on proportions (invariant to scaling, so sum≠100% is fine)
  function runDhondt() {
    const cands = entries
      .map((e, i) => ({ e, i }))
      .filter(({ e }) => !e.isBlancos)
      .filter(({ i }) => pcts[i] > 0)
      .map(({ e, i }) => ({ id: e.id, votes: pcts[i] }));
    return dhondt(cands, seats2026);
  }

  // ── DOM scaffold ──────────────────────────────────────────────
  const wrap = document.createElement("div");
  wrap.style.cssText = "max-width:760px";

  // Info + seat change note
  const infoRow = document.createElement("div");
  infoRow.style.cssText = "margin:.3rem 0 .6rem;display:flex;align-items:center;gap:12px;flex-wrap:wrap";
  const infoSpan = document.createElement("span");
  infoSpan.style.cssText = "opacity:.6;font-size:.88em";
  infoSpan.textContent = `${p.nombre} · Jul 2023 → 2026 · ${vc.toLocaleString("es-ES")} votos`;
  infoRow.appendChild(infoSpan);
  if (seatsDelta !== 0) {
    const badge = document.createElement("span");
    badge.style.cssText = "font-size:.78em;background:#FFF3CD;border:1px solid #FFC107;border-radius:4px;padding:2px 8px;font-weight:600";
    badge.textContent = `⚠ Escaños 2026: ${seats2026} (${seatsDelta > 0 ? "+" : ""}${seatsDelta} por ajuste poblacional)`;
    infoRow.appendChild(badge);
  } else {
    const seatsSpan = document.createElement("span");
    seatsSpan.style.cssText = "opacity:.5;font-size:.88em";
    seatsSpan.textContent = `${seats2026} escaños`;
    infoRow.appendChild(seatsSpan);
  }
  wrap.appendChild(infoRow);

  // Seat bars
  const barWrap = document.createElement("div");
  barWrap.style.cssText = "display:flex;gap:12px;margin-bottom:1.2rem";
  wrap.appendChild(barWrap);

  // Total counter
  const totalEl = document.createElement("div");
  totalEl.style.cssText = "font-size:.85em;font-weight:600;padding:5px 10px;border-radius:5px;margin-bottom:.8rem;display:inline-block";
  wrap.appendChild(totalEl);

  // Grid container (rebuilt on addParty/removeParty)
  const gridWrap = document.createElement("div");
  wrap.appendChild(gridWrap);

  // Add party button
  const addBtn = document.createElement("button");
  addBtn.textContent = "+ Añadir partido";
  addBtn.style.cssText = "margin-top:.8rem;font-size:.8em;border:1px dashed #aaa;border-radius:5px;padding:5px 14px;cursor:pointer;background:transparent;opacity:.7";
  addBtn.addEventListener("click", addParty);
  wrap.appendChild(addBtn);

  // Reset all
  const resetAllBtn = document.createElement("button");
  resetAllBtn.textContent = "↺ Restablecer todo";
  resetAllBtn.style.cssText = "margin-top:.8rem;margin-left:10px;font-size:.8em;border:1px solid #ccc;border-radius:5px;padding:5px 14px;cursor:pointer;background:transparent;opacity:.7";
  resetAllBtn.addEventListener("click", () => {
    for (let i = 0; i < pcts.length; i++) pcts[i] = entries[i].initPct;
    rebuildGrid();
    updateAll();
  });
  wrap.appendChild(resetAllBtn);

  // ── Grid builder ──────────────────────────────────────────────
  function rebuildGrid() {
    gridWrap.innerHTML = "";
    const grid = document.createElement("div");
    grid.style.cssText = "display:grid;grid-template-columns:minmax(80px,170px) 64px 1fr 42px 42px 38px 24px;align-items:center;column-gap:8px;row-gap:5px";
    gridWrap.appendChild(grid);

    // Header
    for (const [txt, align] of [["Partido","left"],["% voto","right"],["Slider",""],["2023","center"],["2026 sim.","center"],["Δ","center"],["",""]]) {
      const h = document.createElement("div");
      h.style.cssText = `font-size:.72em;opacity:.4;font-weight:600;border-bottom:1px solid #e0e0e0;padding-bottom:3px;text-align:${align || "left"}`;
      h.textContent = txt;
      grid.appendChild(h);
    }

    entries.forEach((e, i) => {
      const col = e.bloque ? (COLORS[e.bloque] ?? "#999") : "#ccc";

      // Name
      const nameCell = document.createElement("div");
      nameCell.style.cssText = "display:flex;align-items:center;gap:5px;overflow:hidden";
      const dot = document.createElement("span");
      dot.style.cssText = `width:8px;height:8px;border-radius:50%;background:${col};flex-shrink:0`;
      nameCell.appendChild(dot);

      if (e.isNuevo) {
        const inp = document.createElement("input");
        inp.type = "text"; inp.value = e.label; inp.placeholder = "Nombre";
        inp.style.cssText = "font-size:.8em;font-weight:700;border:none;border-bottom:1px solid #ccc;background:transparent;width:100%;min-width:0;outline:none";
        inp.addEventListener("input", () => { e.label = inp.value; });
        nameCell.appendChild(inp);
      } else {
        const nm = document.createElement("span");
        nm.style.cssText = "font-size:.8em;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis";
        nm.textContent = e.label;
        nm.title = e.denominacion;
        nameCell.appendChild(nm);
      }
      grid.appendChild(nameCell);

      // % number
      const numInp = document.createElement("input");
      numInp.type = "number"; numInp.min = "0"; numInp.max = "100"; numInp.step = "0.1";
      numInp.value = pcts[i].toFixed(1);
      numInp.style.cssText = "width:100%;font-size:.8em;border:1px solid #e0e0e0;border-radius:3px;padding:2px 4px;text-align:right;box-sizing:border-box";
      const numCell = document.createElement("div");
      numCell.appendChild(numInp);
      grid.appendChild(numCell);

      // Slider
      const slider = document.createElement("input");
      slider.type = "range"; slider.min = "0"; slider.max = "100"; slider.step = "0.1";
      slider.value = pcts[i].toFixed(1);
      slider.style.cssText = `width:100%;accent-color:${e.isBlancos ? "#aaa" : col}`;
      const sliderCell = document.createElement("div");
      sliderCell.appendChild(slider);
      grid.appendChild(sliderCell);

      // 2023 seats
      const s23 = document.createElement("div");
      s23.style.cssText = "text-align:center;font-size:.8em;opacity:.45";
      s23.textContent = (e.isBlancos || e.isNuevo || e.isOtros) ? "—" : e.escanos2023;
      grid.appendChild(s23);

      // Sim seats
      const sSim = document.createElement("div");
      sSim.style.cssText = "text-align:center;font-size:.8em;font-weight:700";
      sSim.dataset.idx = i;
      sSim.className = "seats-sim";
      grid.appendChild(sSim);

      // Delta
      const dEl = document.createElement("div");
      dEl.style.cssText = "text-align:center;font-size:.8em;font-weight:700";
      dEl.dataset.idx = i;
      dEl.className = "seats-delta";
      grid.appendChild(dEl);

      // Reset / remove button
      const btn = document.createElement("button");
      btn.style.cssText = "font-size:.72em;border:none;background:transparent;cursor:pointer;opacity:.35;padding:1px 3px";
      if (e.isNuevo) {
        btn.textContent = "✕"; btn.title = "Eliminar partido";
        btn.addEventListener("click", () => removeParty(i));
      } else {
        btn.textContent = "↺"; btn.title = "Restablecer a 2023";
        btn.addEventListener("click", () => { pcts[i] = e.initPct; syncRow(i, slider, numInp); updateAll(); });
      }
      grid.appendChild(btn);

      // Wire events (free movement — no auto-redistribution)
      slider.addEventListener("input", () => { pcts[i] = +slider.value; numInp.value = pcts[i].toFixed(1); updateAll(); });
      numInp.addEventListener("change", () => { pcts[i] = Math.max(0, Math.min(100, +numInp.value)); slider.value = pcts[i].toFixed(1); updateAll(); });
    });
  }

  function syncRow(i, slider, numInp) {
    slider.value = pcts[i].toFixed(1);
    numInp.value = pcts[i].toFixed(1);
  }

  // ── Seat bar builder ──────────────────────────────────────────
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

  // ── Update (runs after every slider move) ─────────────────────
  function updateAll() {
    const sim = runDhondt();
    const total = pcts.reduce((s, v) => s + v, 0);
    const diff  = total - 100;
    const ok    = Math.abs(diff) < 0.1;

    // Total counter
    if (ok) {
      totalEl.textContent = "Total: 100% ✓";
      totalEl.style.background = "#E8F5E9"; totalEl.style.color = "#2E7D32";
    } else if (diff > 0) {
      totalEl.textContent = `Total: ${total.toFixed(1)}% — Exceso: ${diff.toFixed(1)}% a quitar`;
      totalEl.style.background = "#FFEBEE"; totalEl.style.color = "#C62828";
    } else {
      totalEl.textContent = `Total: ${total.toFixed(1)}% — Falta: ${(-diff).toFixed(1)}% por asignar`;
      totalEl.style.background = "#FFF8E1"; totalEl.style.color = "#E65100";
    }

    // Update sim/delta cells (found by class + data-idx)
    const simCells   = gridWrap.querySelectorAll(".seats-sim");
    const deltaCells = gridWrap.querySelectorAll(".seats-delta");

    entries.forEach((e, i) => {
      const simS  = e.isBlancos ? null : (sim[e.id] ?? 0);
      const hasReal = !e.isBlancos && !e.isNuevo && !e.isOtros;
      const real  = hasReal ? e.escanos2023 : null;

      if (simCells[i])   simCells[i].textContent = simS === null ? "—" : simS;

      if (deltaCells[i]) {
        if (simS === null) {
          deltaCells[i].textContent = "—"; deltaCells[i].style.color = "#aaa";
        } else if (real === null) {
          deltaCells[i].textContent = simS > 0 ? "+" + simS : "—";
          deltaCells[i].style.color = simS > 0 ? "#2E7D32" : "#aaa";
        } else {
          const d = simS - real;
          deltaCells[i].textContent = d === 0 ? "=" : (d > 0 ? "+" + d : String(d));
          deltaCells[i].style.color = d > 0 ? "#2E7D32" : d < 0 ? "#C62828" : "#888";
        }
      }
    });

    // Seat bars
    barWrap.innerHTML = "";
    const realByBlock = {};
    for (const [blq, n] of Object.entries(p.escanos_por_bloque ?? {})) if (n > 0) realByBlock[blq] = n;
    const simByBlock = {};
    for (const [id, n] of Object.entries(sim)) {
      const entry = entries.find(e => e.id === id);
      const blq   = entry?.bloque ?? "otros";
      simByBlock[blq] = (simByBlock[blq] ?? 0) + n;
    }
    barWrap.appendChild(buildSeatBar(`Real 2023 (${seats2023} esc)`, realByBlock, seats2023, 0.72));
    barWrap.appendChild(buildSeatBar(`Simulado 2026 (${seats2026} esc)`, simByBlock, seats2026, 0.92));
  }

  rebuildGrid();
  updateAll();
  return wrap;
})();
display(simEl);
```

---

> **Nota metodológica.** Base de partida: resultado oficial de Jul 2023 por circunscripción. "Otros" agrupa los partidos con menos del 1% de votos a candidaturas. Los votos en blanco se excluyen del cálculo D'Hondt. Los escaños de Cádiz y Madrid están actualizados al ajuste poblacional de 2026 (Cádiz −1, Madrid +1). La barrera legal del 3% no está modelada.
