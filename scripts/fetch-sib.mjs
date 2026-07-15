#!/usr/bin/env node
// Descarga indicadores del sistema financiero desde la API de la Superintendencia
// de Bancos (SIB) —endpoint 'indicadores/financieros', formato long— y los guarda
// como snapshots JSON en data/series/, con el mismo formato que el master
// ({ meta, observations }) para que el sitio los lea como cualquier serie local.
//
// La CLAVE de la API nunca se hardcodea: se lee de SIB_SUBSCRIPTION_KEY (el GitHub
// secret) y se envía en la cabecera authHeader (Ocp-Apim-Subscription-Key).
//
// Fuente de las filas, por orden de prioridad:
//   1. SIB_API_BASE definido  → GET {SIB_API_BASE}/{endpoint} con la clave.
//   2. SIB_SNAPSHOT_URL       → descarga ese JSON (snapshot del observatorio).
//   3. si no                  → lee el snapshot local (source.localSnapshot).
//
// De cada fuente se toman las filas { periodo, entidad, tipo_entidad, indicador,
// valor }, se filtran por 'filter' (entidad=TODOS, tipo_entidad=BM) y por el
// 'indicador' de cada serie, y se escribe data/series/<file>.json.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const OUT_DIR = path.join(ROOT, "data", "series");
const CONFIG = JSON.parse(fs.readFileSync(path.join(__dirname, "sib-sources.json"), "utf8"));

const API_KEY = process.env.SIB_SUBSCRIPTION_KEY || process.env.SIB_API_KEY || "";
const API_BASE = process.env.SIB_API_BASE || "";
const SNAPSHOT_URL = process.env.SIB_SNAPSHOT_URL || "";
const SRC = CONFIG.source || {};
const AUTH_HEADER = process.env.SIB_AUTH_HEADER || SRC.authHeader || "Ocp-Apim-Subscription-Key";

// Encuentra el arreglo de filas dentro de respuestas con distintas envolturas.
function pickRows(json) {
  if (Array.isArray(json)) return json;
  for (const k of ["rows", "data", "value", "result", "results", "items", "datos", "records"]) {
    if (json && Array.isArray(json[k])) return json[k];
  }
  if (json && typeof json === "object") {
    for (const v of Object.values(json)) {
      if (Array.isArray(v)) return v;
      if (v && typeof v === "object") { const inner = pickRows(v); if (inner.length) return inner; }
    }
  }
  return [];
}

function periodoToIso(p) {
  const s = String(p || "").trim();
  let m;
  if ((m = s.match(/^(\d{4})[-/](\d{1,2})/))) return `${m[1]}-${m[2].padStart(2, "0")}-01`;
  if ((m = s.match(/^(\d{4})(\d{2})$/))) return `${m[1]}-${m[2]}-01`;
  const d = new Date(s);
  return isNaN(d.getTime()) ? null : d.toISOString().slice(0, 10);
}

async function loadRows() {
  if (API_BASE) {
    const url = API_BASE.replace(/\/$/, "") + "/" + String(SRC.endpoint || "").replace(/^\//, "");
    const headers = { Accept: "application/json" };
    if (API_KEY) headers[AUTH_HEADER] = API_KEY;
    console.log(`→ API SIB: ${url}`);
    const res = await fetch(url, { headers });
    const text = await res.text();
    if (!res.ok) throw new Error(`HTTP ${res.status} de la API SIB. Muestra: ${text.slice(0, 240)}`);
    return pickRows(JSON.parse(text));
  }
  if (SNAPSHOT_URL) {
    console.log(`→ snapshot remoto: ${SNAPSHOT_URL}`);
    const res = await fetch(SNAPSHOT_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status} al bajar el snapshot remoto`);
    return pickRows(await res.json());
  }
  const local = path.join(ROOT, SRC.localSnapshot || "data/sib_snapshot.json");
  console.log(`→ snapshot local: ${path.relative(ROOT, local)}`);
  return pickRows(JSON.parse(fs.readFileSync(local, "utf8")));
}

function buildSeries(rows, ind, filter) {
  const obs = [];
  for (const r of rows) {
    if (r.indicador !== ind.indicador) continue;
    if (filter.entidad != null && r.entidad !== filter.entidad) continue;
    if (filter.tipo_entidad != null && r.tipo_entidad !== filter.tipo_entidad) continue;
    const iso = periodoToIso(r.periodo);
    const raw = typeof r.valor === "string" ? parseFloat(r.valor.replace(/,/g, "")) : r.valor;
    if (iso == null || raw == null || isNaN(raw)) continue;
    obs.push({ date: iso, value: raw * (ind.scale == null ? 1 : ind.scale), variable: "valor", period: iso.slice(0, 7) });
  }
  obs.sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
  return obs;
}

async function main() {
  if (API_BASE && !API_KEY) console.warn("⚠ SIB_API_BASE definido pero SIB_SUBSCRIPTION_KEY vacío; la API probablemente rechace la petición.");
  fs.mkdirSync(OUT_DIR, { recursive: true });

  let rows;
  try { rows = await loadRows(); }
  catch (e) { console.error("✗ No se pudieron obtener las filas:", e.message); process.exit(1); }
  console.log(`Filas obtenidas: ${rows.length}`);

  const filter = CONFIG.filter || {};
  let ok = 0, skipped = 0;
  for (const ind of CONFIG.indicators) {
    const obs = buildSeries(rows, ind, filter);
    if (!obs.length) {
      console.error(`✗ [${ind.file}] 0 observaciones para indicador='${ind.indicador}' (${JSON.stringify(filter)}). ¿Cambió el nombre del indicador o el filtro?`);
      skipped++;
      continue;
    }
    const snap = {
      meta: {
        id: ind.file, nombre: ind.nombre, fuente: "SIB", frecuencia: "mensual",
        unidad: ind.unidad || "percent", variables: ["valor"],
        start_date: obs[0].date, end_date: obs[obs.length - 1].date,
        observations: obs.length, updated_at: new Date().toISOString()
      },
      observations: obs
    };
    fs.writeFileSync(path.join(OUT_DIR, ind.file + ".json"), JSON.stringify(snap));
    console.log(`✓ [${ind.file}] ${obs.length} obs · ${snap.meta.start_date} → ${snap.meta.end_date} · último=${obs[obs.length - 1].value}`);
    ok++;
  }
  console.log(`\nHecho. ${ok} actualizados, ${skipped} omitidos.`);
}

main().catch(e => { console.error("Error fatal:", e); process.exit(1); });
