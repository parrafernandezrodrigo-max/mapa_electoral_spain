---
title: Mapa Electoral España
---

<div style="text-align:center;margin:1.5rem 0 2rem">
  <h1 style="font-size:2.2rem;font-weight:800;margin:0;line-height:1.1;letter-spacing:-.5px">Mapa Electoral España</h1>
  <p style="font-size:1.15rem;opacity:.65;margin:.45rem 0 0;font-weight:400">Elecciones Generales 1977–2023</p>
</div>

```js
import * as d3       from "npm:d3";
import * as topojson from "npm:topojson-client";
```

```js
const topoData    = await FileAttachment("data/provinces_topo.json").json();
const results     = await FileAttachment("data/summary_province.json").json();
const bloquesMeta = await FileAttachment("data/bloques_meta.json").json();
const nameToIne   = await FileAttachment("data/name_to_ine.json").json();
```

```js
const geo = topojson.feature(topoData, topoData.objects.provinces);
geo.features.forEach(f => { f.properties.cod_ine = nameToIne[f.properties.name] ?? null; });

const CANARIAS  = new Set(["35", "38"]);
const ENCLAVES  = new Set(["51", "52"]);
const geoPen    = { type: "FeatureCollection", features: geo.features.filter(f => !CANARIAS.has(f.properties.cod_ine) && !ENCLAVES.has(f.properties.cod_ine)) };
const geoCan    = { type: "FeatureCollection", features: geo.features.filter(f =>  CANARIAS.has(f.properties.cod_ine)) };
const geoCeuta  = { type: "FeatureCollection", features: geo.features.filter(f => f.properties.cod_ine === "51") };
const geMelilla = { type: "FeatureCollection", features: geo.features.filter(f => f.properties.cod_ine === "52") };

const COLORS = {
  ...Object.fromEntries(Object.entries(bloquesMeta).map(([k, v]) => [k, v.color])),
  otros: "#999"
};

const barrierColor = d3.scaleSequential()
  .domain([2, 52])
  .interpolator(t => d3.interpolateRdYlGn(1 - t))
  .clamp(true);

const wastedColor = d3.scaleSequential()
  .domain([0, 40])
  .interpolator(t => d3.interpolateOranges(t * 0.9 + 0.05))
  .clamp(true);

const CONV_LABELS = {
  "197706": "Jun 1977", "197903": "Mar 1979", "198210": "Oct 1982", "198606": "Jun 1986",
  "198910": "Oct 1989", "199306": "Jun 1993", "199603": "Mar 1996",
  "200003": "Mar 2000", "200403": "Mar 2004", "200803": "Mar 2008",
  "201111": "Nov 2011", "201512": "Dic 2015", "201606": "Jun 2016",
  "201904": "Abr 2019", "201911": "Nov 2019", "202307": "Jul 2023",
};
```

```js
const convInput = Inputs.select(Object.keys(CONV_LABELS), {
  label: "Elección",
  format: d => CONV_LABELS[d],
  value: "202307",

});
const vistaInput = Inputs.radio(["bloque_ganador", "barrera_real", "votos_perdidos"], {
  label: "Vista",
  format: d => ({ bloque_ganador: "Bloque ganador", barrera_real: "Barrera real", votos_perdidos: "Votos perdidos" })[d],
  value: "bloque_ganador",
});
const convId = Generators.input(convInput);
const vista  = Generators.input(vistaInput);
```

<div style="display:flex;gap:2rem;align-items:flex-end;flex-wrap:wrap;margin:0 0 1rem">
  ${convInput}
  ${vistaInput}
</div>

```js
// Leyenda
const legendEl = (() => {
  const div = document.createElement("div");
  div.style.cssText = "display:flex;gap:14px;flex-wrap:wrap;margin-bottom:12px";
  if (vista === "barrera_real") {
    div.style.alignItems = "center";
    div.style.gap = "8px";
    const label = document.createElement("span");
    label.style.opacity = "0.7";
    label.style.fontSize = ".82em";
    label.textContent = "Barrera real →";
    div.appendChild(label);
    for (const v of [2, 5, 10, 15, 20, 30, 50]) {
      const s = document.createElement("span");
      s.style.cssText = "display:inline-flex;align-items:center;gap:3px;font-size:.82em";
      s.innerHTML = `<span style="display:inline-block;width:24px;height:12px;background:${barrierColor(v)};border-radius:2px"></span><span>${v}%</span>`;
      div.appendChild(s);
    }
    const note = document.createElement("span");
    note.style.cssText = "opacity:.5;font-size:.82em";
    note.textContent = "(verde=baja · rojo=alta)";
    div.appendChild(note);
  } else if (vista === "votos_perdidos") {
    div.style.alignItems = "center";
    div.style.gap = "8px";
    const label = document.createElement("span");
    label.style.cssText = "opacity:.7;font-size:.82em";
    label.textContent = "% votos sin escaño →";
    div.appendChild(label);
    for (const v of [0, 5, 10, 15, 20, 30, 40]) {
      const s = document.createElement("span");
      s.style.cssText = "display:inline-flex;align-items:center;gap:3px;font-size:.82em";
      s.innerHTML = `<span style="display:inline-block;width:24px;height:12px;background:${wastedColor(v)};border-radius:2px"></span><span>${v}%</span>`;
      div.appendChild(s);
    }
    const note = document.createElement("span");
    note.style.cssText = "opacity:.5;font-size:.82em";
    note.textContent = "(claro=poco · naranja=mucho)";
    div.appendChild(note);
  } else {
    const entries = [...Object.entries(bloquesMeta), ["otros", { label: "Otros", color: "#999" }]];
    for (const [, b] of entries) {
      const s = document.createElement("span");
      s.style.cssText = "display:inline-flex;align-items:center;gap:5px;font-size:.82em";
      s.innerHTML = `<span style="display:inline-block;width:13px;height:13px;background:${b.color};border-radius:2px"></span>${b.label}`;
      div.appendChild(s);
    }
  }
  return div;
})();
display(legendEl);
```

```js
// Mapa
const mapEl = (() => {
  const W = 800, H = 560;
  const convData = results[convId] ?? {};

  function provColor(cod) {
    const p = convData[cod];
    if (!p) return "#e0e0e0";
    if (vista === "barrera_real") return p.barrera_real_pct != null ? barrierColor(p.barrera_real_pct) : "#e0e0e0";
    if (vista === "votos_perdidos") return p.pct_votos_perdidos != null ? wastedColor(p.pct_votos_perdidos) : "#e0e0e0";

    // Detectar empate entre bloques
    const esc = p.escanos_por_bloque ?? {};
    const maxEsc = Math.max(0, ...Object.values(esc));
    if (maxEsc === 0) return "#e0e0e0";
    const ganadores = Object.keys(esc).filter(b => esc[b] === maxEsc).sort();
    if (ganadores.length === 1) return COLORS[ganadores[0]] ?? "#999";
    return ensurePattern(ganadores);
  }

  const projPen = d3.geoConicConformal()
    .center([-3.5, 40.2]).parallels([36, 44]).scale(2800).translate([W / 2, H / 2 - 20]);
  const pathPen = d3.geoPath(projPen);

  const wrap = document.createElement("div");
  wrap.style.cssText = "position:relative;max-width:" + W + "px;user-select:none";

  const svgEl = d3.create("svg")
    .attr("viewBox", "0 0 " + W + " " + H)
    .style("width", "100%")
    .style("display", "block");
  wrap.appendChild(svgEl.node());

  // Patrones de rayas: generación bajo demanda para cualquier nº de bloques
  const defs = svgEl.append("defs");
  const createdPatterns = new Set();

  function ensurePattern(ganadores) {
    const id = "tie-" + ganadores.join("--");
    if (!createdPatterns.has(id)) {
      createdPatterns.add(id);
      const n = ganadores.length;
      const stripeW = n <= 2 ? 4 : 3;          // 4px para duelos, 3px para triples+
      const totalW  = stripeW * n;
      const pat = defs.append("pattern")
        .attr("id", id)
        .attr("patternUnits", "userSpaceOnUse")
        .attr("width", totalW).attr("height", totalW)
        .attr("patternTransform", "rotate(45 0 0)");
      ganadores.forEach((b, i) => {
        pat.append("rect")
          .attr("x", i * stripeW).attr("width", stripeW).attr("height", totalW)
          .attr("fill", COLORS[b] ?? "#999");
      });
    }
    return "url(#" + id + ")";
  }

  const tip = d3.select(wrap).append("div")
    .style("position", "absolute").style("display", "none")
    .style("background", "var(--theme-background-alt,#fff)")
    .style("border", "1px solid #ddd").style("border-radius", "6px")
    .style("padding", "10px 14px").style("font-size", ".82em")
    .style("box-shadow", "0 4px 16px rgba(0,0,0,.15)")
    .style("pointer-events", "none").style("max-width", "260px")
    .style("line-height", "1.6").style("z-index", "10");

  function showTip(event, cod) {
    const p = convData[cod];
    if (!p) return;
    const bloqueLabel = bloquesMeta[p.bloque_ganador]?.label ?? "—";
    const bloqueColor = COLORS[p.bloque_ganador] ?? "#999";
    const escBloques = Object.entries(p.escanos_por_bloque ?? {})
      .filter(([, n]) => n > 0).sort((a, b) => b[1] - a[1])
      .map(([b, n]) => `<span style="color:${COLORS[b] ?? "#999"};font-weight:600">${n}</span> ${bloquesMeta[b]?.label ?? b}`)
      .join(" · ");
    const top5 = (p.top5_partidos ?? []).slice(0, 5)
      .map(q => `<tr><td>${q.siglas}</td><td style="text-align:right;padding-left:8px">${q.votos.toLocaleString("es-ES")}</td><td style="text-align:right;padding-left:6px">${q.escanos_dhondt}</td></tr>`)
      .join("");

    const wastedRows = Object.entries(p.votos_perdidos_por_bloque ?? {})
      .sort((a, b) => b[1] - a[1])
      .map(([b, v]) => `<tr><td style="color:${COLORS[b] ?? "#999"};font-weight:600">${bloquesMeta[b]?.label ?? b}</td><td style="text-align:right;padding-left:8px">${v.toLocaleString("es-ES")}</td></tr>`)
      .join("");

    const wastedSection = vista === "votos_perdidos" && wastedRows ? `
      <div style="margin-top:6px;font-size:.9em;font-weight:600">Votos sin escaño: ${p.pct_votos_perdidos?.toFixed(1) ?? "—"}%</div>
      <table style="width:100%;border-collapse:collapse;margin-top:2px">
        <tr style="opacity:.5;font-size:.9em"><td>Bloque</td><td style="text-align:right">Votos</td></tr>
        ${wastedRows}
      </table>` : "";

    tip.html(`
      <strong style="font-size:1.05em">${p.nombre}</strong><br>
      <span style="opacity:.6">${p.label_eleccion} · ${p.seats_total} escaños</span><br><br>
      <b>Bloque:</b> <span style="color:${bloqueColor}">${bloqueLabel}</span><br>
      <b>Barrera real:</b> ${p.barrera_real_pct?.toFixed(1) ?? "—"}% · <b>Último:</b> ${p.partido_ultimo_escano}<br>
      <div style="margin:4px 0;font-size:.9em">${escBloques}</div>
      <table style="width:100%;border-collapse:collapse;margin-top:4px">
        <tr style="opacity:.5;font-size:.9em"><td>Partido</td><td style="text-align:right">Votos</td><td style="text-align:right">Esc</td></tr>
        ${top5}
      </table>
      ${wastedSection}`);
    const rect = wrap.getBoundingClientRect();
    tip.style("left", (event.clientX - rect.left + 14) + "px")
       .style("top",  (event.clientY - rect.top  - 10) + "px")
       .style("display", "block");
  }

  function drawProvinces(geoData, pathFn) {
    svgEl.append("g").selectAll("path")
      .data(geoData.features).join("path")
      .attr("d", pathFn)
      .attr("fill", f => provColor(f.properties.cod_ine))
      .attr("stroke", "#fff").attr("stroke-width", 0.6)
      .attr("pointer-events", "all")  // captura eventos aunque fill sea pattern/none
      .style("cursor", "pointer")
      .on("mouseover", function(evt, f) {
        d3.select(this).attr("stroke", "#333").attr("stroke-width", 1.5);
        showTip(evt, f.properties.cod_ine);
      })
      .on("mousemove", (evt, f) => showTip(evt, f.properties.cod_ine))
      .on("mouseout", function() {
        d3.select(this).attr("stroke", "#fff").attr("stroke-width", 0.6);
        tip.style("display", "none");
      });
  }

  // Canarias: fitExtent en la sección izquierda del inset
  const projCan = d3.geoMercator()
    .fitExtent([[10, H - 134], [205, H - 8]], geoCan);
  const pathCan = d3.geoPath(projCan);

  // Ceuta y Melilla: fitExtent en la sección derecha del inset
  const projCeuta = d3.geoMercator()
    .fitExtent([[213, H - 128], [275, H - 78]], geoCeuta);
  const pathCeuta = d3.geoPath(projCeuta);

  const projMelilla = d3.geoMercator()
    .fitExtent([[213, H - 68], [275, H - 8]], geMelilla);
  const pathMelilla = d3.geoPath(projMelilla);

  drawProvinces(geoPen, pathPen);
  drawProvinces(geoCan, pathCan);
  drawProvinces(geoCeuta, pathCeuta);
  drawProvinces(geMelilla, pathMelilla);

  // Recuadro inset (más pequeño)
  const iY = H - 150, iW = 275, iH = 145;
  svgEl.append("rect")
    .attr("x", 5).attr("y", iY).attr("width", iW).attr("height", iH)
    .attr("fill", "none").attr("stroke", "#bbb").attr("stroke-width", 1).attr("stroke-dasharray", "4,3");

  // Separador vertical entre Canarias y enclaves
  svgEl.append("line")
    .attr("x1", 208).attr("y1", iY + 2).attr("x2", 208).attr("y2", iY + iH - 2)
    .attr("stroke", "#ddd").attr("stroke-width", 1).attr("stroke-dasharray", "2,2");

  // Separador horizontal entre Ceuta y Melilla
  svgEl.append("line")
    .attr("x1", 209).attr("y1", H - 76).attr("x2", 279).attr("y2", H - 76)
    .attr("stroke", "#ddd").attr("stroke-width", 1).attr("stroke-dasharray", "2,2");

  // Etiquetas
  for (const [txt, x, y] of [
    ["Canarias", 10, iY + 13],
    ["Ceuta",    213, iY + 13],
    ["Melilla",  213, H - 76 + 13],
  ]) {
    svgEl.append("text").attr("x", x).attr("y", y)
      .attr("font-size", "10px").attr("fill", "#888").text(txt);
  }

  return wrap;
})();
display(mapEl);
```

---

## Resultados por provincia — ${CONV_LABELS[convId]}

```js
const tableEl = (() => {
  const convData = results[convId] ?? {};
  const rows = Object.entries(convData)
    .map(([, p]) => ({
      "Provincia":        p.nombre,
      "Escaños":          p.seats_total,
      "Barrera real %":   p.barrera_real_pct != null ? +p.barrera_real_pct.toFixed(2) : null,
      "Votos perdidos %": p.pct_votos_perdidos != null ? +p.pct_votos_perdidos.toFixed(1) : null,
      "Último escaño":    p.partido_ultimo_escano,
      "Bloque ganador":   bloquesMeta[p.bloque_ganador]?.label ?? "—",
    }));

  return Inputs.table(rows, {
    columns: ["Provincia", "Escaños", "Barrera real %", "Votos perdidos %", "Último escaño", "Bloque ganador"],
    rows: 52,
    sort: "Votos perdidos %",
    reverse: true,
  });
})();
display(tableEl);
```
