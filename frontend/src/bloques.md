---
title: Bloques ideológicos
---

<div style="text-align:center;margin:1.5rem 0 1.5rem">
  <h1 style="font-size:2rem;font-weight:800;margin:0;line-height:1.1">Bloques ideológicos</h1>
  <p style="font-size:1.1rem;opacity:.65;margin:.4rem 0 0">Clasificación de partidos utilizada en el mapa · 1977–2023</p>
</div>

```js
import * as d3 from "npm:d3";
const results     = await FileAttachment("data/summary_province.json").json();
const bloquesMeta = await FileAttachment("data/bloques_meta.json").json();
```

```js
// Agregar partidos por bloque sumando votos y escaños de todos los top5
const byBloque = new Map();
for (const [, convData] of Object.entries(results)) {
  for (const [, prov] of Object.entries(convData)) {
    for (const partido of prov.top5_partidos ?? []) {
      const bloque = partido.bloque ?? "otros";
      if (!byBloque.has(bloque)) byBloque.set(bloque, new Map());
      const mapa = byBloque.get(bloque);
      const prev = mapa.get(partido.siglas) ?? { votos: 0, escanos: 0, apariciones: 0 };
      mapa.set(partido.siglas, {
        votos:      prev.votos      + partido.votos,
        escanos:    prev.escanos    + partido.escanos_dhondt,
        apariciones: prev.apariciones + 1,
      });
    }
  }
}

// Orden de bloques + "otros" al final
const bloqueOrder = [...Object.keys(bloquesMeta), "otros"];
const bloquesList = bloqueOrder.map(id => {
  const partidos = [...(byBloque.get(id)?.entries() ?? [])]
    .map(([siglas, d]) => ({ siglas, ...d }))
    .sort((a, b) => b.votos - a.votos);
  const totalVotos  = partidos.reduce((s, p) => s + p.votos, 0);
  const totalEscanos = partidos.reduce((s, p) => s + p.escanos, 0);
  return {
    id,
    label:   bloquesMeta[id]?.label ?? "Otros",
    color:   bloquesMeta[id]?.color ?? "#999",
    desc:    bloquesMeta[id]?.desc  ?? "",
    partidos,
    totalVotos,
    totalEscanos,
  };
});

// Total de votos para calcular share relativo dentro de cada bloque
const totalVotos = bloquesList.reduce(
  (acc, b) => acc + b.partidos.reduce((s, p) => s + p.votos, 0), 0
);
```

```js
const CONV_LABELS = {
  "197706": "1977", "197903": "1979", "198210": "1982", "198606": "1986",
  "198910": "1989", "199306": "1993", "199603": "1996",
  "200003": "2000", "200403": "2004", "200803": "2008",
  "201111": "2011", "201512": "2015", "201606": "2016",
  "201904": "2019a","201911": "2019b","202307": "2023",
};
const convIds     = Object.keys(CONV_LABELS);
const bloqueOrder = [...Object.keys(bloquesMeta), "otros"];
const COLORS      = { ...Object.fromEntries(Object.entries(bloquesMeta).map(([k,v]) => [k, v.color])), otros: "#999" };

// Escaños por bloque por elección
const seatsByElec = convIds.map(cid => {
  const row = { convId: cid, label: CONV_LABELS[cid] };
  for (const blq of bloqueOrder) row[blq] = 0;
  for (const [, provData] of Object.entries(results[cid] ?? {})) {
    for (const [blq, n] of Object.entries(provData.escanos_por_bloque ?? {})) {
      if (blq in row) row[blq] += n;
    }
  }
  row._total = bloqueOrder.reduce((s, b) => s + (row[b] ?? 0), 0);
  return row;
});
```

```js
const evolucionBloquesEl = (() => {
  const W = 860, H = 300;
  const margin = { top: 16, right: 140, bottom: 36, left: 44 };
  const iW = W - margin.left - margin.right;
  const iH = H - margin.top - margin.bottom;

  const bloquesActivos = bloqueOrder.filter(b => seatsByElec.some(r => r[b] > 0));

  const stack  = d3.stack().keys(bloquesActivos).order(d3.stackOrderNone).offset(d3.stackOffsetNone);
  const stacked = stack(seatsByElec);

  const xScale = d3.scaleBand().domain(seatsByElec.map(d => d.label)).range([0, iW]).padding(0.18);
  const yMax   = d3.max(seatsByElec, d => d._total) ?? 350;
  const yScale = d3.scaleLinear().domain([0, yMax]).range([iH, 0]).nice();

  const svg = d3.create("svg")
    .attr("viewBox", "0 0 " + W + " " + H)
    .style("width", "100%").style("display", "block");

  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  // Grid
  g.append("g")
    .call(d3.axisLeft(yScale).tickSize(-iW).tickFormat(""))
    .call(g => g.select(".domain").remove())
    .call(g => g.selectAll("line").attr("stroke", "#ebebeb").attr("stroke-dasharray", "2,2"));

  // Mayoría absoluta
  const maj = Math.round(yMax / 2);
  if (maj > 0) {
    g.append("line")
      .attr("x1", 0).attr("y1", yScale(maj)).attr("x2", iW).attr("y2", yScale(maj))
      .attr("stroke", "#555").attr("stroke-width", 1.2).attr("stroke-dasharray", "5,3");
    g.append("text")
      .attr("x", iW + 4).attr("y", yScale(maj) + 4)
      .attr("font-size", "9px").attr("fill", "#555").attr("font-weight", "600")
      .text("m.a.");
  }

  // Barras apiladas
  const tooltip = d3.select(document.body).append("div")
    .style("position", "fixed").style("display", "none")
    .style("background", "var(--theme-background-alt,#fff)")
    .style("border", "1px solid #ddd").style("border-radius", "6px")
    .style("padding", "9px 13px").style("font-size", ".8em")
    .style("pointer-events", "none").style("box-shadow", "0 4px 14px rgba(0,0,0,.13)")
    .style("z-index", "9999").style("min-width", "170px");

  g.selectAll("g.layer")
    .data(stacked)
    .join("g")
      .attr("class", "layer")
      .attr("fill", d => COLORS[d.key] ?? "#999")
    .selectAll("rect")
    .data(d => d.map(pt => ({ ...pt, key: d.key })))
    .join("rect")
      .attr("x", d => xScale(d.data.label))
      .attr("y", d => yScale(d[1]))
      .attr("height", d => Math.max(0, yScale(d[0]) - yScale(d[1])))
      .attr("width", xScale.bandwidth())
      .attr("opacity", 0.88)
    .on("mousemove", (event, d) => {
      const r   = d.data;
      const lbl = bloquesMeta[d.key]?.label ?? d.key;
      const n   = r[d.key] ?? 0;
      let html = `<b>${r.label}</b> · ${lbl}<br><br>`;
      html += `<b>${n} escaños</b><br>`;
      html += `<span style="opacity:.6">${r._total} total · mayoría abs. ${Math.ceil(r._total / 2) + 1}</span><hr style="margin:6px 0;border:none;border-top:1px solid #eee">`;
      for (const b of bloquesActivos) {
        if (!r[b]) continue;
        html += `<div style="display:flex;justify-content:space-between;gap:20px">
          <span style="display:flex;align-items:center;gap:4px">
            <span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${COLORS[b]}"></span>
            ${bloquesMeta[b]?.label ?? b}
          </span>
          <b>${r[b]}</b>
        </div>`;
      }
      tooltip.html(html).style("display", "block")
        .style("left", (event.clientX + 14) + "px")
        .style("top",  (event.clientY - 10) + "px");
    })
    .on("mouseleave", () => tooltip.style("display", "none"));

  // Eje X
  g.append("g").attr("transform", `translate(0,${iH})`)
    .call(d3.axisBottom(xScale).tickSize(3))
    .call(g => g.select(".domain").attr("stroke", "#ccc"))
    .call(g => g.selectAll("text").attr("font-size", "10px").attr("fill", "#666"));

  // Eje Y
  g.append("g")
    .call(d3.axisLeft(yScale).ticks(6))
    .call(g => g.select(".domain").remove())
    .call(g => g.selectAll("text").attr("font-size", "10px").attr("fill", "#666"));

  // Leyenda
  const legend = svg.append("g").attr("transform", `translate(${margin.left + iW + 10},${margin.top})`);
  bloquesActivos.forEach((b, i) => {
    const row = legend.append("g").attr("transform", `translate(0,${i * 18})`);
    row.append("rect").attr("width", 10).attr("height", 10).attr("y", 1).attr("rx", 2).attr("fill", COLORS[b] ?? "#999").attr("opacity", 0.88);
    row.append("text").attr("x", 14).attr("y", 10).attr("font-size", "10px").attr("fill", "#555").text(bloquesMeta[b]?.label ?? b);
  });

  const wrap = document.createElement("div");
  wrap.style.cssText = "margin-bottom:1.5rem";
  wrap.appendChild(svg.node());
  return wrap;
})();
display(evolucionBloquesEl);
```

```js
const bloquesEl = (() => {
  const grid = document.createElement("div");
  grid.style.cssText = "display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1.2rem;margin-top:1rem";

  for (const bloque of bloquesList) {
    if (!bloque.partidos.length) continue;

    const card = document.createElement("div");
    card.style.cssText = "border:1px solid #e0e0e0;border-radius:10px;overflow:hidden";

    // Cabecera coloreada
    const header = document.createElement("div");
    header.style.cssText = "padding:10px 14px;display:flex;align-items:center;gap:10px";
    header.style.background = bloque.color + "22";
    header.style.borderBottom = "3px solid " + bloque.color;
    const votosStr = bloque.totalVotos >= 1e9
      ? (bloque.totalVotos / 1e9).toFixed(2) + "B"
      : (bloque.totalVotos / 1e6).toFixed(1) + "M";
    header.innerHTML =
      `<span style="display:inline-block;width:14px;height:14px;border-radius:3px;background:${bloque.color};flex-shrink:0"></span>` +
      `<strong style="font-size:1rem">${bloque.label}</strong>` +
      `<span style="margin-left:auto;font-size:.78em;opacity:.55;white-space:nowrap">${votosStr} votos · ${bloque.totalEscanos} esc</span>`;
    card.appendChild(header);

    // Lista de partidos
    const ul = document.createElement("div");
    ul.style.cssText = "padding:10px 14px;display:flex;flex-direction:column;gap:6px";

    const maxVotos = bloque.partidos[0]?.votos ?? 1;

    for (const p of bloque.partidos) {
      const row = document.createElement("div");
      row.style.cssText = "display:grid;grid-template-columns:80px 1fr auto;gap:6px;align-items:center";

      const siglas = document.createElement("span");
      siglas.style.cssText = "font-weight:600;font-size:.85em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis";
      siglas.textContent = p.siglas;
      siglas.title = p.siglas;

      const barWrap = document.createElement("div");
      barWrap.style.cssText = "background:#f0f0f0;border-radius:3px;height:6px;overflow:hidden";
      const bar = document.createElement("div");
      bar.style.cssText = "height:100%;border-radius:3px;background:" + bloque.color + ";opacity:.75";
      bar.style.width = Math.round(p.votos / maxVotos * 100) + "%";
      barWrap.appendChild(bar);

      const nums = document.createElement("span");
      nums.style.cssText = "font-size:.78em;opacity:.6;white-space:nowrap;text-align:right";
      nums.textContent = (p.votos / 1e6).toFixed(1) + "M v · " + p.escanos + " esc";
      nums.title = p.votos.toLocaleString("es-ES") + " votos acumulados · " + p.escanos + " escaños";

      row.appendChild(siglas);
      row.appendChild(barWrap);
      row.appendChild(nums);
      ul.appendChild(row);
    }
    card.appendChild(ul);

    // Nota al pie: fuente
    const footer = document.createElement("div");
    footer.style.cssText = "padding:6px 14px 8px;font-size:.72em;opacity:.45;border-top:1px solid #f0f0f0";
    footer.textContent = bloque.partidos.length + " partidos · votos y escaños acumulados 1977–2023";
    card.appendChild(footer);

    grid.appendChild(card);
  }
  return grid;
})();
display(bloquesEl);
```

---

> **Nota metodológica.** Los partidos mostrados son los que aparecen en el *top 5* de alguna provincia en al menos una elección. Los votos y escaños son acumulados sobre todas las circunscripciones y convocatorias del período 1977–2023. La clasificación es propia y agrupa formaciones con trayectoria similar; las coaliciones electorales se asignan al bloque de su componente principal.
