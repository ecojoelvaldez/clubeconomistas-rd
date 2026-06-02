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

## Cómo carga la sección Estadísticas
1. Al abrir, hace `fetch("data/series_catalog.json")`.
2. Al elegir institución, filtra el catálogo por `fuente`.
3. Al elegir una serie, hace `fetch("data/series/<id>.json")`.
4. Si la serie tiene varias `variables`, aparece un selector; la gráfica pivotea por variable.
5. Series largas se reducen (downsample) a ~220 puntos para render fluido.

## Desplegar en Vercel
- Sube esta carpeta a un repo de GitHub.
- En Vercel: New Project → importa el repo → Framework Preset: **Other** → Deploy.
- No requiere build. Output directory: la raíz (`.`).

## Desplegar en GitHub Pages
- Settings → Pages → Source: Deploy from branch → `main` / root.
- Las rutas son relativas, así que funciona bajo subdirectorio sin cambios.

## Instituciones con datos
BCRD (48 series), Hacienda y Economía (4), SIMV (3), DGII (2).
BVRD y FRED quedan como placeholders hasta cargar sus series.
