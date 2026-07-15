// Proxy same-origin para el tablero "Global & mercados" y las Noticias.
// Evita los problemas de CORS al pedir datos a FRED y Yahoo Finance (y a los
// feeds RSS) desde el servidor de Vercel en lugar del navegador.
//
// Uso:  /api/proxy?url=<URL https absoluta y codificada>
//
// Es un proxy con lista blanca de hosts (no un proxy abierto): solo reenvía a
// las fuentes que el sitio realmente consume. Cachea la respuesta en el borde
// de Vercel para no golpear las fuentes en cada visita.

const ALLOWED_HOST_SUFFIXES = [
  "stlouisfed.org",       // FRED (fredgraph.csv)
  "finance.yahoo.com",    // Yahoo Finance (chart API)
  "diariolibre.com",      // Noticias
  "eldinero.com.do",      // Noticias
  "bancentral.gov.do",    // Noticias BCRD
  "bloomberglinea.com",   // Noticias
  "news.google.com"       // Agregador de noticias
];

function hostAllowed(hostname) {
  const h = String(hostname || "").toLowerCase();
  return ALLOWED_HOST_SUFFIXES.some(s => h === s || h.endsWith("." + s));
}

module.exports = async function handler(req, res) {
  let target = req.query && req.query.url;
  // Si el runtime no parsea la query, la extraemos de la URL cruda.
  if (!target && req.url) {
    try { target = new URL(req.url, "http://localhost").searchParams.get("url"); } catch (e) {}
  }

  res.setHeader("Access-Control-Allow-Origin", "*");

  if (!target || typeof target !== "string" || !/^https:\/\//i.test(target)) {
    res.status(400).send("Parámetro 'url' inválido (se requiere https://).");
    return;
  }

  let parsed;
  try { parsed = new URL(target); }
  catch (e) { res.status(400).send("URL malformada."); return; }

  if (!hostAllowed(parsed.hostname)) {
    res.status(403).send("Host no permitido: " + parsed.hostname);
    return;
  }

  try {
    const upstream = await fetch(target, {
      headers: {
        // Algunas fuentes rechazan peticiones sin User-Agent de navegador.
        "User-Agent": "Mozilla/5.0 (compatible; ClubEconomistasBot/1.0)",
        "Accept": "text/csv,application/json,application/xml,text/xml,*/*"
      }
    });

    const body = await upstream.text();
    const ct = upstream.headers.get("content-type") || "text/plain; charset=utf-8";

    res.setHeader("Content-Type", ct);
    // Cache en el borde: 30 min fresco, 1 día sirviendo stale mientras revalida.
    res.setHeader("Cache-Control", "public, max-age=1800, s-maxage=1800, stale-while-revalidate=86400");
    res.status(upstream.status).send(body);
  } catch (e) {
    res.status(502).send("Error del proxy: " + (e && e.message ? e.message : "desconocido"));
  }
}
