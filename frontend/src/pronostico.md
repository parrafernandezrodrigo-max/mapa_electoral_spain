---
title: Simulador electoral 2026
---

<div style="text-align:center;margin:1.5rem 0 1.5rem">
  <h1 style="font-size:2rem;font-weight:800;margin:0;line-height:1.1">Simulador electoral 2026</h1>
  <p style="font-size:1.1rem;opacity:.65;margin:.4rem 0 0">¿Cómo afectaría un cambio en el voto a los escaños? · Por provincia</p>
</div>

<p style="max-width:700px;font-size:.9em;line-height:1.6;margin:0 0 1.4rem;opacity:.75">
  Los sliders parten del resultado real de Jul 2023. Muévelos para ver cómo cambia el reparto
  D'Hondt en la provincia. La suma siempre es 100%: al subir un partido, el resto baja
  proporcionalmente. Los votos en blanco se excluyen del reparto D'Hondt.
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

  const vc    = p.votos_candidaturas;
  const seats = p.seats_total;

  // ── Build party list ──────────────────────────────────────────
  const THRESHOLD  = 0.01; // 1 %
  const allParties = [...(p.partidos_con_escano ?? []), ...(p.partidos_sin_escano ?? [])];
  const shown      = allParties.filter(q => q.votos / vc >= THRESHOLD);
  const otrosVotos = allParties.filter(q => q.votos / vc < THRESHOLD).reduce((s, q) => s + q.votos, 0);

  const OTROS_ID  = "__otros__";
  const BLANCO_ID = "__blancos__";
  const NUEVO_ID  = "__nuevo__";

  const entries = [
    ...shown.map(q => ({
      id: q.siglas, label: q.siglas, denominacion: q.denominacion,
      bloque: q.bloque, escanos2023: q.escanos_dhondt ?? 0,
      isBlancos: false, isNuevo: false,
      initPct: q.votos / vc * 100,
    })),
    ...(otrosVotos > 0 ? [{
      id: OTROS_ID, label: "Otros", denominacion: "Partidos menores (agregado)",
      bloque: "otros", escanos2023: 0, isBlancos: false, isNuevo: false,
      initPct: otrosVotos / vc * 100,
    }] : []),
    { id: BLANCO_ID, label: "En blanco", denominacion: "Votos en blanco (excluidos de D'Hondt)",
      bloque: null, escanos2023: 0, isBlancos: true, isNuevo: false, initPct: 0 },
    { id: NUEVO_ID, label: "Nuevo partido", denominacion: "",
      bloque: null, escanos2023: 0, isBlancos: false, isNuevo: true, initPct: 0 },
  ];

  // ── Mutable state ─────────────────────────────────────────────
  const pcts = entries.map(e => e.initPct);
  let nuevoLabel = "Nuevo partido";
  let nuevoBloque = null;

  function adjustOthers(changedIdx, rawVal) {
    const newVal = Math.max(0, Math.min(100, rawVal));
    const otherIdxs = pcts.map((_, j) => j).filter(j => j !== changedIdx);
    const othersSum = otherIdxs.reduce((s, j) => s + pcts[j], 0);
    const needed    = 100 - newVal;
    pcts[changedIdx] = newVal;
    if (othersSum > 0.001) {
      const scale = needed / othersSum;
      for (const j of otherIdxs) pcts[j] = Math.max(0, pcts[j] * scale);
    } else if (needed > 0) {
      for (const j of otherIdxs) pcts[j] = needed / otherIdxs.length;
    }
    // float precision fix
    const total = pcts.reduce((s, v) => s + v, 0);
    if (Math.abs(total - 100) > 0.01)
      for (let j = 0; j < pcts.length; j++) pcts[j] = pcts[j] * 100 / total;
  }

  function runDhondt() {
    const cands = entries
      .map((e, i) => ({ e, i }))
      .filter(({ e }) => !e.isBlancos)
      .filter(({ i }) => pcts[i] > 0)
      .map(({ e, i }) => ({ id: e.id, votes: pcts[i] }));
    return dhondt(cands, seats);
  }

  // ── DOM setup ─────────────────────────────────────────────────
  const wrap = document.createElement("div");
  wrap.style.cssText = "max-width:740px";

  // Province info + reset all
  const header = document.createElement("div");
  header.style.cssText = "display:flex;align-items:center;justify-content:space-between;margin:.3rem 0 1rem";
  const infoSpan = document.createElement("span");
  infoSpan.style.cssText = "opacity:.6;font-size:.88em";
  infoSpan.textContent = `${p.nombre} · Jul 2023 → 2026 · ${seats} escaños · ${vc.toLocaleString("es-ES")} votos`;
  const resetAllBtn = document.createElement("button");
  resetAllBtn.textContent = "↺ Restablecer todo";
  resetAllBtn.style.cssText = "font-size:.78em;border:1px solid #ccc;border-radius:4px;padding:3px 10px;cursor:pointer;background:transparent;opacity:.7";
  header.appendChild(infoSpan);
  header.appendChild(resetAllBtn);
  wrap.appendChild(header);

  // Seat bars
  const barWrap = document.createElement("div");
  barWrap.style.cssText = "display:flex;gap:12px;margin-bottom:1.2rem";
  wrap.appendChild(barWrap);

  // Grid: party rows
  const grid = document.createElement("div");
  grid.style.cssText = "display:grid;grid-template-columns:minmax(80px,160px) 62px 1fr 40px 40px 36px 24px;align-items:center;column-gap:8px;row-gap:4px";
  wrap.appendChild(grid);

  // Grid header
  for (const [txt, align] of [["Partido","left"],["% voto","right"],["Slider",""],["2023","center"],["Sim.","center"],["Δ","center"],["",""]]) {
    const h = document.createElement("div");
    h.style.cssText = `font-size:.72em;opacity:.45;font-weight:600;border-bottom:1px solid #e0e0e0;padding-bottom:3px;text-align:${align}`;
    h.textContent = txt;
    grid.appendChild(h);
  }

  // Total & results
  const totalEl   = document.createElement("div");
  totalEl.style.cssText = "margin:.6rem 0 1.2rem;font-size:.82em;font-weight:600";
  wrap.appendChild(totalEl);

  const resultsEl = document.createElement("div");
  wrap.appendChild(resultsEl);

  // ── Build rows ────────────────────────────────────────────────
  const sliderEls  = [];
  const numEls     = [];
  const seatsSimEls = [];
  const deltaEls   = [];

  entries.forEach((e, i) => {
    const col = e.bloque ? (COLORS[e.bloque] ?? "#999") : "#bbb";

    // Name cell
    const nameCell = document.createElement("div");
    nameCell.style.cssText = "display:flex;align-items:center;gap:5px;overflow:hidden";
    const dot = document.createElement("span");
    dot.style.cssText = `width:8px;height:8px;border-radius:50%;background:${col};flex-shrink:0`;
    nameCell.appendChild(dot);

    if (e.isNuevo) {
      const inp = document.createElement("input");
      inp.type = "text"; inp.value = nuevoLabel;
      inp.placeholder = "Nombre";
      inp.style.cssText = "font-size:.8em;font-weight:700;border:none;border-bottom:1px solid #ccc;background:transparent;width:100%;outline:none;min-width:0";
      inp.addEventListener("input", () => { nuevoLabel = inp.value; });
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
    numEls.push(numInp);

    // Slider
    const slider = document.createElement("input");
    slider.type = "range"; slider.min = "0"; slider.max = "100"; slider.step = "0.1";
    slider.value = pcts[i].toFixed(1);
    slider.style.cssText = `width:100%;accent-color:${e.isBlancos ? "#aaa" : col}`;
    const sliderCell = document.createElement("div");
    sliderCell.appendChild(slider);
    grid.appendChild(sliderCell);
    sliderEls.push(slider);

    // 2023 seats
    const s23 = document.createElement("div");
    s23.style.cssText = "text-align:center;font-size:.8em;opacity:.45";
    s23.textContent = (e.isBlancos || e.isNuevo || e.id === OTROS_ID) ? "—" : e.escanos2023;
    grid.appendChild(s23);

    // Sim seats
    const sSim = document.createElement("div");
    sSim.style.cssText = "text-align:center;font-size:.8em;font-weight:700";
    grid.appendChild(sSim);
    seatsSimEls.push(sSim);

    // Delta
    const dEl = document.createElement("div");
    dEl.style.cssText = "text-align:center;font-size:.8em;font-weight:700";
    grid.appendChild(dEl);
    deltaEls.push(dEl);

    // Reset / clear button
    const btn = document.createElement("button");
    btn.textContent = e.isNuevo ? "✕" : "↺";
    btn.title = e.isNuevo ? "Poner a 0" : "Restablecer a 2023";
    btn.style.cssText = "font-size:.72em;border:none;background:transparent;cursor:pointer;opacity:.35;padding:1px 3px";
    btn.addEventListener("click", () => { adjustOthers(i, e.initPct); updateAll(); });
    grid.appendChild(btn);

    // Wire events
    slider.addEventListener("input", () => { adjustOthers(i, +slider.value); updateAll(); });
    numInp.addEventListener("change", () => { adjustOthers(i, +numInp.value); updateAll(); });
  });

  // Reset all
  resetAllBtn.addEventListener("click", () => {
    for (let i = 0; i < pcts.length; i++) pcts[i] = entries[i].initPct;
    updateAll();
  });

  // ── Update function ───────────────────────────────────────────
  function buildSeatBar(label, escByBlock, opacity) {
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
      const segCol = COLORS[blq] ?? "#999";
      seg.style.cssText = `flex:${n};background:${segCol};opacity:${opacity};display:flex;align-items:center;justify-content:center`;
      if (n / seats > 0.06) {
        const t = document.createElement("span");
        t.style.cssText = "font-size:9px;color:#fff;font-weight:700;pointer-events:none";
        t.textContent = n;
        seg.appendChild(t);
      }
      seg.title = `${bloquesMeta[blq]?.label ?? blq}: ${n} esc`;
      bar.appendChild(seg);
    }
    // remainder (unplaced) → grey
    if (placed < seats) {
      const rem = document.createElement("div");
      rem.style.cssText = `flex:${seats - placed};background:#ddd`;
      bar.appendChild(rem);
    }
    cont.appendChild(bar);
    return cont;
  }

  function updateAll() {
    const sim = runDhondt();

    // Update sliders and numbers
    entries.forEach((e, i) => {
      sliderEls[i].value = pcts[i].toFixed(2);
      numEls[i].value    = pcts[i].toFixed(1);

      const hasReal = !e.isBlancos && !e.isNuevo && e.id !== OTROS_ID;
      const simS = e.isBlancos ? null : (sim[e.id] ?? 0);
      const real = hasReal ? e.escanos2023 : null;

      seatsSimEls[i].textContent = simS === null ? "—" : simS;

      if (simS === null) {
        deltaEls[i].textContent = "—"; deltaEls[i].style.color = "#aaa";
      } else if (real === null) {
        // nuevo or otros: just show sim
        deltaEls[i].textContent = simS > 0 ? "+" + simS : "—";
        deltaEls[i].style.color = simS > 0 ? "#2E7D32" : "#aaa";
      } else {
        const d = simS - real;
        deltaEls[i].textContent = d === 0 ? "=" : (d > 0 ? "+" + d : String(d));
        deltaEls[i].style.color = d > 0 ? "#2E7D32" : d < 0 ? "#C62828" : "#888";
      }
    });

    // Total
    const total = pcts.reduce((s, v) => s + v, 0);
    const ok = Math.abs(total - 100) < 0.1;
    totalEl.textContent = `Total: ${total.toFixed(1)}% ${ok ? "✓" : "⚠ no suma 100%"}`;
    totalEl.style.color = ok ? "#2E7D32" : "#C62828";

    // Seat bars
    barWrap.innerHTML = "";

    const realByBlock = {};
    for (const [blq, n] of Object.entries(p.escanos_por_bloque ?? {})) if (n > 0) realByBlock[blq] = n;

    const simByBlock = {};
    for (const [id, n] of Object.entries(sim)) {
      const entry = entries.find(e => e.id === id);
      const blq = entry?.bloque ?? "otros";
      simByBlock[blq] = (simByBlock[blq] ?? 0) + n;
    }

    barWrap.appendChild(buildSeatBar("Real 2023", realByBlock, 0.75));
    barWrap.appendChild(buildSeatBar("Simulado 2026", simByBlock, 0.92));
  }

  updateAll();
  return wrap;
})();
display(simEl);
```

---

> **Nota.** Los datos de partida son el resultado oficial de Jul 2023 por circunscripción. Los partidos con menos del 1% se agrupan en "Otros". Los votos en blanco se contabilizan en la suma pero no participan en el reparto D'Hondt. La barrera legal del 3% no está modelada: cualquier partido con votos compite en el reparto.
