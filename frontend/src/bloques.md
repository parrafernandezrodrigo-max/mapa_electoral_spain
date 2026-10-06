---
title: Bloques ideológicos
---

<div style="text-align:center;margin:1.5rem 0 1.5rem">
  <h1 style="font-size:2rem;font-weight:800;margin:0;line-height:1.1">Bloques ideológicos</h1>
  <p style="font-size:1.1rem;opacity:.65;margin:.4rem 0 0">Clasificación de partidos utilizada en el mapa · 1977–2023</p>
</div>

```js
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
