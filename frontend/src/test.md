---
title: Test
---

# Test de carga

```js
import * as d3 from "npm:d3";
import * as topojson from "npm:topojson-client";
display("d3.select: "              + typeof d3.select);
display("d3.geoConicConformal: "   + typeof d3.geoConicConformal);
display("d3.scaleSequential: "     + typeof d3.scaleSequential);
display("d3.interpolateRdYlGn: "   + typeof d3.interpolateRdYlGn);
display("d3.geoPath: "             + typeof d3.geoPath);
```

```js
const topo = await FileAttachment("data/provinces_topo.json").json();
const geo  = topojson.feature(topo, topo.objects.provinces);
display("TopoJSON OK, features: " + geo.features.length);
display("Sample name: " + geo.features[0].properties.name);
```

```js
const nameToIne = await FileAttachment("data/name_to_ine.json").json();
const missing = geo.features.filter(f => !nameToIne[f.properties.name]).map(f => f.properties.name);
display("Sin mapeo INE: " + JSON.stringify(missing));
```

```js
// Mapa Mercator — IIFE pattern (correcto en Observable Framework)
const mercatorMap = (() => {
  const w = 600, h = 400;
  const proj = d3.geoMercator().fitSize([w, h], geo);
  const path = d3.geoPath(proj);
  const svg  = d3.create("svg").attr("width", w).attr("height", h)
                 .style("border", "1px solid red").style("display","block");
  svg.selectAll("path").data(geo.features).join("path")
     .attr("d", path).attr("fill", "#ccc").attr("stroke", "#fff").attr("stroke-width", 0.5);
  return svg.node();
})();
display("Mapa Mercator OK — " + mercatorMap.tagName);
display(mercatorMap);
```

```js
// Mapa ConicConformal (igual que index.md)
const conicMap = (() => {
  const W = 800, H = 560;
  const penFeatures = geo.features.filter(f => {
    const ine = nameToIne[f.properties.name];
    return ine && !["35","38"].includes(ine);
  });
  const geoPen2 = { type: "FeatureCollection", features: penFeatures };
  const proj = d3.geoConicConformal()
    .center([-3.5, 40.2]).parallels([36, 44]).scale(2800).translate([W/2, H/2-20]);
  const path = d3.geoPath(proj);
  const svg  = d3.create("svg").attr("viewBox", "0 0 " + W + " " + H)
    .style("width", "600px").style("display", "block").style("border", "1px solid blue");
  svg.selectAll("path").data(geoPen2.features).join("path")
     .attr("d", path).attr("fill", "#6a9").attr("stroke", "#fff").attr("stroke-width", 0.5);
  return svg.node();
})();
display("ConicConformal OK — provincias: " + conicMap.querySelectorAll("path").length);
display(conicMap);
```

```js
const res = await FileAttachment("data/summary_province.json").json();
display("Results OK, convocatorias: " + Object.keys(res).length);
display("Prov '28' en 202307: " + JSON.stringify(res["202307"]?.["28"]?.nombre));
```
