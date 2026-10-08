export default {
  title: "Las elecciones generales de España",
  favicon: "🗳️",
  root: "src",
  output: "dist",
  theme: ["air", "near-midnight"],
  header: `<div style="display:flex;align-items:center;gap:12px;padding:4px 0">
    <span style="font-weight:700;font-size:1.1em">Las elecciones generales de España</span>
    <span style="opacity:.5;font-size:.85em">Elecciones Generales 1977 – 2023</span>
  </div>`,
  footer: "Fuente: Ministerio del Interior — Infoelectoral. Cálculo D'Hondt propio.",
  pages: [
    { name: "Porra provincial 29-N",      path: "/estimador" },
    { name: "Mapa Electoral histórico",   path: "/" },
    { name: "Barrera electoral",          path: "/evolucion" },
    { name: "Bloques ideológicos",        path: "/bloques" },
    { name: "¿Y si hubieran ido juntos?", path: "/simulador" },
  ],
};
