#!/usr/bin/env node
// Descarga indicadores del sistema financiero desde la API de la Superintendencia
// de Bancos (SIB) y los guarda como snapshots JSON en data/series/, con el mismo
// formato que el master ({ meta, observations }) para que el sitio los lea como
// cualquier otra serie local.
//
// La CLAVE de la API nunca se hardcodea: se lee de la variable de entorno
// SIB_API_KEY (el GitHub secret) y se envía en la cabecera definida en
// scripts/sib-sources.json ("authHeader", por defecto Ocp-Apim-Subscription-Key).
//
// Diseño defensivo: si un endpoint falla o no está configurado, se registra y se
// omite ese indicador SIN romper el resto ni el workflow. Al primer fallo de forma
// imprime una muestra de la respuesta cruda para poder ajustar dateKey/valueKey.
//
// Uso:  SIB_API_KEY=xxxx node scripts/fetch-sib.mjs

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const OUT_DIR = path.join(ROOT, "data", "series");
const CONFIG = JSON.parse(fs.readFileSync(path.join(__dirname, "sib-sources.json"), "utf8"));

const API_KEY = process.env.SIB_API_KEY || "";
const BASE = process.env.SIB_API_BASE || CONFIG.base;
const AUTH_HEADER = process.env.SIB_AUTH_HEADER || CONFIG.authHeader || "Ocp-Apim-Subscription-Key";

// Meses en español → número, para normalizar fechas tipo "ene-2024".
const MES = { ene: 1, feb: 2, mar: 3, abr: 4, may: 5, jun: 6, jul: 7, ago: 8, sep: 9, set: 9, oct: 10, nov: 11, dic: 12 };

function toIsoMonth(raw) {
  if (raw == null) return null;
  const s = String(raw).trim();
  let m;
  if ((m = s.match(/^(\d{4})[-/](\d{1,2})(?:[-/](\d{1,2}))?/))) {
    const day = m[3] ? m[3].padStart(2, "0") : "01";
    return `${m[1]}-${m[2].padStart(2, "0")}-${day}`;
  }
  if ((m = s.match(/^([a-zA-Z]{3})\w*[-/ ](\d{4})$/))) {
    const mo = MES[m[1].toLowerCase().slice(0, 3)];
    if (mo) return `${m[2]}-${String(mo).padStart(2, "0")}-01`;
  }
  if ((m = s.match(/^(\d{4})(\d{2})$/))) return `${m[1]}-${m[2]}-01`;
  const d = new Date(s);
  if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10);
  return null;
}

// Encuentra el arreglo de datos dentro de respuestas con distintas envolturas.
function pickArray(json) {
  if (Array.isArray(json)) return json;
  for (const k of ["data", "value", "result", "results", "items", "datos", "records", "Table", "response"]) {
    if (json && Array.isArray(json[k])) return json[k];
  }
  // A veces viene anidado un nivel más (p. ej. { data: { items: [...] } }).
  if (json && typeof json === "object") {
    for (const v of Object.values(json)) {
      if (Array.isArray(v)) return v;
      if (v && typeof v === "object") {
        const inner = pickArray(v);
        if (inner.length) return inner;
      }
    }
  }
  return [];
}

function getField(obj, key) {
  if (obj == null) return undefined;
  if (key in obj) return obj[key];
  // match case-insensitive por si el API usa otra capitalización
  const lk = String(key).toLowerCase();
  for (const k of Object.keys(obj)) if (k.toLowerCase() === lk) return obj[k];
  return undefined;
}

async function fetchIndicator(ind) {
  if (!ind.path) {
    console.log(`· [${ind.file}] sin 'path' configurado → omitido (edita scripts/sib-sources.json).`);
    return null;
  }
  const url = new URL(BASE.replace(/\/$/, "") + ind.path);
  for (const [k, v] of Object.entries(ind.query || {})) url.searchParams.set(k, v);

  const headers = { "Accept": "application/json" };
  if (API_KEY) headers[AUTH_HEADER] = API_KEY;

  const res = await fetch(url, { headers });
  const text = await res.text();
  if (!res.ok) {
    console.error(`✗ [${ind.file}] HTTP ${res.status} en ${url.pathname}. Muestra: ${text.slice(0, 240)}`);
    return null;
  }

  let json;
  try { json = JSON.parse(text); }
  catch (e) { console.error(`✗ [${ind.file}] respuesta no-JSON. Muestra: ${text.slice(0, 240)}`); return null; }

  const rows = pickArray(json);
  if (!rows.length) {
    console.error(`✗ [${ind.file}] no encontré un arreglo de datos. Estructura: ${JSON.stringify(json).slice(0, 300)}`);
    return null;
  }

  const scale = ind.scale == null ? 1 : ind.scale;
  const obs = [];
  for (const r of rows) {
    const iso = toIsoMonth(getField(r, ind.dateKey));
    const rawVal = getField(r, ind.valueKey);
    const val = typeof rawVal === "string" ? parseFloat(rawVal.replace(/,/g, "")) : rawVal;
    if (iso == null || val == null || isNaN(val)) continue;
    obs.push({ date: iso, value: val * scale, variable: "valor", period: iso.slice(0, 7) });
  }
  obs.sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));

  if (!obs.length) {
    console.error(`✗ [${ind.file}] 0 observaciones tras parsear. Revisa dateKey='${ind.dateKey}' / valueKey='${ind.valueKey}'. Ejemplo de fila: ${JSON.stringify(rows[0]).slice(0, 300)}`);
    return null;
  }

  return {
    meta: {
      id: ind.file,
      nombre: ind.nombre,
      fuente: "SIB",
      frecuencia: "mensual",
      unidad: ind.unidad || "percent",
      variables: ["valor"],
      start_date: obs[0].date,
      end_date: obs[obs.length - 1].date,
      observations: obs.length,
      updated_at: new Date().toISOString()
    },
    observations: obs
  };
}

async function main() {
  if (!API_KEY) console.warn("⚠ SIB_API_KEY no está definido; se intentará sin autenticación (probablemente falle).");
  fs.mkdirSync(OUT_DIR, { recursive: true });

  let ok = 0, skipped = 0;
  for (const ind of CONFIG.indicators) {
    try {
      const snap = await fetchIndicator(ind);
      if (!snap) { skipped++; continue; }
      const fp = path.join(OUT_DIR, ind.file + ".json");
      fs.writeFileSync(fp, JSON.stringify(snap));
      console.log(`✓ [${ind.file}] ${snap.observations.length} obs · ${snap.meta.start_date} → ${snap.meta.end_date}`);
      ok++;
    } catch (e) {
      console.error(`✗ [${ind.file}] error: ${e.message}`);
      skipped++;
    }
  }
  console.log(`\nHecho. ${ok} actualizados, ${skipped} omitidos.`);
  // No fallamos el workflow por indicadores omitidos: el objetivo es actualizar
  // lo que se pueda sin romper el sitio ni la Action.
}

main().catch(e => { console.error("Error fatal:", e); process.exit(1); });
