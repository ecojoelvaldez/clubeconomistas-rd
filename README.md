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

- **Dominicana** (13 indicadores, se leen del master local en `data/series/`):
  IMAE, PIB nominal, ocupados, inflación subyacente, TPM, tasa activa, tipo de cambio,
  reservas, remesas, cuenta corriente, turismo, deuda/PIB y recaudación DGII.
- **Global & mercados** (10 indicadores, se cargan **en vivo** desde el navegador):
  Fed Funds, Treasury 10a, pendiente 10a−2a, inflación de EE.UU. y VIX/dólar/WTI vía
  **FRED** (`fredgraph.csv`, sin API key); oro, S&P 500 y Bitcoin vía **Yahoo Finance**.

Cada indicador declara su `load` (`kind: local | fred | yahoo`), su formato (`fmt`),
su signo semántico (`sign`) y transformaciones opcionales (`scale`, `aggregate`,
`transform: "yoy"`). Los cargadores viven en `loadLocalPoints` / `loadFredPoints` /
`loadYahooPoints`; los datos externos usan el mismo proxy CORS (`fetchTextWithCors`)
que las Noticias, con estados de carga y error si la fuente no responde. Series largas
se reducen (downsample) a ~220 puntos para render fluido.

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
