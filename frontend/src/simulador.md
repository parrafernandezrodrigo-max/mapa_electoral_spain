---
title: Simulador de coaliciones
---

<div style="text-align:center;margin:1.5rem 0 1.5rem">
  <h1 style="font-size:2rem;font-weight:800;margin:0;line-height:1.1">¿Y si hubieran ido juntos?</h1>
  <p style="font-size:1.1rem;opacity:.65;margin:.4rem 0 0">Simulador de coaliciones electorales · 1977–2023</p>
</div>

<p style="max-width:700px;font-size:.9em;line-height:1.6;margin:0 0 1.2rem;opacity:.75">
  Selecciona una elección y asigna partidos a coaliciones (A, B, C…).
  La simulación recalcula el reparto D'Hondt en cada provincia con los votos combinados
  y muestra quién gana o pierde escaños respecto al resultado real.
</p>

```js
import * as d3 from "npm:d3";
const results     = await FileAttachment("data/summary_province.json").json();
const bloquesMeta = await FileAttachment("data/bloques_meta.json").json();
```

```js
const CONV_LABELS = {
  "197706": "Jun 1977","197903": "Mar 1979","198210": "Oct 1982","198606": "Jun 1986",
  "198910": "Oct 1989","199306": "Jun 1993","199603": "Mar 1996",
  "200003": "Mar 2000","200403": "Mar 2004","200803": "Mar 2008",
  "201111": "Nov 2011","201512": "Dic 2015","201606": "Jun 2016",
  "201904": "Abr 2019","201911": "Nov 2019","202307": "Jul 2023",
};
const convIds    = Object.keys(CONV_LABELS);
const bloqueOrder = [...Object.keys(bloquesMeta), "otros"];

const COAL_NAMES  = ["A", "B", "C", "D"];
const COAL_COLORS = { A: "#1565C0", B: "#B71C1C", C: "#2E7D32", D: "#E65100" };

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
const elecInput = Inputs.select(convIds, {
  label: "Elección",
  format: cid => CONV_LABELS[cid],
  value: "202307",
});
const elecId = Generators.input(elecInput);
```

${elecInput}

```js
// Parties appearing in the selected election (national aggregates)
const elecParties = (() => {
  const map = new Map();
  for (const prov of Object.values(results[elecId] ?? {})) {
    for (const p of prov.top5_partidos ?? []) {
      const bloque = p.bloque ?? "otros";
      const prev = map.get(p.siglas) ?? { siglas: p.siglas, bloque, votos: 0, escanos: 0 };
      map.set(p.siglas, {
        ...prev, bloque,
        votos:   prev.votos   + (p.votos ?? 0),
        escanos: prev.escanos + (p.escanos_dhondt ?? 0),
      });
    }
  }
  const list = [...map.values()].sort((a, b) => b.votos - a.votos);
  // Index by block
  const byBlock = new Map();
  for (const p of list) {
    if (!byBlock.has(p.bloque)) byBlock.set(p.bloque, []);
    byBlock.get(p.bloque).push(p);
  }
  return { list, byBlock };
})();
```

```js
// Coalition-assignment UI — rebuilds when election changes
const partyBuilderEl = (() => {
  const state = Object.fromEntries(elecParties.list.map(p => [p.siglas, "Solo"]));

  const wrap = document.createElement("div");
  wrap.style.cssText = "display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:.7rem;margin:.8rem 0 1.6rem";

  for (const bid of bloqueOrder) {
    const parties = elecParties.byBlock.get(bid) ?? [];
    if (!parties.length) continue;

    const m    = bloquesMeta[bid] ?? { label: "Otros", color: "#999" };
    const card = document.createElement("div");
    card.style.cssText = `border:2px solid ${m.color}55;border-radius:8px;overflow:hidden`;

    // Header
    const hdr = document.createElement("div");
    hdr.style.cssText = `background:${m.color}18;padding:7px 12px;border-bottom:2px solid ${m.color}44;display:flex;align-items:center;gap:7px`;
    hdr.innerHTML = `<span style="width:10px;height:10px;border-radius:50%;background:${m.color};display:inline-block;flex-shrink:0"></span><strong style="font-size:.87em">${m.label}</strong>`;
    card.appendChild(hdr);

    const body = document.createElement("div");
    body.style.cssText = "padding:5px 10px 8px;display:flex;flex-direction:column;gap:2px";

    for (const p of parties) {
      const row = document.createElement("div");
      row.style.cssText = "display:flex;align-items:center;gap:5px;padding:2px 0";

      // Party name
      const nm = document.createElement("span");
      nm.style.cssText = "font-weight:700;font-size:.82em;min-width:52px";
      nm.textContent = p.siglas;

      // Info
      const inf = document.createElement("span");
      inf.style.cssText = "flex:1;font-size:.72em;opacity:.42;white-space:nowrap;overflow:hidden;text-overflow:ellipsis";
      inf.textContent = `${(p.votos / 1e6).toFixed(1)}M · ${p.escanos} esc`;

      // Coalition pill buttons: · A B C D
      const pills = document.createElement("div");
      pills.style.cssText = "display:flex;gap:2px;flex-shrink:0";

      function refreshPills(active) {
        for (const btn of pills.querySelectorAll("button")) {
          const opt = btn.dataset.opt;
          const sel = opt === active;
          if (opt === "Solo") {
            btn.style.cssText = `font-size:.72em;font-weight:700;width:18px;height:18px;border-radius:3px;cursor:pointer;border:1px solid ${sel?"#aaa":"#e0e0e0"};background:${sel?"#ddd":"transparent"};color:${sel?"#444":"#bbb"}`;
          } else {
            btn.style.cssText = `font-size:.72em;font-weight:700;width:18px;height:18px;border-radius:3px;cursor:pointer;border:1px solid ${sel?COAL_COLORS[opt]:"#e0e0e0"};background:${sel?COAL_COLORS[opt]:"transparent"};color:${sel?"#fff":"#bbb"}`;
          }
        }
      }

      for (const [label, realOpt] of [["·", "Solo"], ...COAL_NAMES.map(c => [c, c])]) {
        const btn = document.createElement("button");
        btn.textContent = label;
        btn.dataset.opt = realOpt;
        btn.title = realOpt === "Solo" ? "Compite solo (histórico)" : `Añadir a Coalición ${realOpt}`;
        btn.addEventListener("click", () => {
          state[p.siglas] = realOpt;
          refreshPills(realOpt);
          wrap.value = { ...state };
          wrap.dispatchEvent(new CustomEvent("input"));
        });
        pills.appendChild(btn);
      }
      refreshPills("Solo");

      row.appendChild(nm);
      row.appendChild(inf);
      row.appendChild(pills);
      body.appendChild(row);
    }

    card.appendChild(body);
    wrap.appendChild(card);
  }

  wrap.value = { ...state };
  return wrap;
})();

const coalConfig = Generators.input(partyBuilderEl);
display(partyBuilderEl);
```

```js
// Compute simulation for the selected election + current coalition config
const simResults = (() => {
  const partyBloque = Object.fromEntries(elecParties.list.map(p => [p.siglas, p.bloque]));

  // Which coalitions are active (2+ members)
  const coalMembers = {};
  for (const [sig, coal] of Object.entries(coalConfig)) {
    if (coal !== "Solo") {
      if (!coalMembers[coal]) coalMembers[coal] = [];
      coalMembers[coal].push(sig);
    }
  }
  const activeCoals = Object.fromEntries(Object.entries(coalMembers).filter(([, m]) => m.length >= 2));

  // candId(sig) → the candidate this party votes for in the simulation
  function candId(sig) {
    const coal = coalConfig[sig] ?? "Solo";
    return (coal !== "Solo" && activeCoals[coal]) ? `coal:${coal}` : sig;
  }

  // Real seats per block (national)
  const realByBlock = {};
  for (const prov of Object.values(results[elecId] ?? {})) {
    for (const [b, n] of Object.entries(prov.escanos_por_bloque ?? {})) {
      if (n > 0) realByBlock[b] = (realByBlock[b] ?? 0) + n;
    }
  }

  // Real seats per party (national, from top5 — used for coalition real-total comparison)
  const realByParty = {};
  for (const prov of Object.values(results[elecId] ?? {})) {
    for (const p of prov.top5_partidos ?? []) {
      realByParty[p.siglas] = (realByParty[p.siglas] ?? 0) + (p.escanos_dhondt ?? 0);
    }
  }

  // Baseline simulation: all parties competing solo (top5 only, no coalitions)
  // Used as reference so the top5-truncation bias cancels out in deltas
  const simByCandSolo = {};
  for (const prov of Object.values(results[elecId] ?? {})) {
    const voteMap = {};
    for (const p of prov.top5_partidos ?? []) voteMap[p.siglas] = (p.votos ?? 0);
    const won = dhondt(Object.entries(voteMap).map(([id, votes]) => ({ id, votes })), prov.seats_total ?? 0);
    for (const [id, n] of Object.entries(won)) simByCandSolo[id] = (simByCandSolo[id] ?? 0) + n;
  }

  // Simulate per province with coalition merges
  const simByCand = {}; // candId -> seats nationally
  for (const prov of Object.values(results[elecId] ?? {})) {
    const voteMap = {};
    for (const p of prov.top5_partidos ?? []) {
      const cid = candId(p.siglas);
      voteMap[cid] = (voteMap[cid] ?? 0) + (p.votos ?? 0);
    }
    const won = dhondt(Object.entries(voteMap).map(([id, votes]) => ({ id, votes })), prov.seats_total ?? 0);
    for (const [id, n] of Object.entries(won)) simByCand[id] = (simByCand[id] ?? 0) + n;
  }

  // Map sim seats → block (for chart bar coloring)
  const simByBlockOrCoal = {};
  for (const [cid, n] of Object.entries(simByCand)) {
    const key = cid.startsWith("coal:") ? cid : `block:${partyBloque[cid] ?? "otros"}`;
    simByBlockOrCoal[key] = (simByBlockOrCoal[key] ?? 0) + n;
  }

  // Coalition summary: for each active coalition + solo parties with seats
  // Deltas compare coalition-sim vs solo-sim to cancel top5-truncation bias
  const coalSummary = [];

  for (const [letter, members] of Object.entries(activeCoals).sort()) {
    const baseTotal = members.reduce((s, sig) => s + (simByCandSolo[sig] ?? 0), 0);
    const simTotal  = simByCand[`coal:${letter}`] ?? 0;
    coalSummary.push({
      type: "coal", letter,
      label: `Coalición ${letter}`,
      members,
      realTotal: baseTotal, simTotal,
      delta: simTotal - baseTotal,
    });
  }

  // Solo parties (that won at least 1 seat in baseline or coalition sim)
  for (const p of elecParties.list) {
    const coal = coalConfig[p.siglas] ?? "Solo";
    if (coal !== "Solo" && activeCoals[coal]) continue; // in an active coalition
    const baseS = simByCandSolo[p.siglas] ?? 0;
    const simS  = simByCand[p.siglas] ?? 0;
    if (baseS > 0 || simS > 0) {
      coalSummary.push({
        type: "solo",
        label: p.siglas,
        bloque: p.bloque,
        members: [p.siglas],
        realTotal: baseS, simTotal: simS,
        delta: simS - baseS,
      });
    }
  }

  return { realByBlock, realByParty, simByCandSolo, simByCand, simByBlockOrCoal, activeCoals, coalSummary };
})();
```

```js
// Comparison chart: Real bar + Simulated bar
const chartEl = (() => {
  const { realByBlock, simByBlockOrCoal, activeCoals } = simResults;
  const W = 760, barH = 36, gap = 10;
  const mL = 92, mR = 18, mT = 32, mB = 24;
  const iW = W - mL - mR;
  const xScale = d3.scaleLinear().domain([0, 350]).range([0, iW]);
  const H = 2 * barH + gap + mT + mB;

  const svg = d3.create("svg")
    .attr("viewBox", `0 0 ${W} ${H}`)
    .style("width", "100%").style("display", "block").style("overflow", "visible");

  const g = svg.append("g").attr("transform", `translate(${mL},${mT})`);

  // X axis
  g.append("g")
    .attr("transform", `translate(0,${2*barH+gap+4})`)
    .call(d3.axisBottom(xScale).ticks(7).tickFormat(d => d))
    .call(g => g.select(".domain").remove())
    .call(g => g.selectAll("line").attr("stroke","#e8e8e8"))
    .call(g => g.selectAll("text").attr("font-size","9.5px").attr("fill","#888"));

  // Majority line
  const majX = xScale(176);
  g.append("line")
    .attr("x1",majX).attr("y1",-22).attr("x2",majX).attr("y2",2*barH+gap+8)
    .attr("stroke","#333").attr("stroke-width",1.1).attr("stroke-dasharray","5,3").attr("opacity",.5);
  g.append("text")
    .attr("x",majX).attr("y",-24).attr("text-anchor","middle").attr("font-size","9px").attr("fill","#444")
    .text("176 (mayoría)");

  const tip = d3.select(document.body).append("div")
    .style("position","fixed").style("display","none")
    .style("background","var(--theme-background-alt,#fff)").style("border","1px solid #ddd")
    .style("border-radius","6px").style("padding","6px 11px").style("font-size",".8em")
    .style("pointer-events","none").style("box-shadow","0 4px 12px rgba(0,0,0,.12)").style("z-index","200");

  // ── REAL bar ──
  g.append("text").attr("x",-6).attr("y",barH/2).attr("text-anchor","end")
    .attr("dominant-baseline","middle").attr("font-size","11px").attr("font-weight","600").attr("fill","#555")
    .text("Real");

  const realSegs = Object.entries(realByBlock)
    .filter(([,n]) => n > 0)
    .sort((a,b) => bloqueOrder.indexOf(a[0]) - bloqueOrder.indexOf(b[0]));
  let rx = 0;
  for (const [bid, n] of realSegs) {
    const w   = xScale(n);
    const col = bloquesMeta[bid]?.color ?? "#999";
    const lbl = bloquesMeta[bid]?.label ?? bid;
    g.append("rect")
      .attr("x",rx).attr("y",0).attr("width",w).attr("height",barH)
      .attr("fill",col).attr("opacity",.82)
      .on("mouseover",(evt)=>tip.html(`<b>${lbl}</b> · Real: <b>${n}</b> esc`).style("display","block"))
      .on("mousemove",(evt)=>tip.style("left",(evt.clientX+14)+"px").style("top",(evt.clientY-10)+"px"))
      .on("mouseleave",()=>tip.style("display","none"));
    if (w > 18)
      g.append("text").attr("x",rx+w/2).attr("y",barH/2).attr("text-anchor","middle")
        .attr("dominant-baseline","middle").attr("font-size","9px").attr("fill","#fff").attr("font-weight","700")
        .style("pointer-events","none").text(n);
    rx += w;
  }

  // ── SIMULATED bar ──
  const hasCoals = Object.keys(activeCoals).length > 0;
  g.append("text").attr("x",-6).attr("y",barH+gap+barH/2).attr("text-anchor","end")
    .attr("dominant-baseline","middle").attr("font-size","11px").attr("font-weight","600")
    .attr("fill", hasCoals ? "#333" : "#aaa")
    .text("Simulación");

  if (!hasCoals) {
    g.append("text").attr("x",iW/2).attr("y",barH+gap+barH/2).attr("text-anchor","middle")
      .attr("dominant-baseline","middle").attr("font-size","11px").attr("fill","#bbb")
      .text("Asigna 2+ partidos a una coalición para ver el resultado simulado");
  } else {
    // Ordered: coalitions first (A→B→C→D), then solo blocks
    const simSegs = Object.entries(simByBlockOrCoal)
      .filter(([,n]) => n > 0)
      .sort((a,b) => {
        const aC = a[0].startsWith("coal:"), bC = b[0].startsWith("coal:");
        if (aC && bC) return a[0].slice(5).localeCompare(b[0].slice(5));
        if (aC) return -1; if (bC) return 1;
        return bloqueOrder.indexOf(a[0].slice(6)) - bloqueOrder.indexOf(b[0].slice(6));
      });
    let sx = 0;
    for (const [id, n] of simSegs) {
      const w = xScale(n);
      let col, lbl;
      if (id.startsWith("coal:")) {
        const letter  = id.slice(5);
        col  = COAL_COLORS[letter];
        lbl  = `Coalición ${letter} (${(activeCoals[letter]??[]).join(" + ")})`;
      } else {
        const bid = id.slice(6);
        col  = bloquesMeta[bid]?.color ?? "#999";
        lbl  = bloquesMeta[bid]?.label ?? bid;
      }
      g.append("rect")
        .attr("x",sx).attr("y",barH+gap).attr("width",w).attr("height",barH)
        .attr("fill",col).attr("opacity",.92)
        .on("mouseover",(evt)=>tip.html(`<b>${lbl}</b><br>Simulado: <b>${n}</b> esc`).style("display","block"))
        .on("mousemove",(evt)=>tip.style("left",(evt.clientX+14)+"px").style("top",(evt.clientY-10)+"px"))
        .on("mouseleave",()=>tip.style("display","none"));
      if (w > 18)
        g.append("text").attr("x",sx+w/2).attr("y",barH+gap+barH/2).attr("text-anchor","middle")
          .attr("dominant-baseline","middle").attr("font-size","9px").attr("fill","#fff").attr("font-weight","700")
          .style("pointer-events","none").text(n);
      sx += w;
    }
  }

  return svg.node();
})();
display(chartEl);
```

```js
// Coalition + party gain/loss table
const summaryEl = (() => {
  const { coalSummary, activeCoals } = simResults;
  if (Object.keys(activeCoals).length === 0) return null;

  const rows = coalSummary.map(entry => ({
    "Grupo":            entry.type === "coal"
                          ? `Coalición ${entry.letter}`
                          : `${entry.label} (${bloquesMeta[entry.bloque]?.label ?? entry.bloque ?? "solo"})`,
    "Partidos":         entry.members.join(" + "),
    "Esc. sin coalición": entry.realTotal,
    "Esc. simulados":   entry.simTotal,
    "Diferencia":       entry.delta,
  }));

  return Inputs.table(rows, {
    columns: ["Grupo","Partidos","Esc. sin coalición","Esc. simulados","Diferencia"],
    rows: 20,
    sort: "Diferencia",
    reverse: true,
    format: {
      "Diferencia": d => (d > 0 ? "+" : "") + d,
    },
  });
})();
if (summaryEl) display(summaryEl);
```

---

## Detalle por provincia

```js
const provinceEl = (() => {
  const { realByParty, simByCand, activeCoals } = simResults;
  if (Object.keys(activeCoals).length === 0) {
    const note = document.createElement("p");
    note.style.cssText = "opacity:.5;font-size:.9em";
    note.textContent = "Asigna partidos a coaliciones para ver el detalle provincial.";
    return note;
  }

  const partyBloque = Object.fromEntries(elecParties.list.map(p => [p.siglas, p.bloque]));

  function candId(sig) {
    const coal = coalConfig[sig] ?? "Solo";
    return (coal !== "Solo" && activeCoals[coal]) ? `coal:${coal}` : sig;
  }

  const rows = Object.entries(results[elecId] ?? {}).map(([cp, prov]) => {
    // Baseline simulation (all solo, top5 only) — reference to cancel top5-truncation bias
    const soloVoteMap = {};
    for (const p of prov.top5_partidos ?? []) soloVoteMap[p.siglas] = (p.votos ?? 0);
    const soloProv = dhondt(Object.entries(soloVoteMap).map(([id, v]) => ({id, votes: v})), prov.seats_total ?? 0);

    // Map solo seats to coalition candidate ids (for fair comparison)
    const realByCandProv = {};
    for (const p of prov.top5_partidos ?? []) {
      const cid = candId(p.siglas);
      realByCandProv[cid] = (realByCandProv[cid] ?? 0) + (soloProv[p.siglas] ?? 0);
    }

    // Simulate this province with coalitions
    const voteMap = {};
    for (const p of prov.top5_partidos ?? []) {
      const cid = candId(p.siglas);
      voteMap[cid] = (voteMap[cid] ?? 0) + (p.votos ?? 0);
    }
    const simProv = dhondt(Object.entries(voteMap).map(([id, v]) => ({id, votes: v})), prov.seats_total ?? 0);

    // Seats change (sum of abs deltas)
    const allCands = new Set([...Object.keys(realByCandProv), ...Object.keys(simProv)]);
    let totalChange = 0;
    const lines = [];
    for (const cid of allCands) {
      const r = realByCandProv[cid] ?? 0;
      const s = simProv[cid] ?? 0;
      const d = s - r;
      if (d !== 0) {
        totalChange += Math.abs(d);
        const lbl = cid.startsWith("coal:")
          ? `Coal. ${cid.slice(5)}`
          : (bloquesMeta[partyBloque[cid]]?.label ?? cid);
        lines.push(`${d > 0 ? "+" : ""}${d} ${lbl}`);
      }
    }

    return {
      "Provincia":    prov.nombre,
      "Escaños":      prov.seats_total,
      "Esc. cambian": totalChange,
      "Cambios":      lines.join(" · ") || "Sin cambio",
    };
  });

  return Inputs.table(rows, {
    columns: ["Provincia","Escaños","Esc. cambian","Cambios"],
    rows: 52,
    sort: "Esc. cambian",
    reverse: true,
  });
})();
display(provinceEl);
```

---

> **Nota metodológica.** La simulación usa los votos de los 5 partidos más votados por circunscripción y elección. Partidos fuera de ese top 5 no se modelan. La columna "Esc. sin coalición" y las diferencias muestran el efecto puro de unir partidos: comparan la simulación con coalición frente a la misma simulación sin ella (ambas con el mismo motor D'Hondt y los mismos datos), eliminando así el sesgo de truncar al top 5. La barra "Real" del gráfico refleja el resultado oficial completo.
