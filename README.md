# Club Economistas — MVP de Estadísticas

Sitio estático (React + Recharts vía CDN) conectado al master de datos público del Club.

## Estructura
```
index.html            # App completa (una sola página)
vercel.json           # Headers de cache para /data
data/
  series_catalog.json # Catálogo ligero de las 57 series
  catalog_*.json      # Catálogo por institución
  papers_catalog.json # Repositorio de investigación (CEPAL)
  papers_bcrd_concurso.json  # Premios del Concurso de Economía BCRD
  series/CE-SER-2026-XXXX.json  # Observaciones, cargadas bajo demanda
scripts/
  build_bcrd_catalog.py  # Regenera papers_bcrd_concurso.json
```

## Investigación: premios del Concurso BCRD
`data/papers_bcrd_concurso.json` (63 entradas) recoge los trabajos premiados del
**Concurso Anual de Economía Biblioteca «Juan Pablo Duarte»** del Banco Central de la
República Dominicana y los volúmenes anuales de la serie *Nueva literatura económica
dominicana* que los compilan. No se aloja ningún PDF: cada entrada enlaza al documento
en el Repositorio Cultural del BCRD, al PDF del CDN institucional o a la colección
completa de la serie. Se regenera con `python3 scripts/build_bcrd_catalog.py`.

## Blog · Opiniones
Columnas firmadas por economistas invitados. Se publican desde **Panel admin →
Opiniones**: nombre, cargo, titular, bajada, artículo completo y una foto **PNG con
fondo transparente** (hasta 1.5 MB, guardada en base64 junto al artículo). Con Supabase
activo se guardan en la tabla `club_opiniones`; sin backend quedan en `localStorage`.

```sql
create table club_opiniones (
  id text primary key,
  author text not null,
  role text,
  title text not null,
  standfirst text,
  body text,
  photo text,
  published_at timestamptz default now(),
  created_at timestamptz default now()
);
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

La **franja de indicadores** (ticker) no lleva cifras escritas a mano: lee el último
dato publicado de ocho indicadores (`TICKER_KEYS`) con el mismo cargador de
Estadísticas y calcula la variación contra la observación anterior. Los campos del
editor del sitio quedan solo como respaldo si esa carga falla.

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
