# Club Economistas — MVP de Estadísticas

Sitio estático (React + Recharts vía CDN) conectado al master de datos público del Club.

## Estructura
```
index.html            # App completa (una sola página)
vercel.json           # Headers de cache para /data
data/
  series_catalog.json # Catálogo ligero de las 57 series
  catalog_*.json      # Catálogo por institución
  series/CE-SER-2026-XXXX.json  # Observaciones, cargadas bajo demanda
```

## La sección Estadísticas es curada, no un catálogo plano
No expone las 57 series crudas del master. Presenta una **curaduría** definida en
la constante `CURATED` dentro de `index.html`: pocos indicadores —los que de verdad
mueven la economía— agrupados por tema y presentados con contexto editorial, lectura
formateada (con su unidad real) y enlace a la fuente. Se organiza en dos paneles:

- **Dominicana** (indicadores del master local + fiscales del FMI en vivo):
  IMAE, PIB nominal, ocupados, inflación subyacente, TPM, tasa activa, tipo de cambio,
  reservas, remesas, cuenta corriente, turismo, deuda/PIB, recaudación DGII y emisiones
  de renta fija en RD$ (SIMV / mercado de valores) desde el master; más balance fiscal,
  ingresos y gasto del gobierno (% del PIB) desde el **FMI · DataMapper (WEO)** en vivo.
- **Global & mercados** (10 indicadores, se cargan **en vivo** desde el navegador):
  Fed Funds, Treasury 10a, pendiente 10a−2a, inflación de EE.UU., WTI, índice del dólar,
  VIX, S&P 500 y Bitcoin vía **FRED** (`fredgraph.csv`, sin API key); oro vía
  **Yahoo Finance** (`chart` API).

Cada indicador declara su `load` (`kind: local | fred | yahoo | imf`), su formato
(`fmt`), su signo semántico (`sign`) y transformaciones opcionales (`scale`,
`aggregate`, `where`, `transform: "yoy"`). Los cargadores viven en `loadLocalPoints`
/ `loadFredPoints` / `loadYahooPoints` / `loadImfPoints` (el del FMI recorta las
proyecciones WEO a futuro para no mostrar un pronóstico como dato). Series largas se
reducen (downsample) a ~220 puntos.

### Cómo se resuelve el CORS de los datos globales
FRED y Yahoo no envían cabeceras CORS abiertas, así que el fetch directo falla en el
navegador. `fetchTextWithCors` (compartido con las Noticias) intenta, en orden:
1. **directo**;
2. **`/api/proxy`** — función serverless de Vercel (`api/proxy.js`) que hace la
   petición desde el servidor (sin CORS) con lista blanca de hosts y cache en el borde;
3. varios **proxies CORS públicos** (corsproxy.io, codetabs, allorigins) como respaldo
   para despliegues sin serverless (GitHub Pages).

En Vercel, el paso 2 resuelve todo de forma fiable. Si ninguna vía responde, el
indicador muestra un estado de error claro en lugar de romperse.

El master crudo sigue disponible en `data/` (57 series) como respaldo del panel
Dominicana; no se muestra como catálogo.

## Desplegar en Vercel
- Sube esta carpeta a un repo de GitHub.
- En Vercel: New Project → importa el repo → Framework Preset: **Other** → Deploy.
- No requiere build. Output directory: la raíz (`.`).

## Desplegar en GitHub Pages
- Settings → Pages → Source: Deploy from branch → `main` / root.
- Las rutas son relativas, así que funciona bajo subdirectorio sin cambios.

## Fuentes
- **Master local** (`data/series/`): BCRD, Hacienda y Economía, SIMV, DGII.
- **En vivo desde el navegador**: FRED (Reserva Federal de St. Louis) y Yahoo Finance.
