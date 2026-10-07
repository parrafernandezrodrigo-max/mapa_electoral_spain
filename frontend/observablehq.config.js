export default {
  title: "Mapa Electoral España",
  favicon: "🗳️",
  root: "src",
  output: "dist",
  theme: ["air", "near-midnight"],
  header: `<div style="display:flex;align-items:center;gap:12px;padding:4px 0">
    <span style="font-weight:700;font-size:1.1em">Mapa Electoral España</span>
    <span style="opacity:.5;font-size:.85em">Elecciones Generales 1977 – 2023</span>
  </div>`,
  footer: "Fuente: Ministerio del Interior — Infoelectoral. Cálculo D'Hondt propio.",
  pages: [
    { name: "Mapa electoral",    path: "/" },
    { name: "Evolución barrera", path: "/evolucion" },
    { name: "Bloques ideológicos", path: "/bloques" },
    { name: "¿Y si hubieran ido juntos?", path: "/simulador" },
    { name: "Simulador electoral 2026",   path: "/pronostico" },
  ],
};
