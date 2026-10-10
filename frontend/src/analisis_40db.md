---
title: Análisis encuesta 40dB
toc: false
---

<style>
/* Usar todo el ancho disponible — quita el padding derecho del TOC */
article.observablehq--article,
.observablehq--article {
  max-width: 100% !important;
  padding-right: 1rem !important;
}

/* ── Cabecera de sección ── */
.enc-header { text-align:center; margin:1.5rem 0 1rem; }
.enc-header h1 { font-size:1.9rem; font-weight:800; margin:0; line-height:1.15; }
.enc-header p  { font-size:1rem; opacity:.65; margin:.4rem 0 0; }
.moe-badge {
  display:inline-block;
  background:color-mix(in srgb, var(--theme-blue,#4269d0) 12%, transparent);
  border:1px solid color-mix(in srgb, var(--theme-blue,#4269d0) 35%, transparent);
  color:var(--theme-blue,#4269d0);
  font-size:.75rem; font-weight:700;
  padding:2px 9px; border-radius:4px; margin-left:8px; vertical-align:middle;
}

/* ── Tarjeta metodología ── */
.methodology {
  background:var(--theme-background-alt);
  border:1px solid color-mix(in srgb, var(--theme-foreground) 12%, transparent);
  border-radius:8px; padding:16px 20px; margin:0 0 1.2rem;
  font-size:.85rem; line-height:1.75; color:var(--theme-foreground);
}
.methodology h2 { font-size:.9rem; font-weight:700; margin:0 0 8px; letter-spacing:.04em; }
.tier-row { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
.tier-pill {
  display:flex; align-items:center; gap:6px;
  background:var(--theme-background);
  border:1px solid color-mix(in srgb, var(--theme-foreground) 12%, transparent);
  border-radius:6px; padding:4px 10px; font-size:.78rem;
}

/* ── Resumen nacional ── */
.nat-summary {
  display:flex; gap:10px; flex-wrap:wrap; margin:0 0 1rem;
}
.nat-card {
  flex:1; min-width:110px;
  background:var(--theme-background-alt);
  border:1px solid color-mix(in srgb, var(--theme-foreground) 10%, transparent);
  border-radius:8px; padding:10px 14px; text-align:center;
}
.nat-card .p-name  { font-weight:700; font-size:.88rem; }
.nat-card .p-seats { font-size:1.5rem; font-weight:800; line-height:1.1; }
.nat-card .p-delta { font-size:.76rem; opacity:.65; margin-top:2px; }
.nat-card .p-pct   { font-size:.76rem; opacity:.5; }

/* ── Barra de bloques ── */
.bloc-bar {
  background:var(--theme-background-alt);
  border:1px solid color-mix(in srgb, var(--theme-foreground) 10%, transparent);
  border-radius:8px; padding:10px 16px;
  font-size:.84rem; margin:0 0 1.2rem;
  display:flex; flex-wrap:wrap; gap:16px; align-items:center;
}

/* ── Tabs ── */
.party-tabs {
  display:flex; gap:0; border-bottom:2px solid
    color-mix(in srgb, var(--theme-foreground) 15%, transparent);
  margin:0 0 0; overflow-x:auto;
}
.tab-btn {
  background:none; border:none; cursor:pointer;
  padding:9px 18px; font-size:.86rem; font-weight:600;
  color:color-mix(in srgb, var(--theme-foreground) 40%, transparent);
  border-bottom:3px solid transparent; margin-bottom:-2px;
  white-space:nowrap; transition:color .15s;
  font-family:inherit;
}
.tab-btn:hover  { color:color-mix(in srgb, var(--theme-foreground) 70%, transparent); }
.tab-btn.active { border-bottom-color:currentColor; }

/* ── Secciones ── */
.party-section { display:none; margin-top:12px; }
.party-section.active { display:block; }

.section-summary {
  background:var(--theme-background-alt);
  border:1px solid color-mix(in srgb, var(--theme-foreground) 10%, transparent);
  border-radius:6px; padding:9px 14px;
  font-size:.82rem; margin-bottom:12px;
  color:color-mix(in srgb, var(--theme-foreground) 75%, transparent);
}
.section-summary b { color:var(--theme-foreground); }

/* ── Tabla ── */
.enc-table-wrap { overflow-x:auto; -webkit-overflow-scrolling:touch; }
.enc-table {
  width:100%; border-collapse:collapse; font-size:.77rem;
  color:var(--theme-foreground); table-layout:auto;
}
.enc-table thead th {
  background:var(--theme-background-alt);
  color:color-mix(in srgb, var(--theme-foreground) 60%, transparent);
  font-weight:600; padding:6px 7px; text-align:left;
  border-bottom:2px solid color-mix(in srgb, var(--theme-foreground) 15%, transparent);
  position:sticky; top:0; z-index:5; white-space:nowrap; overflow:hidden;
}
.enc-table thead th.r { text-align:right; }
.enc-table thead th.c { text-align:center; }
/* Columnas sortables */
.enc-table thead th[data-k] { cursor:pointer; user-select:none; }
.enc-table thead th[data-k]:hover { color:var(--theme-foreground); }
.enc-table thead th[data-k][data-dir="asc"]::after  { content:" ↑"; font-size:.65rem; opacity:.6; }
.enc-table thead th[data-k][data-dir="desc"]::after { content:" ↓"; font-size:.65rem; opacity:.6; }
.enc-table tbody tr {
  border-bottom:1px solid
    color-mix(in srgb, var(--theme-foreground) 8%, transparent);
  transition:background .1s;
}
.enc-table tbody tr:hover {
  background:color-mix(in srgb, var(--theme-foreground) 4%, transparent);
}
/* Todas las celdas: sin salto de línea por defecto */
.enc-table td {
  padding:4px 7px; vertical-align:middle; white-space:nowrap;
}
.enc-table td.r  { text-align:right; font-variant-numeric:tabular-nums; }
.enc-table td.c  { text-align:center; }
.enc-table td.prov { font-weight:600; }
/* Saca de: ancho para 2 badges en la misma línea */
.enc-table td.wrap { white-space:nowrap; min-width:130px; }
/* Mínimos para columnas clave */
.enc-table .col-conf { min-width:165px; }
.enc-table .col-pct  { min-width:44px; }

.enc-table tfoot tr {
  border-top:2px solid color-mix(in srgb, var(--theme-foreground) 18%, transparent);
  background:var(--theme-background-alt);
  font-weight:700;
}
.enc-table tfoot td { padding:6px 8px; }

/* Pills */
.pill {
  display:inline-block; padding:1px 6px; border-radius:4px;
  font-size:.70rem; font-weight:700; margin:1px;
}
.frag-filo     { background:#F8514922; color:#F85149; border:1px solid #F8514944; cursor:help; }
.frag-sensible { background:#D2992222; color:#D29922; border:1px solid #D2992244; cursor:help; }
.frag-none     { background:#3FB95022; color:#3FB950; border:1px solid #3FB95044; cursor:help; }
.p-VOX  { background:#3FB95022; color:#3FB950; border:1px solid #3FB95044; }
.p-PP   { background:#60A5FA22; color:#60A5FA; border:1px solid #60A5FA44; }
.p-PSOE { background:#F8717122; color:#F87171; border:1px solid #F8717144; }
.p-SUMAR{ background:#C084FC22; color:#C084FC; border:1px solid #C084FC44; }
.p-IZQ  { background:#E879F922; color:#E879F9; border:1px solid #E879F944; }
.p-other{ background:#6B728022; color:#9CA3AF; border:1px solid #6B728044; }

/* Colores semánticos */
.gain  { color:#3FB950; font-weight:700; }
.loss  { color:#F85149; font-weight:700; }
.same  { color:color-mix(in srgb, var(--theme-foreground) 45%, transparent); }
.dots  { letter-spacing:2px; }
.c-seguro { color:#F78166; }
.c-muy    { color:#3FB950; }
.c-prob   { color:#52C46A; }
.c-pos    { color:#D29922; }
.c-poco   { color:color-mix(in srgb, var(--theme-foreground) 45%, transparent); }
</style>

<div class="enc-header">
  <h1>Análisis de escaños por provincia <span class="moe-badge">MoE ±3,5pp · IC 95%</span></h1>
  <p>Encuesta 40dB/El País/SER · Octubre 2026 · N=800 · Swing uniforme sobre resultados reales 23J</p>
</div>

<div class="methodology">
  <h2>Metodología</h2>
  <p>
    <strong>Swing model:</strong> factor proporcional uniforme sobre los votos reales de cada partido en cada provincia
    (factor = estimación 40dB / resultado 23J nacional), recalculando el reparto D'Hondt real.
  </p>
  <p style="margin-top:8px">
    La columna <strong>Swing</strong> indica si el swing produce un cambio de escaños en esa provincia:
    <span class="pill frag-none">FIABLE</span> = el swing cambia los escaños y el último ganado es sólido (no se pierde aunque el partido saque un 5% menos),
    <span class="pill frag-sensible">SENSIBLE</span> = el swing cambia los escaños pero el último ganado es marginal (un 5% menos lo pierde),
    <span class="pill frag-filo">AL FILO</span> = el <em>último</em> escaño que da el swing es el último repartido por D'Hondt — cualquier pequeña bajada lo pierde.
  </p>
  <p style="margin-top:8px">
    La columna <strong>¿Cerca del sig. escaño?</strong> mide la distancia entre la estimación swing y el umbral D'Hondt
    para ganar <em>un escaño más</em> del que ya da el swing. El MoE de la encuesta es ±3,5pp (N=800, IC 95%):
  </p>
  <div class="tier-row">
    <div class="tier-pill"><span class="dots c-muy">●●●●○</span> <strong>MUY PROBABLE</strong> — 0–1,5pp: menos de la mitad del MoE</div>
    <div class="tier-pill"><span class="dots c-prob">●●●○○</span> <strong>PROBABLE</strong> — 1,5–3pp: dentro del MoE</div>
    <div class="tier-pill"><span class="dots c-pos">●●○○○</span> <strong>POSIBLE</strong> — 3–5pp: entre 1× y 1,5× el MoE</div>
    <div class="tier-pill"><span class="dots c-poco">●○○○○</span> <strong>POCO PROBABLE</strong> — &gt; 5pp: supera el MoE</div>
  </div>
</div>

```js
const allData   = await FileAttachment("data/all_parties_data.json").json();
const summaries = await FileAttachment("data/party_summaries.json").json();
```

```js
const PARTIES = [
  { key: "VOX",   label: "VOX",                  color: "#3FB950", pct26: 18.9 },
  { key: "PP",    label: "PP",                   color: "#60A5FA", pct26: 31.9 },
  { key: "PSOE",  label: "PSOE",                 color: "#F87171", pct26: 28.1 },
  { key: "SUMAR", label: "SUMAR",                color: "#C084FC", pct26:  5.3 },
  { key: "IZQ",   label: "Izquierda (SUMAR+Pod.)",color: "#E879F9", pct26:  7.6 },
];

const CONF_CLASS = {
  "SEGURO":        "c-seguro",
  "MUY PROBABLE":  "c-muy",
  "PROBABLE":      "c-prob",
  "POSIBLE":       "c-pos",
  "POCO PROBABLE": "c-poco",
};
// Texto corto para la columna Confianza (con tooltip completo)
const CONF_CELL = {
  "SEGURO":        { cls:"c-seguro", dots:"●●●●●", short:"SEGURO"   },
  "MUY PROBABLE":  { cls:"c-muy",    dots:"●●●●○", short:"MUY PROB."},
  "PROBABLE":      { cls:"c-prob",   dots:"●●●○○", short:"PROB."    },
  "POSIBLE":       { cls:"c-pos",    dots:"●●○○○", short:"POSIBLE"  },
  "POCO PROBABLE": { cls:"c-poco",   dots:"●○○○○", short:"POCO PROB."},
};
// Badge de swing: solo aparece cuando el swing cambia los escaños (s26 > s23)
const FRAG_LABEL = {
  filo:     `<span class="pill frag-filo"     title="Gana el último escaño con su primer divisor — cualquier pequeña bajada lo pierde">AL FILO</span>`,
  sensible: `<span class="pill frag-sensible" title="El escaño ganado se pierde si los votos bajan un 5%">SENSIBLE</span>`,
  none:     `<span class="pill frag-none"     title="Cambio de escaños sólido">FIABLE</span>`,
};

function partyBadge(name) {
  const cls = ["VOX","PP","PSOE","SUMAR","IZQ"].includes(name) ? `p-${name}` : "p-other";
  return `<span class="pill ${cls}">${name === "IZQ" ? "Izq." : name}</span>`;
}
```

```js
// ── Resumen nacional ──────────────────────────────────────────────────────
const natDiv = document.createElement("div");
natDiv.className = "nat-summary";
for (const p of PARTIES) {
  const s = summaries[p.key];
  const diff = s.seats26 - s.seats23;
  const dStr = diff > 0 ? `+${diff}` : `${diff}`;
  const dCls = diff > 0 ? "gain" : diff < 0 ? "loss" : "same";
  natDiv.innerHTML += `
    <div class="nat-card">
      <div class="p-name" style="color:${p.color}">${p.label}</div>
      <div class="p-seats" style="color:${p.color}">${s.seats26}</div>
      <div class="p-delta"><span class="${dCls}">${dStr}</span> vs 2023 (${s.seats23})</div>
      <div class="p-pct">${p.pct26}% encuesta</div>
    </div>`;
}
display(natDiv);

// ── Barra de bloques ──────────────────────────────────────────────────────
const pp26   = summaries.PP.seats26;
const vox26  = summaries.VOX.seats26;
const psoe26 = summaries.PSOE.seats26;
const izq26  = summaries.IZQ.seats26;
const derecha = pp26 + vox26;
const MAYORIA = 176;
const blocEl = document.createElement("div");
blocEl.className = "bloc-bar";
blocEl.innerHTML = `
  <div><strong>Bloque derecha</strong> (PP+VOX):
    <strong style="color:#60A5FA">${pp26}</strong> +
    <strong style="color:#3FB950">${vox26}</strong> =
    <strong>${derecha}</strong>
    <span class="${derecha >= MAYORIA ? "gain" : "loss"}" style="margin-left:4px">
      (${derecha >= MAYORIA ? "+" : ""}${derecha - MAYORIA} vs mayoría ${MAYORIA})
    </span>
  </div>
  <div><strong>Bloque izquierda</strong> (PSOE+Izq.):
    <strong style="color:#F87171">${psoe26}</strong> +
    <strong style="color:#E879F9">${izq26}</strong> =
    <strong>${psoe26 + izq26}</strong>
  </div>`;
display(blocEl);
```

```js
// ── Tabs + tablas ─────────────────────────────────────────────────────────
const TIER_ORDER = { 'SEGURO':0,'MUY PROBABLE':1,'PROBABLE':2,'POSIBLE':3,'POCO PROBABLE':4 };

function buildRows(data, sortKey, sortDir) {
  const sorted = [...data].sort((a, b) => {
    let va, vb;
    if      (sortKey === 'diff') { va = a.s26 - a.s23; vb = b.s26 - b.s23; }
    else if (sortKey === 'conf') { va = TIER_ORDER[a.conf] ?? 5; vb = TIER_ORDER[b.conf] ?? 5; }
    else                         { va = a[sortKey]; vb = b[sortKey]; }
    if (typeof va === 'string') return sortDir * va.localeCompare(vb, 'es');
    return sortDir * (va - vb);
  });

  return sorted.map(r => {
    const cc  = CONF_CLASS[r.conf];
    const cf  = CONF_CELL[r.conf];
    const escStr = r.s23 === r.s26
      ? `<span class="same">${r.s26}</span>`
      : r.s26 > r.s23
        ? `<span class="gain">${r.s23}→${r.s26}</span>`
        : `<span class="loss">${r.s23}→${r.s26}</span>`;
    const gainCell = r.gain_from?.length
      ? r.gain_from.map(partyBadge).join(" ")
      : `<span style="opacity:.35">—</span>`;
    const fragCell = (r.s26 <= r.s23)
      ? `<span style="opacity:.35">—</span>`
      : (FRAG_LABEL[r.fragile] ?? "");
    const gapStr = r.gap > 0 ? `+${r.gap.toFixed(1)}pp` : `${r.gap.toFixed(1)}pp`;
    const filoNote = (r.fragile === 'filo' && r.s26 > r.s23)
      ? ` · ⚠ El último escaño ganado es AL FILO (el escaño actual se pierde con una bajada mínima)`
      : '';
    return `<tr>
      <td class="prov">${r.prov}</td>
      <td class="r">${r.esc}</td>
      <td class="r">${r.p19.toFixed(1)}%</td>
      <td class="r">${r.p23.toFixed(1)}%</td>
      <td class="r"><strong>${r.p26.toFixed(1)}%</strong></td>
      <td class="c">${fragCell}</td>
      <td class="r">${escStr}</td>
      <td class="wrap">${gainCell}</td>
      <td class="${cf.cls} col-conf" title="Gap al sig. escaño: ${gapStr} · Umbral: ${r.umbral.toFixed(1)}%${filoNote}"><span class="dots">${cf.dots}</span> ${cf.short}</td>
    </tr>`;
  }).join('');
}

function buildTable(data) {
  let sortKey = 'esc', sortDir = -1;
  const tot23 = data.reduce((s, r) => s + r.s23, 0);
  const tot26 = data.reduce((s, r) => s + r.s26, 0);
  const diff  = tot26 - tot23;
  const dStr  = diff > 0 ? `+${diff}` : `${diff}`;
  const dCls  = diff > 0 ? "gain" : diff < 0 ? "loss" : "same";

  const wrap = document.createElement('div');
  wrap.className = 'enc-table-wrap';
  wrap.innerHTML = `<table class="enc-table">
    <thead><tr>
      <th data-k="prov">Provincia</th>
      <th class="r" data-k="esc" data-dir="desc">Esc.</th>
      <th class="r col-pct" data-k="p19">2019%</th>
      <th class="r col-pct" data-k="p23">2023%</th>
      <th class="r col-pct" data-k="p26"><strong>2026 est%</strong></th>
      <th class="c" title="Solidez del cambio de escaños del swing model" style="min-width:88px">Swing / último esc.</th>
      <th class="r" data-k="diff">Esc 23→26</th>
      <th>Saca de</th>
      <th class="col-conf" data-k="gap" title="Distancia al umbral D'Hondt del siguiente escaño" style="min-width:150px">¿Cerca del sig.?</th>
    </tr></thead>
    <tbody>${buildRows(data, sortKey, sortDir)}</tbody>
    <tfoot><tr>
      <td colspan="5" style="font-size:.79rem;opacity:.6">TOTAL 52 PROVINCIAS</td>
      <td></td>
      <td class="r">
        <span class="${dCls}">${tot23}→${tot26}</span>
        <span class="${dCls}" style="font-size:.74rem;margin-left:4px">(${dStr})</span>
      </td>
      <td colspan="2"></td>
    </tr></tfoot>
  </table>`;

  wrap.querySelectorAll('thead th[data-k]').forEach(th => {
    th.addEventListener('click', () => {
      if (sortKey === th.dataset.k) {
        sortDir *= -1;
      } else {
        sortKey = th.dataset.k;
        sortDir = (sortKey === 'prov' || sortKey === 'conf') ? 1 : -1;
      }
      wrap.querySelectorAll('thead th[data-k]').forEach(t => {
        t.dataset.dir = (t.dataset.k === sortKey) ? (sortDir > 0 ? 'asc' : 'desc') : '';
      });
      wrap.querySelector('tbody').innerHTML = buildRows(data, sortKey, sortDir);
    });
  });

  return wrap;
}

function buildSummaryLine(party, data) {
  const s = summaries[party.key];
  const diff = s.seats26 - s.seats23;
  const dStr = diff > 0 ? `+${diff}` : `${diff}`;
  const dCls = diff > 0 ? "gain" : diff < 0 ? "loss" : "same";
  const tiers = {};
  data.forEach(r => { tiers[r.conf] = (tiers[r.conf] || 0) + 1; });
  // Factor swing nacional: pct26 / pct23 (media ponderada implícita en el modelo)
  const avgP23 = data.reduce((a, r) => a + r.p23, 0) / data.length;
  const avgP26 = data.reduce((a, r) => a + r.p26, 0) / data.length;
  const factor = avgP23 > 0 ? (avgP26 / avgP23).toFixed(2) : "—";
  const factorCls = avgP26 >= avgP23 ? "gain" : "loss";
  const nearCount = (tiers["MUY PROBABLE"]||0) + (tiers["PROBABLE"]||0);
  const nearLabel = nearCount > 0
    ? ` · <span style="color:var(--theme-foreground);opacity:.75">${nearCount} prov. a menos de ±MoE del sig. escaño</span>`
    : '';
  return `<div class="section-summary">
    <strong style="color:${party.color}">${party.label}</strong> ·
    Estimación 2026: ${party.pct26}% ·
    Factor swing: <span class="${factorCls}">×${factor}</span> sobre 23J ·
    Escaños swing: <strong>${s.seats26}</strong>
    (<span class="${dCls}">${dStr}</span> vs 2023)${nearLabel}
  </div>`;
}

// Contenedor principal de tabs
const tabsNav  = document.createElement("nav");  tabsNav.className  = "party-tabs";
const tabsBody = document.createElement("div");

PARTIES.forEach((party, idx) => {
  // Botón de tab
  const btn = document.createElement("button");
  btn.className  = "tab-btn" + (idx === 0 ? " active" : "");
  btn.textContent = party.label;
  btn.dataset.party = party.key;
  if (idx === 0) btn.style.color = party.color;
  btn.onclick = () => {
    tabsNav.querySelectorAll(".tab-btn").forEach(b => {
      const active = b.dataset.party === party.key;
      b.classList.toggle("active", active);
      b.style.color = active ? party.color : "";
    });
    tabsBody.querySelectorAll(".party-section").forEach(s => {
      s.classList.toggle("active", s.id === `ps-${party.key}`);
    });
  };
  tabsNav.appendChild(btn);

  // Sección
  const sec = document.createElement("div");
  sec.className = "party-section" + (idx === 0 ? " active" : "");
  sec.id = `ps-${party.key}`;
  sec.innerHTML = buildSummaryLine(party, allData[party.key]);
  sec.appendChild(buildTable(allData[party.key]));
  tabsBody.appendChild(sec);
});

display(tabsNav);
display(tabsBody);
```
