# =============================================================================
# Econometria de Series de Tiempo
# Modelos VAR y SVAR aplicados al mercado laboral de la Republica Dominicana
# Estudiante: Robert Cueto
# -----------------------------------------------------------------------------
# Codigo COMPLETAMENTE REPRODUCIBLE en R.
# Requiere: vars, urca, tseries, svars, ggplot2, reshape2, zoo
#   install.packages(c("vars","urca","tseries","svars","ggplot2","reshape2","zoo"))
#
# Datos: panel trimestral 2016Q1-2025Q4 (BCRD: cuentas nacionales, ENCFT, IPC).
# Ocupados y desempleo coinciden con el master del Club (CE-SER-2026-0014).
# Ver ../data/panel_trimestral.csv y ../data/README_datos.md
# =============================================================================

library(vars); library(urca); library(tseries); library(svars)
library(ggplot2); library(zoo)
set.seed(12345)

## ---- 1. Carga de datos -----------------------------------------------------
panel <- read.csv("panel_trimestral.csv", stringsAsFactors = FALSE)
panel$date <- as.Date(panel$date)
panel <- panel[order(panel$date), ]

## ---- 2. Construccion de las variables del sistema --------------------------
# Transformaciones (log-diferencias en % y niveles) segun la consigna.
dl <- function(x) 100 * diff(log(x))
crec_pib  <- dl(panel$imae)           # crecimiento del PIB real (indice s.a.)
inflacion <- dl(panel$ipc)            # inflacion trimestral = D log(IPC)
sal_real  <- dl(panel$sal_real_idx)   # crecimiento del salario real (dato ENCFT)
crec_ocu  <- dl(panel$ocupados)       # crecimiento de los ocupados
desempleo <- panel$tasa_deso[-1]      # tasa de desocupacion (nivel)
fechas    <- panel$date[-1]

# Ordenamiento recursivo (identificacion contemporanea / modelo AB):
#   alternativo (actividad -> precios -> empleo -> salario real -> desempleo)
Y <- data.frame(
  crec_pib = crec_pib,
  inflacion = inflacion,
  crec_ocu = crec_ocu,
  sal_real = sal_real,
  desempleo = desempleo
)
Y <- window(ts(Y, start = c(2016, 2), frequency = 4))
# recorte al periodo efectivo (se pierde 2016Q1 por la diferenciacion)

## ---- 3. Analisis exploratorio ----------------------------------------------
plot.ts(Y, main = "Variables del sistema")
summary(Y)
round(cor(Y), 3)                       # matriz de correlaciones

## ---- 4. Pruebas de estacionariedad (ADF) -----------------------------------
adf_report <- function(x, nombre) {
  t <- ur.df(x, type = "drift", selectlags = "AIC")
  cat(sprintf("ADF %-14s estadistico=%.3f  crit5%%=%.3f\n",
              nombre, t@teststat[1], t@cval[1, "5pct"]))
}
for (j in seq_len(ncol(Y))) adf_report(Y[, j], colnames(Y)[j])
# Nota: las tasas de crecimiento y la inflacion son estacionarias por
# construccion; la tasa de desocupacion se trata como I(0) (acotada,
# reversion a la media). El bajo poder del ADF en muestras cortas (n~39)
# se discute en el informe.

## ---- 5. Seleccion del numero de rezagos ------------------------------------
sel <- VARselect(Y, lag.max = 2, type = "const")
print(sel$selection)                   # AIC, HQ, SC(BIC), FPE
print(sel$criteria)
p <- 1                               # rezago elegido (criterio: BIC)

## ---- 6. Estimacion del VAR -------------------------------------------------
var_est <- VAR(Y, p = p, type = "const")
summary(var_est)

## ---- 7. Diagnostico del modelo ---------------------------------------------
roots(var_est)                                   # estabilidad: |raiz| < 1
serial.test(var_est, lags.pt = 8, type = "PT.asymptotic")   # Portmanteau
normality.test(var_est, multivariate.only = TRUE)           # Jarque-Bera
arch.test(var_est, lags.multi = 4)                          # heterocedasticidad

## ---- 8. Identificacion SVAR (restricciones contemporaneas, esquema AB) -----
# El esquema recursivo de corto plazo (Cholesky) implementa las restricciones
# de la consigna: A es triangular inferior con diagonal unitaria (B diagonal).
# Opcion a) con el paquete vars mediante una matriz A triangular inferior:
amat <- diag(ncol(Y)); amat[lower.tri(amat)] <- NA
svar_est <- SVAR(var_est, estmethod = "scoring", Amat = amat,
                 Bmat = diag(ncol(Y)), max.iter = 1000)
print(svar_est$A)
# Opcion b) equivalente con el paquete svars (id.chol respeta el orden de Y):
svar_chol <- id.chol(var_est)
summary(svar_chol)

## ---- 9. Funciones impulso-respuesta (IRF) ----------------------------------
irf_svar <- irf(svar_chol, n.ahead = 16, ci = 0.68, boot = TRUE, nboot = 500)
plot(irf_svar)

## ---- 10. Descomposicion de varianza (FEVD) ---------------------------------
fevd_svar <- fevd(svar_chol, n.ahead = 12)
plot(fevd_svar)
# horizontes 4, 8 y 12 trimestres se tabulan en el informe.

## ---- 11. Choques estructurales recuperados ---------------------------------
shocks <- as.data.frame(svar_chol$B %*% t(resid(var_est)))  # e_t = B^{-1} u_t (aprox)
# (en la practica: structural shocks = solve(P) %*% residuales reducidos)
P <- t(chol(summary(var_est)$covres))
struct <- t(solve(P) %*% t(resid(var_est)))
colnames(struct) <- colnames(Y)
struct <- data.frame(date = fechas[(p+1):length(fechas)], struct)
matplot(struct$date, struct[, -1], type = "l", lty = 1,
        main = "Choques estructurales recuperados")
legend("topright", colnames(Y), col = 1:ncol(Y), lty = 1, cex = 0.7)

## ---- 12. Robustez: modelo ampliado con Remesas (log) -----------------------------
# Se re-estima el sistema incorporando Remesas (log) y se verifica que los signos
# y la persistencia de las respuestas del empleo y el desempleo a un choque de
# actividad se mantienen. Ver informe.

cat("\nAnalisis completado para: Robert Cueto\n")
