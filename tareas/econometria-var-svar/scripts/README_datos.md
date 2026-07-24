# Base de datos — VAR/SVAR del mercado laboral dominicano

Panel **trimestral 2016Q1–2025Q4** (`panel_trimestral.csv`), 40 observaciones, con
datos del BCRD (cuentas nacionales, ENCFT e IPC). El panel base se provee en
`panel_usuario.csv`; `build_panel.py` lo normaliza y le añade las remesas del master
del Club para el ejercicio de robustez.

## Columnas de `panel_trimestral.csv`

| Columna | Contenido | Fuente |
|---|---|---|
| `imae` | Índice de PIB real desestacionalizado | BCRD, cuentas nacionales |
| `ocupados` | Ocupados (personas) | BCRD, ENCFT |
| `tasa_deso` | Tasa de desocupación (%) | BCRD, ENCFT |
| `ipc` | IPC (índice, promedio trimestral) | BCRD |
| `salario_hora` / `sal_nom_idx` | Salario nominal por hora (RD$) | BCRD, ENCFT |
| `sal_real_idx` | Índice de salario real = `salario_hora / ipc × 100` | derivada |
| `tpm` | Tasa de política monetaria (%) | BCRD |
| `remesas` | Remesas familiares (suma trimestral, USD) | master del Club, CE-SER-2026-0037 |
| `lpib, locu, lipc, lsalnom, lsalreal` | Transformaciones log | derivadas |

## Verificación de consistencia (hecha antes de estimar)

- `ocupados` y `tasa_deso` **coinciden exactamente** con las series de la ENCFT del
  master del Club (`CE-SER-2026-0014`) → mismo origen BCRD.
- Identidades internas del panel base: `inflacion_trimestral = Δlog(ipc)` y
  `salario_real = log(salario_hora) − log(ipc)` se cumplen (tolerancia 1e-4).
- Cobertura completa 2016Q1–2025Q4 sin valores faltantes.

## Nota

A diferencia de una versión preliminar, **el salario es un dato observado** (salario
por hora de la ENCFT), no un proxy reconstruido. El salario real muestra la
trayectoria esperada: mejora en 2016–2019, caída en 2020 y en el pico inflacionario
de 2021, y recuperación sostenida en 2022–2025.

## Reproducir el panel

```bash
python3 build_panel.py panel_trimestral.csv panel_usuario.csv
```

Requiere además `data/series/CE-SER-2026-0037.json` del repositorio
`clubeconomistas-rd` para la columna de remesas.
