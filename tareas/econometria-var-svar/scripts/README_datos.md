# Base de datos — VAR/SVAR del mercado laboral dominicano

Panel **trimestral 2018Q1–2025Q4** (`panel_trimestral.csv`) construido a partir del
master de datos público del Club de Economistas Dominicanos
(`data/series/*.json`, repositorio `clubeconomistas-rd`). Salvo el salario, **todas
las series son datos reales del BCRD**.

## Origen de cada columna

| Columna | Serie del master | ID | Frecuencia origen | Tratamiento |
|---|---|---|---|---|
| `imae` | IMAE base 2018 (Serie Original, Índice) | CE-SER-2026-0039 | mensual | promedio trimestral |
| `ocupados` | PET total — Ocupados | CE-SER-2026-0014 | trimestral | directo |
| `pea` | PET total — Fuerza de Trabajo (PEA) | CE-SER-2026-0014 | trimestral | directo |
| `desocupados` | PET total — Desocupados | CE-SER-2026-0014 | trimestral | directo |
| `tasa_deso` | derivada | — | trimestral | `desocupados/pea*100` |
| `ipc` | Costo de la canasta nacional (base 2019-2020) | CE-SER-2026-0029 | mensual | promedio trimestral |
| `tpm` | Tasa de política monetaria | CE-SER-2026-0032 | mensual | promedio trimestral (×100 → %) |
| `remesas` | Remesas familiares recibidas | CE-SER-2026-0037 | mensual | suma trimestral (USD) |
| `sal_real_idx` | **proxy reconstruido** (ver abajo) | — | trimestral | índice, base 2016Q1=100 |
| `sal_nom_idx` | derivada | — | trimestral | `sal_real_idx * ipc/100` |

Columnas de transformación incluidas por conveniencia: `lpib=log(imae)`,
`locu=log(ocupados)`, `lipc=log(ipc)`, `lsalnom`, `lsalreal`.

## Decisiones de medición

- **Actividad real (PIB).** Se usa el **IMAE**, indicador mensual que el propio BCRD
  emplea como aproximación de alta frecuencia del PIB. El PIB trimestral encadenado
  (CE-SER-2026-0043/0047) solo cubre desde 2018 y mezcla en el master niveles con
  tasas de crecimiento, por lo que el IMAE es la opción limpia y de mayor cobertura.
- **IPC.** El IPC subyacente del master (0028) solo tiene frecuencia **anual**. Se
  aproxima con el **costo de la canasta nacional** (0029), mensual, cuya variación
  interanual reproduce con fidelidad la inflación *headline* del BCRD (≈8 % en 2021,
  ≈9 % en el pico de 2022, ≈3,3 % en 2024). Esto fija el inicio efectivo del panel en
  **2018Q1**.
- **Desempleo.** La tasa de desocupación se deriva de la ENCFT (0014) como
  `Desocupados / PEA`.

## ⚠️ Serie de salario — proxy reconstruido (única serie no observada)

El master del Club **no contiene** un índice de salarios ni de ingreso laboral del
BCRD. La columna `sal_real_idx` es un **índice ilustrativo reconstruido** del ingreso
laboral real promedio de los ocupados (concepto ENCFT), con una trayectoria suave y
determinista (sin ruido aleatorio) calibrada a los hechos estilizados publicados por
el BCRD:

- 2018–2019: estable, con leve mejora (recuperación sostenida);
- 2020: caída por el choque de la pandemia;
- 2021–2022: erosión por el choque inflacionario mundial;
- 2023–2025: recuperación gradual del salario real.

**Para una entrega final debe sustituirse por el `Ingreso laboral promedio` (nominal
o real) de la ENCFT del BCRD.** El código (`build_panel.py` y `analisis_var_svar.R`)
está estructurado para que solo haya que reemplazar esta columna: las demás variables
y todo el flujo de estimación permanecen iguales.

## Reproducir el panel

```bash
python3 build_panel.py panel_trimestral.csv
```

Requiere `data/series/*.json` del repositorio `clubeconomistas-rd`.
