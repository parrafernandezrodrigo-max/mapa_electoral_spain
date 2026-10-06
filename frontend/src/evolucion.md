---
title: Evolución barrera electoral
---

<div style="text-align:center;margin:1.5rem 0 1.5rem">
  <h1 style="font-size:2rem;font-weight:800;margin:0;line-height:1.1">Evolución de la barrera electoral real</h1>
  <p style="font-size:1.1rem;opacity:.65;margin:.4rem 0 0">Porcentaje de voto necesario para obtener el último escaño · 1977–2023</p>
</div>

```js
import * as d3 from "npm:d3";
const results     = await FileAttachment("data/summary_province.json").json();
const bloquesMeta = await FileAttachment("data/bloques_meta.json").json();
```

```js
const CONV_LABELS = {
  "197706": "1977", "197903": "1979", "198210": "1982", "198606": "1986",
  "198910": "1989", "199306": "1993", "199603": "1996",
  "200003": "2000", "200403": "2004", "200803": "2008",
  "201111": "2011", "201512": "2015", "201606": "2016",
  "201904": "2019a","201911": "2019b","202307": "2023",
};
const convIds = Object.keys(CONV_LABELS);

// Construir series por provincia
const seriesMap = new Map();
for (const convId of convIds) {
  for (const [cod, p] of Object.entries(results[convId] ?? {})) {
    if (!seriesMap.has(cod)) seriesMap.set(cod, { cod, nombre: p.nombre, pts: [] });
    if (p.barrera_real_pct != null) {
      seriesMap.get(cod).pts.push({
        convId, xi: convIds.indexOf(convId),
        y: p.barrera_real_pct, seats: p.seats_total,
        ultimo: p.partido_ultimo_escano,
      });
    }
  }
}
const series = [...seriesMap.values()].sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
```

```js
// Selector de provincias a destacar
const highlightInput = Inputs.search(series, {
  label: "Buscar provincia",
  format: d => d.nombre,
  placeholder: "Ceuta, Madrid, Soria…",
});
const highlighted = Generators.input(highlightInput);
```

${highlightInput}

<p style="font-size:.82em;opacity:.6;margin:.4rem 0 .8rem">
  <span style="display:inline-block;width:12px;height:12px;background:#2171b5;border-radius:2px;vertical-align:middle;margin-right:4px"></span>Barrera media ≤ 3% &nbsp;·&nbsp;
  <span style="display:inline-block;width:12px;height:12px;background:#d73027;border-radius:2px;vertical-align:middle;margin-right:4px"></span>Barrera media > 3% (más rojo = más alta) &nbsp;·&nbsp;
  Color basado en la media de todas las elecciones.
</p>

```js
const chartEl = (() => {
  const W = 900, H = 480;
  const margin = { top: 20, right: 110, bottom: 50, left: 52 };
  const iW = W - margin.left - margin.right;
  const iH = H - margin.top - margin.bottom;

  const highlightSet = new Set(highlighted.map(d => d.cod));

  // Eje Y: reajusta al rango de las provincias seleccionadas
  let yMin = 0, yMax = 58;
  if (highlightSet.size > 0) {
    const hlPts = series.filter(s => highlightSet.has(s.cod)).flatMap(s => s.pts.map(p => p.y));
    if (hlPts.length > 0) {
      yMin = Math.max(0, d3.min(hlPts) - 3);
      yMax = d3.max(hlPts) + 3;
    }
  }

  const xScale = d3.scaleLinear().domain([0, convIds.length - 1]).range([0, iW]);
  const yScale = d3.scaleLinear().domain([yMin, yMax]).range([iH, 0]).nice();

  const line = d3.line()
    .x(d => xScale(d.xi))
    .y(d => yScale(d.y))
    .defined(d => d.y != null);

  const svg = d3.create("svg")
    .attr("viewBox", "0 0 " + W + " " + H)
    .style("width", "100%").style("display", "block");

  const g = svg.append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  // Línea de referencia al 3% (solo si está en el rango visible)
  const [yDomMin, yDomMax] = yScale.domain();
  if (3 >= yDomMin && 3 <= yDomMax) {
    g.append("line")
      .attr("x1", 0).attr("y1", yScale(3))
      .attr("x2", iW).attr("y2", yScale(3))
      .attr("stroke", "#111").attr("stroke-width", 1.5).attr("stroke-dasharray", "6,3");
    g.append("text")
      .attr("x", iW + 4).attr("y", yScale(3) + 4)
      .attr("font-size", "10px").attr("fill", "#111").attr("font-weight", "600")
      .text("3%");
  }

  // Grid horizontal
  g.append("g").attr("class", "grid")
    .call(d3.axisLeft(yScale).tickSize(-iW).tickFormat(""))
    .call(g => g.select(".domain").remove())
    .call(g => g.selectAll("line").attr("stroke", "#e8e8e8").attr("stroke-dasharray", "2,2"));

  // Eje X
  g.append("g").attr("transform", "translate(0," + iH + ")")
    .call(d3.axisBottom(xScale)
      .ticks(convIds.length - 1)
      .tickFormat(i => CONV_LABELS[convIds[Math.round(i)]] ?? ""))
    .call(g => g.select(".domain").attr("stroke", "#ccc"))
    .call(g => g.selectAll("text").attr("font-size", "11px").attr("fill", "#666"));

  // Eje Y
  g.append("g")
    .call(d3.axisLeft(yScale).ticks(8).tickFormat(d => d + "%"))
    .call(g => g.select(".domain").remove())
    .call(g => g.selectAll("text").attr("font-size", "11px").attr("fill", "#666"));

  // Label eje Y
  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -iH / 2).attr("y", -40)
    .attr("text-anchor", "middle")
    .attr("font-size", "11px").attr("fill", "#888")
    .text("Barrera real (%)");

  // Escalas de color por barrera media: azul ≤3%, naranja-rojo >3%
  const colorBelow3 = d3.scaleSequential([3, 0]).interpolator(d3.interpolateBlues);
  const colorAbove3 = d3.scaleSequential([3, 52]).interpolator(d3.interpolateOrRd);
  function lineBaseColor(s) {
    const avg = s.pts.length ? s.pts.reduce((sum, p) => sum + p.y, 0) / s.pts.length : 0;
    return avg <= 3 ? colorBelow3(Math.max(avg, 0.3)) : colorAbove3(Math.min(avg, 51));
  }

  // Líneas de fondo (no destacadas) y destacadas
  const bgGroup = g.append("g");
  const fgGroup = g.append("g");

  // Tooltip compartido
  const tooltip = d3.select(document.body).append("div")
    .style("position", "fixed").style("display", "none")
    .style("background", "var(--theme-background-alt,#fff)")
    .style("border", "1px solid #ddd").style("border-radius", "6px")
    .style("padding", "9px 13px").style("font-size", ".82em")
    .style("pointer-events", "none").style("box-shadow", "0 4px 16px rgba(0,0,0,.12)")
    .style("z-index", "100").style("min-width", "180px");

  function showProvTooltip(event, s) {
    const [mx] = d3.pointer(event, g.node());
    const xi = Math.max(0, Math.min(convIds.length - 1, Math.round(xScale.invert(mx))));
    const convId = convIds[xi];
    const pt = s.pts.find(p => p.xi === xi);

    g.selectAll(".hover-line").remove();
    g.append("line").attr("class", "hover-line")
      .attr("x1", xScale(xi)).attr("y1", 0)
      .attr("x2", xScale(xi)).attr("y2", iH)
      .attr("stroke", "#999").attr("stroke-width", 1).attr("stroke-dasharray", "3,2");

    if (pt) {
      // Punto destacado en la línea activa
      g.selectAll(".hover-dot").remove();
      g.append("circle").attr("class", "hover-dot")
        .attr("cx", xScale(xi)).attr("cy", yScale(pt.y))
        .attr("r", 5).attr("fill", "#e63946").attr("stroke", "#fff").attr("stroke-width", 1.5);

      tooltip.html(
        `<strong style="font-size:1.05em">${s.nombre}</strong><br>` +
        `<span style="opacity:.6">${CONV_LABELS[convId]}</span><br><br>` +
        `<b>Barrera real:</b> ${pt.y.toFixed(2)}%<br>` +
        `<b>Último escaño:</b> ${pt.ultimo}<br>` +
        `<b>Escaños:</b> ${pt.seats}`
      );
    } else {
      tooltip.html(`<strong>${s.nombre}</strong><br><span style="opacity:.5">Sin datos en ${CONV_LABELS[convId]}</span>`);
    }
    tooltip.style("display", "block")
      .style("left", (event.clientX + 16) + "px")
      .style("top",  (event.clientY - 20) + "px");
  }

  function hideTooltip() {
    tooltip.style("display", "none");
    g.selectAll(".hover-line, .hover-dot").remove();
  }

  for (const s of series) {
    const isHL = highlightSet.has(s.cod);
    const target = isHL ? fgGroup : bgGroup;
    const baseColor = lineBaseColor(s);

    // Línea visible
    target.append("path")
      .datum(s.pts)
      .attr("fill", "none").attr("d", line)
      .attr("stroke-width", isHL ? 2.5 : 0.9)
      .attr("stroke", isHL ? "#e63946" : baseColor)
      .attr("opacity", isHL ? 1 : (highlightSet.size > 0 ? 0.25 : 0.75))
      .style("pointer-events", "none");

    // Hit-area invisible (más ancha, captura hover)
    target.append("path")
      .datum(s.pts)
      .attr("fill", "none").attr("d", line)
      .attr("stroke", "transparent").attr("stroke-width", 10)
      .style("cursor", "pointer")
      .on("mousemove", (event) => showProvTooltip(event, s))
      .on("mouseleave", hideTooltip);

    if (isHL) {
      fgGroup.selectAll(null).data(s.pts).join("circle")
        .attr("cx", d => xScale(d.xi)).attr("cy", d => yScale(d.y))
        .attr("r", 3).attr("fill", "#e63946").style("pointer-events", "none");

      const last = s.pts[s.pts.length - 1];
      if (last) {
        fgGroup.append("text")
          .attr("x", xScale(last.xi) + 5).attr("y", yScale(last.y) + 4)
          .attr("font-size", "10px").attr("fill", "#e63946").text(s.nombre)
          .style("pointer-events", "none");
      }
    }
  }

  const wrap = document.createElement("div");
  wrap.style.position = "relative";
  wrap.appendChild(svg.node());
  return wrap;
})();
display(chartEl);
```

---

## Tabla resumen

```js
const tablaEl = (() => {
  // Construir filas: una por provincia, columnas = elecciones
  const rows = series.map(s => {
    const row = { Provincia: s.nombre };
    for (const cid of convIds) {
      const pt = s.pts.find(p => p.convId === cid);
      row[CONV_LABELS[cid]] = pt ? +pt.y.toFixed(1) : null;
    }
    return row;
  });
  return Inputs.table(rows, {
    columns: ["Provincia", ...convIds.map(c => CONV_LABELS[c])],
    rows: 52,
    format: Object.fromEntries(
      convIds.map(c => [CONV_LABELS[c], d => d != null ? d.toFixed(1) + "%" : "—"])
    ),
  });
})();
display(tablaEl);
```
