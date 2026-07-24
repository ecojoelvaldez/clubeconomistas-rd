# Tarea — Modelos VAR y SVAR aplicados al mercado laboral de la República Dominicana

Econometría de Series de Tiempo. Estimación de un VAR y su contraparte estructural
(SVAR) para la dinámica del mercado laboral dominicano con **datos trimestrales del
BCRD, 2018Q1–2025Q4**, tomados del master de datos público del Club
(`data/series/*.json`).

La tarea se entrega **resuelta para dos estudiantes**, cada uno con una
especificación propia (ordenamiento de identificación, criterio de rezagos y variable
de robustez distintos), pero sobre los mismos datos reales:

| Carpeta | Estudiante | Ordenamiento SVAR | Rezago (criterio) | Robustez |
|---|---|---|---|---|
| `joel-valdez/` | Joel Valdez | base de la consigna (actividad → precios → salarios → empleo → desempleo) | p=1 (AIC) | + TPM |
| `robert-cueto/` | Robert Cueto | alternativo bloque real-primero (actividad → empleo → desempleo → salarios → precios) | p=1 (BIC) | + Remesas |

Cada carpeta contiene los cuatro anexos exigidos:

```
<estudiante>/
  informe.pdf              # Informe técnico (portada + 14 secciones)
  analisis_var_svar.R      # Código reproducible en R (vars / urca / svars)
  data/
    panel_trimestral.csv   # Base de datos utilizada
    README_datos.md        # Origen de cada serie y notas de medición
    build_panel.py         # Reconstrucción del panel desde el master
  figuras/                 # Todas las figuras generadas (8 PNG)
```

## Datos (todos reales del BCRD salvo el salario)

| Variable | Serie del master | ID |
|---|---|---|
| Actividad real (proxy PIB) | IMAE base 2018 | CE-SER-2026-0039 |
| Ocupados / PEA / Desocupados | PET total (ENCFT) | CE-SER-2026-0014 |
| IPC | Costo de la canasta nacional | CE-SER-2026-0029 |
| TPM | Tasa de política monetaria | CE-SER-2026-0032 |
| Remesas | Remesas familiares | CE-SER-2026-0037 |

> **Nota:** el master no contiene un índice de salarios del BCRD. El salario real es
> un **proxy reconstruido** del ingreso laboral real (concepto ENCFT), calibrado a los
> hechos estilizados publicados, y **debe sustituirse por el ingreso laboral de la
> ENCFT** en una entrega final. Ver `*/data/README_datos.md`. El código está armado
> para que solo haya que reemplazar esa columna.

## Reproducir

El análisis se ejecutó en Python (statsmodels) para generar figuras y resultados,
y se entrega además el script R exigido por la consigna. Para regenerar todo:

```bash
cd scripts
python3 build_all.py ../salida      # panel + análisis + R + PDF de ambos estudiantes
```

Dependencias Python: `numpy pandas matplotlib statsmodels reportlab`.
Dependencias R (para `analisis_var_svar.R`): `vars urca tseries svars ggplot2 zoo`.

## Identificación

SVAR por **restricciones contemporáneas de corto plazo** (modelo AB con A triangular
inferior de diagonal unitaria y B diagonal ≡ descomposición de Cholesky sobre el
ordenamiento). Se reportan pruebas ADF, selección de rezagos (AIC/BIC/HQ/FPE),
diagnóstico (estabilidad, Portmanteau, normalidad, ARCH), IRF con bandas *bootstrap*,
FEVD a 4/8/12 trimestres y las series de choques estructurales recuperados.
