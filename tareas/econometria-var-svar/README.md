# Tarea — Modelos VAR y SVAR aplicados al mercado laboral de la República Dominicana

Econometría de Series de Tiempo. Estimación de un VAR y su contraparte estructural
(SVAR) para la dinámica del mercado laboral dominicano con **datos trimestrales del
BCRD, 2016Q1–2025Q4** (cuentas nacionales, ENCFT e IPC). Ocupados y tasa de
desocupación coinciden con las series del master del Club (`CE-SER-2026-0014`); el
salario es dato observado (salario por hora de la ENCFT).

La tarea se entrega **resuelta para dos estudiantes**, cada uno con una
especificación propia (ordenamiento de identificación, número de rezagos y variable
de robustez distintos), pero sobre los mismos datos reales:

| Carpeta | Estudiante | Ordenamiento SVAR | Rezago (criterio) | Robustez |
|---|---|---|---|---|
| `joel-valdez/` | Joel Valdez | base de la consigna (actividad → precios → salarios → empleo → desempleo) | p=2 (AIC) | + TPM |
| `robert-cueto/` | Robert Cueto | alternativo (actividad → precios → empleo → salario real → desempleo) | p=1 (BIC) | + Remesas |

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

## Datos (BCRD, 2016Q1–2025Q4)

| Variable | Contenido | Fuente |
|---|---|---|
| Actividad real (PIB) | Índice de PIB desestacionalizado | BCRD, cuentas nacionales |
| Ocupados / Desocupados | ENCFT (coinciden con `CE-SER-2026-0014`) | BCRD, ENCFT |
| IPC | Índice de precios al consumidor | BCRD |
| Salario nominal / real | Salario por hora (RD$) y su deflactado | BCRD, ENCFT |
| TPM | Tasa de política monetaria | BCRD |
| Remesas | Remesas familiares (`CE-SER-2026-0037`) | master del Club |

> El panel base se provee en `*/data/panel_usuario.csv`; se verificó su consistencia
> (ocupados y desempleo idénticos a la ENCFT del master; identidades internas
> `inflación = Δlog IPC` y `salario real = log(salario) − log(IPC)`). El **salario es
> dato observado**, no un proxy. Ver `*/data/README_datos.md`.

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
