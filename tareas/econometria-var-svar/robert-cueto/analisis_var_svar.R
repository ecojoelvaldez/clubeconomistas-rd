# =============================================================================
# Econometria de Series de Tiempo
# Modelos VAR y SVAR aplicados al mercado laboral de la Republica Dominicana
# Estudiante: Robert Cueto
# -----------------------------------------------------------------------------
# Script COMPLETO y REPRODUCIBLE. Reproduce todo el analisis del informe y
# guarda las figuras en ./figuras/.
#
# Especificacion de este estudiante:
#   - Orden recursivo (alternativo): el empleo/las horas se ajustan dentro del
#     trimestre antes que el salario medio (mas rigido), por lo que el empleo
#     precede al salario real; el desempleo cierra el sistema:
#       [Crec.PIB, Inflacion, Crec.ocupados, Salario real, Desempleo]
#   - Rezago p = 1 (criterio BIC/SC, parsimonia)
#   - Robustez: sistema ampliado con las remesas familiares
#
# Datos: panel trimestral 2016Q1-2025Q4 (BCRD: cuentas nacionales, ENCFT, IPC).
#   Ocupados y desempleo coinciden con el master del Club (CE-SER-2026-0014);
#   el salario es dato observado (salario por hora de la ENCFT).
#
# Requiere:
#   install.packages(c("vars","urca","tseries","svars","zoo"))
# Ejecutar DESDE la carpeta del estudiante:  Rscript analisis_var_svar.R
# =============================================================================

suppressPackageStartupMessages({
  library(vars); library(urca); library(tseries); library(svars); library(zoo)
})
set.seed(12345)
dir.create("figuras", showWarnings = FALSE)
COL <- "#b5411f"

## ---- 1. Carga de datos -----------------------------------------------------
panel_path <- if (file.exists("data/panel_trimestral.csv")) "data/panel_trimestral.csv" else "panel_trimestral.csv"
panel <- read.csv(panel_path, stringsAsFactors = FALSE)
panel$date <- as.Date(panel$date)
panel <- panel[order(panel$date), ]

## ---- 2. Construccion de las variables del sistema --------------------------
# Transformaciones (log-diferencias en % y niveles) segun la consigna.
dl <- function(x) 100 * diff(log(x))
crec_pib  <- dl(panel$imae)           # crecimiento del PIB real (indice s.a.)
inflacion <- dl(panel$ipc)            # inflacion trimestral = 100*D log(IPC)
sal_real  <- dl(panel$sal_real_idx)   # crecimiento del salario real (ENCFT)
crec_ocu  <- dl(panel$ocupados)       # crecimiento de los ocupados
desempleo <- panel$tasa_deso[-1]      # tasa de desocupacion (nivel, %)
fechas    <- panel$date[-1]

# Ordenamiento recursivo (identificacion contemporanea / modelo AB):
#   alternativo: actividad -> precios -> empleo -> salario real -> desempleo
Y <- data.frame(
  crec_pib  = crec_pib,
  inflacion = inflacion,
  crec_ocu  = crec_ocu,
  sal_real  = sal_real,
  desempleo = desempleo
)
Y <- ts(Y, start = c(2016, 2), frequency = 4)   # se pierde 2016Q1 por la diferenciacion
k <- ncol(Y)

## ---- 3. Analisis exploratorio ----------------------------------------------
png("figuras/01_variables.png", width = 1100, height = 850, res = 130)
plot.ts(Y, main = "Variables del sistema (transformadas)", col = COL)
dev.off()

cat("\n== Estadisticas descriptivas ==\n"); print(round(apply(Y, 2, function(z)
  c(media = mean(z), sd = sd(z), min = min(z), max = max(z))), 3))
cat("\n== Matriz de correlaciones ==\n"); print(round(cor(Y), 3))

png("figuras/03_correlaciones.png", width = 700, height = 620, res = 130)
image(1:k, 1:k, t(cor(Y))[, k:1], axes = FALSE, xlab = "", ylab = "",
      col = colorRampPalette(c("#b2182b", "white", "#2166ac"))(41), zlim = c(-1, 1))
axis(1, 1:k, colnames(Y), las = 2, cex.axis = .7); axis(2, 1:k, rev(colnames(Y)), las = 2, cex.axis = .7)
title("Matriz de correlaciones"); box()
dev.off()

## ---- 4. Pruebas de estacionariedad (ADF) -----------------------------------
cat("\n== ADF sobre los logaritmos en NIVEL (se esperan no estacionarios) ==\n")
for (v in c("imae", "ipc", "ocupados", "sal_real_idx")) {
  t <- ur.df(log(panel[[v]]), type = "drift", selectlags = "AIC")
  cat(sprintf("  log(%-13s)  ADF=%.3f  crit5%%=%.3f\n", v, t@teststat[1], t@cval[1, "5pct"]))
}
cat("\n== ADF sobre las variables del sistema (transformadas) ==\n")
for (j in seq_len(k)) {
  t <- ur.df(Y[, j], type = "drift", selectlags = "AIC")
  cat(sprintf("  %-11s  ADF=%.3f  crit5%%=%.3f\n", colnames(Y)[j], t@teststat[1], t@cval[1, "5pct"]))
}
# Nota: los crecimientos y la inflacion son estacionarios por construccion; la
# tasa de desocupacion se trata como I(0) (acotada, reversion a la media). El
# ADF tiene bajo poder con n~39; ver discusion en el informe.

## ---- 5. Seleccion del numero de rezagos ------------------------------------
cat("\n== Seleccion de rezagos (AIC, HQ, SC=BIC, FPE) ==\n")
sel <- VARselect(Y, lag.max = 2, type = "const")   # p<=2 por tamano muestral
print(sel$selection); print(round(sel$criteria, 4))
p <- 1                                             # rezago elegido (criterio BIC/SC)

## ---- 6. Estimacion del VAR -------------------------------------------------
var_est <- VAR(Y, p = p, type = "const")
cat("\n== Resumen del VAR ==\n"); print(summary(var_est))

## ---- 7. Diagnostico del modelo ---------------------------------------------
cat("\n== Estabilidad (todas las raices |.| < 1) ==\n"); print(round(roots(var_est), 3))
png("figuras/04_estabilidad.png", width = 620, height = 620, res = 130)
th <- seq(0, 2 * pi, length.out = 200)
plot(cos(th), sin(th), type = "l", lty = 2, asp = 1, xlab = "Re", ylab = "Im",
     main = "Raices del VAR (autovalores companion)")
ev <- roots(var_est, modulus = FALSE)          # autovalores complejos del companion
points(Re(ev), Im(ev), pch = 19, col = COL); abline(h = 0, v = 0, col = "gray")
dev.off()

cat("\n== Portmanteau (autocorrelacion) ==\n");  print(serial.test(var_est, lags.pt = 8, type = "PT.asymptotic"))
cat("\n== Normalidad (Jarque-Bera multivariante) ==\n"); print(normality.test(var_est, multivariate.only = TRUE))
cat("\n== Heterocedasticidad (ARCH multivariante) ==\n"); print(arch.test(var_est, lags.multi = 4))

## ---- 8. Identificacion SVAR (restricciones contemporaneas, esquema AB) -----
# Esquema recursivo de corto plazo (Cholesky) sobre el orden de Y. Equivale al
# modelo AB con A triangular inferior de diagonal unitaria y B diagonal, e
# implementa las restricciones de la consigna.
svar <- id.chol(var_est)
cat("\n== Matriz de impacto contemporaneo B (= factor de Cholesky) ==\n")
print(round(svar$B, 4))

## ---- 9. Funciones impulso-respuesta (IRF) ----------------------------------
# IRF estructurales (ortogonalizadas) con bandas bootstrap ~1 e.e. (68%).
irf_est <- vars::irf(var_est, n.ahead = 16, ortho = TRUE, boot = TRUE,
                     ci = 0.68, runs = 500)
png("figuras/05_irf.png", width = 1500, height = 1100, res = 120)
plot(irf_est)
dev.off()

## ---- 10. Descomposicion de varianza (FEVD) ---------------------------------
fe <- fevd(var_est, n.ahead = 12)
cat("\n== FEVD a 4, 8 y 12 trimestres (%) ==\n")
for (tgt in c("desempleo", "crec_ocu", "sal_real")) {
  cat(sprintf("\n  -- Varianza de %s explicada por cada choque --\n", tgt))
  print(round(fe[[tgt]][c(4, 8, 12), ] * 100, 1))
}
png("figuras/06_fevd.png", width = 1400, height = 520, res = 120)
op <- par(mfrow = c(1, 3))
for (tgt in c("desempleo", "crec_ocu", "sal_real"))
  barplot(t(fe[[tgt]][c(4, 8, 12), ]) * 100, names.arg = c("4", "8", "12"),
          col = 1:k, main = paste("FEVD:", tgt), xlab = "Horizonte (trim.)", ylim = c(0, 100))
par(op); dev.off()

## ---- 11. Choques estructurales recuperados ---------------------------------
P <- t(chol(summary(var_est)$covres))          # factor de Cholesky de Sigma
struct <- t(solve(P) %*% t(resid(var_est)))    # e_t = P^{-1} u_t
colnames(struct) <- colnames(Y)
fech_s <- fechas[(p + 1):length(fechas)]
png("figuras/07_choques.png", width = 1000, height = 1050, res = 120)
op <- par(mfrow = c(k, 1), mar = c(2, 4, 1, 1))
for (j in seq_len(k)) {
  barplot(struct[, j], col = COL, border = NA, ylab = colnames(Y)[j]); abline(h = 0)
}
par(op); dev.off()
cat("\n== Choque de actividad mas negativo (esperado: 2020Q2) ==\n")
print(fech_s[which.min(struct[, "crec_pib"])])

## ---- 12. Robustez: sistema ampliado con las remesas ------------------------
# Se re-estima incorporando el crecimiento de las remesas (ordenado tras la
# actividad) y se comprueba que las respuestas del empleo y el desempleo a un
# choque de actividad conservan signo, magnitud y persistencia.
remesas <- dl(panel$remesas)
Y6 <- ts(data.frame(crec_pib, remesas, inflacion, crec_ocu, sal_real, desempleo),
         start = c(2016, 2), frequency = 4)
var6 <- VAR(Y6, p = p, type = "const")
irf6 <- vars::irf(var6, impulse = "crec_pib", response = c("crec_ocu", "desempleo"),
                  n.ahead = 16, ortho = TRUE, boot = FALSE)
irfb <- vars::irf(var_est, impulse = "crec_pib", response = c("crec_ocu", "desempleo"),
                  n.ahead = 16, ortho = TRUE, boot = FALSE)
png("figuras/08_robustez.png", width = 1100, height = 460, res = 120)
op <- par(mfrow = c(1, 2))
for (r in c("crec_ocu", "desempleo")) {
  yb <- irfb$irf$crec_pib[, r]; ye <- irf6$irf$crec_pib[, r]
  matplot(0:16, cbind(yb, ye), type = "l", lty = c(1, 2), lwd = 2, col = c(COL, "grey30"),
          xlab = "Trimestres", ylab = r, main = paste("Respuesta de", r, "a choque de actividad"))
  abline(h = 0); legend("topright", c("Base (5 var.)", "+ Remesas (6 var.)"),
         lty = c(1, 2), col = c(COL, "grey30"), bty = "n", cex = .8)
}
par(op); dev.off()
cat("\n== Robustez: VAR ampliado estable? ==\n"); print(all(abs(roots(var6)) < 1))

cat("\n\nAnalisis completado para: Robert Cueto\n")
cat("Figuras guardadas en ./figuras/\n")
