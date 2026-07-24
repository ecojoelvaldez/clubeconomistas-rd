#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motor de estimacion VAR/SVAR del mercado laboral dominicano.
Se ejecuta con una configuracion por estudiante y produce todas las figuras,
tablas y un results.json con los numeros que alimentan el informe.

Identificacion SVAR: esquema recursivo de corto plazo (descomposicion de
Cholesky) sobre el ordenamiento
    [Crec.PIB, Inflacion, Salario Real, Crec.Ocupados, Desempleo].
Este esquema es un caso particular del modelo AB con A triangular inferior de
diagonal unitaria y B diagonal, e implementa exactamente las restricciones
contemporaneas exigidas en la tarea.
"""
import os, json, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.stats.stattools import jarque_bera

plt.rcParams.update({"figure.dpi": 130, "font.size": 9, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.spmap": False} if False else {
                     "figure.dpi": 130, "font.size": 9, "axes.grid": True, "grid.alpha": 0.25})

# ----------------------------------------------------------------------------- config
def get_config(name):
    C = {
        "joel": dict(
            student="Joel Valdez",
            color="#1f5fa6",
            sal_mode="growth",       # salario real en primera diferencia (crecimiento)
            extra_var="tpm",         # variable adicional en robustez (6 variables)
            extra_label="TPM (%)",
            extra_pos=2,             # posicion de la variable extra en el orden recursivo
            lag_criterion="aic",     # criterio privilegiado
            growth="qoq",            # transformacion de crecimiento
            order=["crec_pib","inflacion","sal_real","crec_ocu","desempleo"],  # orden base de la tarea
            order_name="base de la consigna (actividad -> precios -> salarios -> empleo -> desempleo)",
        ),
        "robert": dict(
            student="Robert Cueto",
            color="#b5411f",
            sal_mode="growth",
            extra_var="remesas",
            extra_label="Remesas (log)",
            extra_pos=1,
            lag_criterion="bic",     # criterio privilegiado (parsimonia)
            growth="qoq",
            # ordenamiento alternativo "bloque real primero": actividad y cantidades
            # (empleo, desempleo) son las mas exogenas; las variables nominales
            # (salario real, inflacion) se ajustan al final por rigideces nominales.
            order=["crec_pib","crec_ocu","desempleo","sal_real","inflacion"],
            order_name="alternativo bloque real-primero (actividad -> empleo -> desempleo -> salarios -> precios)",
        ),
    }
    return C[name]

VARLABELS = {
    "crec_pib":  "Crec. PIB (IMAE)",
    "inflacion": "Inflación",
    "sal_real":  "Salario real",
    "crec_ocu":  "Crec. ocupados",
    "desempleo": "Desempleo (%)",
}
ORDER_BASE = ["crec_pib", "inflacion", "sal_real", "crec_ocu", "desempleo"]
VARLABELS["tpm"] = "TPM (%)"
VARLABELS["remesas"] = "Crec. remesas"

# ----------------------------------------------------------------------------- data
def build_svar_data(panel, cfg, order=None, extra=None):
    df = panel.copy()
    d = pd.DataFrame(index=df.index)
    d["crec_pib"]  = 100 * np.log(df["imae"]).diff()
    d["inflacion"] = 100 * np.log(df["ipc"]).diff()
    if cfg["sal_mode"] == "level":
        d["sal_real"] = np.log(df["sal_real_idx"]) * 100          # log-nivel (x100 = indice log)
    else:
        d["sal_real"] = 100 * np.log(df["sal_real_idx"]).diff()   # crecimiento
    d["crec_ocu"]  = 100 * np.log(df["ocupados"]).diff()
    d["desempleo"] = df["tasa_deso"]
    if extra == "tpm":
        d["tpm"] = df["tpm"]
    elif extra == "remesas":
        d["remesas"] = 100 * np.log(df["remesas"]).diff()
    d = d.loc["2018-01-01":"2025-12-31"].dropna()
    cols = order if order is not None else cfg["order"]
    return d[cols]

# ----------------------------------------------------------------------------- helpers
def adf_table(series_dict):
    rows = []
    for name, s in series_dict.items():
        s = s.dropna()
        r = adfuller(s, autolag="AIC", regression="c")
        rows.append(dict(variable=name, adf_stat=round(r[0], 3), pvalue=round(r[1], 4),
                         nlags=int(r[2]), crit5=round(r[4]["5%"], 3),
                         estacionaria=("Si" if r[1] < 0.05 else "No")))
    return rows

def savefig(fig, path):
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)

# ----------------------------------------------------------------------------- main
def run(cfg_name, panel_csv, outdir):
    cfg = get_config(cfg_name)
    ORDER = list(cfg["order"])          # ordenamiento recursivo de este estudiante
    os.makedirs(os.path.join(outdir, "figuras"), exist_ok=True)
    figdir = os.path.join(outdir, "figuras")
    col = cfg["color"]
    panel = pd.read_csv(panel_csv, index_col=0, parse_dates=True)
    data = build_svar_data(panel, cfg)
    res = dict(student=cfg["student"], config=cfg, sample_start=str(data.index.min().date()),
               sample_end=str(data.index.max().date()), nobs=int(len(data)))

    # ---- 0. series crudas ----
    raw = panel.loc["2018-01-01":"2025-12-31", ["imae","ocupados","tasa_deso","ipc","sal_real_idx"]]
    fig, axes = plt.subplots(3, 2, figsize=(9, 8))
    titles = {"imae":"IMAE (indice, base 2018=100)","ocupados":"Ocupados (personas)",
              "tasa_deso":"Tasa de desocupacion (%)","ipc":"IPC / canasta (indice)",
              "sal_real_idx":"Salario real (indice, proxy)"}
    for ax,(k,t) in zip(axes.flat, titles.items()):
        ax.plot(raw.index, raw[k], color=col); ax.set_title(t, fontsize=9)
    axes.flat[-1].axis("off")
    fig.suptitle(f"Series originales — {cfg['student']}", fontsize=11)
    savefig(fig, os.path.join(figdir, "01_series_originales.png"))

    # ---- 1. variables SVAR transformadas ----
    fig, axes = plt.subplots(3, 2, figsize=(9, 8))
    for ax, v in zip(axes.flat, ORDER):
        ax.plot(data.index, data[v], color=col); ax.axhline(0, lw=.6, color="k", alpha=.4)
        ax.set_title(VARLABELS[v], fontsize=9)
    axes.flat[-1].axis("off")
    fig.suptitle(f"Variables del sistema (transformadas) — {cfg['student']}", fontsize=11)
    savefig(fig, os.path.join(figdir, "02_variables_transformadas.png"))

    # ---- 2. descriptivas + correlacion ----
    desc = data.describe().T[["mean","std","min","max"]].round(3)
    desc.index = [VARLABELS[i] for i in desc.index]
    res["descriptivas"] = desc.reset_index().rename(columns={"index":"variable"}).to_dict("records")
    corr = data.corr().round(3)
    res["correlacion"] = corr.values.tolist()
    res["corr_labels"] = [VARLABELS[i] for i in corr.columns]
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(5)); ax.set_yticks(range(5))
    ax.set_xticklabels([VARLABELS[c] for c in corr.columns], rotation=40, ha="right", fontsize=8)
    ax.set_yticklabels([VARLABELS[c] for c in corr.columns], fontsize=8)
    for i in range(5):
        for j in range(5):
            ax.text(j, i, f"{corr.values[i,j]:.2f}", ha="center", va="center",
                    color="white" if abs(corr.values[i,j])>.6 else "black", fontsize=8)
    fig.colorbar(im, fraction=0.046, pad=0.04)
    ax.set_title(f"Matriz de correlaciones — {cfg['student']}", fontsize=10)
    savefig(fig, os.path.join(figdir, "03_correlaciones.png"))

    # ---- 3. ADF ----
    adf_in = {VARLABELS[v]: data[v] for v in ORDER}
    # tambien niveles log para justificar diferenciacion
    adf_lvl = {"log(IMAE)": np.log(panel.loc["2018":"2025","imae"]),
               "log(IPC)":  np.log(panel.loc["2018":"2025","ipc"]),
               "log(Ocupados)": np.log(panel.loc["2018":"2025","ocupados"])}
    res["adf_niveles"] = adf_table(adf_lvl)
    res["adf_modelo"] = adf_table(adf_in)

    # ---- 4. seleccion de rezagos ----
    model = VAR(data)
    maxlags = 2   # con 31 obs y 5 variables se acota p<=2 para preservar grados de libertad
    sel = model.select_order(maxlags)
    ic_tab = {}
    for k in ["aic","bic","hqic","fpe"]:
        try: ic_tab[k] = {int(l): float(v) for l, v in enumerate(getattr(sel, "ics")[k])}
        except Exception: pass
    sels = sel.selected_orders
    res["lag_selection"] = {k: int(v) for k, v in sels.items()}
    crit_map = {"aic":"aic","bic":"bic","hq":"hqic","fpe":"fpe"}
    p = int(sels[crit_map[cfg["lag_criterion"]]])
    p = max(1, min(p, 2))
    res["lag_chosen"] = p
    res["lag_criterion"] = cfg["lag_criterion"]

    # tabla criterios (muestra comun, consistente con select_order); lags 1..maxlags
    ics = sel.ics
    order_df = pd.DataFrame({"AIC":[ics["aic"][l] for l in range(1,maxlags+1)],
                             "BIC":[ics["bic"][l] for l in range(1,maxlags+1)],
                             "HQ":[ics["hqic"][l] for l in range(1,maxlags+1)],
                             "FPE":[ics["fpe"][l] for l in range(1,maxlags+1)]},
                            index=range(1,maxlags+1))
    res["lag_table"] = order_df.round(4).reset_index().rename(columns={"index":"p"}).to_dict("records")

    # ---- 5. estimacion VAR ----
    var_res = model.fit(p)
    res["var_llf"] = float(var_res.llf)

    # ---- 6. diagnostico ----
    roots_mod = np.abs(var_res.roots)              # raices inversas: |root|>1 -> estable
    res["stability_roots_modulus"] = sorted([round(float(x),3) for x in roots_mod])
    res["stable"] = bool(np.all(roots_mod > 1))
    # unit circle plot (eigenvalues of companion = 1/roots)
    eig = var_res.roots
    ev = 1.0/eig
    fig, ax = plt.subplots(figsize=(4.4,4.4))
    th=np.linspace(0,2*np.pi,200); ax.plot(np.cos(th),np.sin(th),'k--',lw=.8)
    ax.scatter(ev.real, ev.imag, color=col, zorder=3)
    ax.axhline(0,lw=.5,color='gray'); ax.axvline(0,lw=.5,color='gray')
    ax.set_aspect("equal"); ax.set_title("Raices del VAR (modulos de los\nautovalores del companion)", fontsize=9)
    ax.set_xlim(-1.2,1.2); ax.set_ylim(-1.2,1.2)
    savefig(fig, os.path.join(figdir, "04_estabilidad.png"))

    # Portmanteau (Ljung-Box) sobre cada residuo
    lb = {}
    lb_lag = 4
    for i,v in enumerate(ORDER):
        r = acorr_ljungbox(var_res.resid.iloc[:,i], lags=[lb_lag], return_df=True)
        lb[VARLABELS[v]] = dict(stat=round(float(r["lb_stat"].iloc[0]),3), pvalue=round(float(r["lb_pvalue"].iloc[0]),4))
    res["ljungbox"] = lb
    res["ljungbox_lag"] = lb_lag
    # whiteness (multivariante) de statsmodels: nlags moderado por tamano muestral
    wnl = p + 2
    try:
        wt = var_res.test_whiteness(nlags=wnl, adjusted=True)
        res["whiteness"] = dict(stat=round(float(wt.test_statistic),3), pvalue=round(float(wt.pvalue),4), nlags=wnl)
    except Exception as e:
        res["whiteness"] = dict(error=str(e))
    # normalidad
    try:
        nt = var_res.test_normality()
        res["normality"] = dict(stat=round(float(nt.test_statistic),3), pvalue=round(float(nt.pvalue),4))
    except Exception as e:
        res["normality"] = dict(error=str(e))
    # ARCH por ecuacion
    arch = {}
    for i,v in enumerate(ORDER):
        try:
            a = het_arch(var_res.resid.iloc[:,i], nlags=4)
            arch[VARLABELS[v]] = dict(stat=round(float(a[0]),3), pvalue=round(float(a[1]),4))
        except Exception: pass
    res["arch"] = arch

    # ---- 7. SVAR recursivo (Cholesky) ----
    Sigma = var_res.sigma_u.values
    P = np.linalg.cholesky(Sigma)               # A0^{-1} = P (impacto estructural)
    res["cholesky_P"] = P.round(4).tolist()
    # matriz A (contemporanea, triangular inferior con diagonal unitaria): A = D * P^{-1}
    Pinv = np.linalg.inv(P)
    A = (np.diag(np.diag(np.linalg.inv(Pinv))) @ Pinv)  # normaliza diagonal a 1 aprox
    # forma estandar A y_t contemporaneo: usamos P para impacto; reportamos P
    horizon = 16
    irf = var_res.irf(horizon)
    # IRF ortogonalizadas (estructurales) con IC bootstrap
    irf_orth = irf.orth_irfs                     # (h+1, k, k)
    res["irf"] = {}
    # bootstrap CI
    try:
        cis = irf.errband_mc(orth=True, repl=500, signif=0.32, seed=12345)  # ~1 s.e.
        lo, hi = cis
    except Exception:
        lo = hi = None

    shocks = ["crec_pib","inflacion","sal_real","crec_ocu"]  # choques a analizar (+empleo)
    shocks_full = ORDER
    # grid: filas = respuesta variable, columnas = choque estructural (seleccion)
    sel_shocks = ["crec_pib","inflacion","sal_real","crec_ocu","desempleo"]
    fig, axes = plt.subplots(len(ORDER), len(sel_shocks), figsize=(13, 11), sharex=True)
    for si, sh in enumerate(sel_shocks):
        j = ORDER.index(sh)
        for ri, rv in enumerate(ORDER):
            i = ORDER.index(rv)
            ax = axes[ri, si]
            y = irf_orth[:, i, j]
            ax.plot(range(horizon+1), y, color=col, lw=1.4)
            if lo is not None:
                ax.fill_between(range(horizon+1), lo[:,i,j], hi[:,i,j], color=col, alpha=.18)
            ax.axhline(0, color="k", lw=.5)
            if ri==0: ax.set_title(f"Choque:\n{VARLABELS[sh]}", fontsize=8)
            if si==0: ax.set_ylabel(VARLABELS[rv], fontsize=8)
            ax.tick_params(labelsize=7)
    fig.suptitle(f"Funciones impulso-respuesta estructurales (Cholesky) — {cfg['student']}\n"
                 f"bandas ~±1 e.e. (bootstrap, 500 rep.)", fontsize=11)
    savefig(fig, os.path.join(figdir, "05_irf.png"))

    # guarda IRF numericas (respuestas clave)
    def irf_path(shock, resp):
        return [round(float(x),4) for x in irf_orth[:, ORDER.index(resp), ORDER.index(shock)]]
    res["irf"]["pib->ocu"]  = irf_path("crec_pib","crec_ocu")
    res["irf"]["pib->deso"] = irf_path("crec_pib","desempleo")
    res["irf"]["infl->sal"] = irf_path("inflacion","sal_real")
    res["irf"]["sal->ocu"]  = irf_path("sal_real","crec_ocu")
    res["irf"]["ocu->deso"] = irf_path("crec_ocu","desempleo")

    # ---- 8. FEVD ----
    fevd = var_res.fevd(13)
    dec = fevd.decomp    # (k, h, k) : var i at horizon h explained by shock j
    res["fevd"] = {}
    for h in [4,8,12]:
        tab = {}
        for i,rv in enumerate(ORDER):
            tab[VARLABELS[rv]] = {VARLABELS[ORDER[j]]: round(float(dec[i,h-1,j])*100,1) for j in range(5)}
        res["fevd"][f"h{h}"] = tab
    # FEVD barras para desempleo, empleo, salario a h=4,8,12
    targets = ["desempleo","crec_ocu","sal_real"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))
    hs=[4,8,12]
    for ax, tv in zip(axes, targets):
        i = ORDER.index(tv)
        bottoms=np.zeros(len(hs))
        cmap = plt.get_cmap("tab10")
        for j,sh in enumerate(ORDER):
            vals=[dec[i,h-1,j]*100 for h in hs]
            ax.bar([str(h) for h in hs], vals, bottom=bottoms, label=VARLABELS[sh], color=cmap(j))
            bottoms+=np.array(vals)
        ax.set_title(f"FEVD: {VARLABELS[tv]}", fontsize=9); ax.set_xlabel("Horizonte (trimestres)")
        ax.set_ylim(0,100)
    axes[-1].legend(fontsize=7, loc="center left", bbox_to_anchor=(1.02,.5))
    fig.suptitle(f"Descomposicion de varianza del error de pronostico — {cfg['student']}", fontsize=11)
    savefig(fig, os.path.join(figdir, "06_fevd.png"))

    # ---- 9. choques estructurales recuperados ----
    u = var_res.resid.values                    # reduced-form
    struct = u @ np.linalg.inv(P).T             # e_t = P^{-1} u_t
    sidx = var_res.resid.index
    fig, axes = plt.subplots(5,1, figsize=(9,10), sharex=True)
    for i,(ax,v) in enumerate(zip(axes, ORDER)):
        ax.bar(sidx, struct[:,i], color=col, width=60)
        ax.axhline(0,color="k",lw=.5); ax.set_ylabel(VARLABELS[v], fontsize=8)
    axes[0].set_title(f"Choques estructurales recuperados — {cfg['student']}", fontsize=11)
    savefig(fig, os.path.join(figdir, "07_choques.png"))
    res["struct_shocks_dates"] = [str(pd.Timestamp(x).date()) for x in sidx]
    res["struct_shocks"] = {VARLABELS[ORDER[i]]: [round(float(struct[t,i]),3) for t in range(len(sidx))] for i in range(5)}

    # ---- 10. ROBUSTEZ: modelo ampliado con variable adicional ----
    ex = cfg["extra_var"]
    ex_order = list(ORDER)
    ex_order.insert(cfg["extra_pos"], ex)
    data_ex = build_svar_data(panel, cfg, order=ex_order, extra=ex)
    var_ex = VAR(data_ex).fit(p)
    irf_ex = var_ex.irf(horizon).orth_irfs
    res["robust_var"] = cfg["extra_var"]
    res["robust_order"] = [VARLABELS[v] for v in ex_order]
    res["robust_stable"] = bool(np.all(np.abs(var_ex.roots) > 1))
    # comparacion respuesta de desempleo y crec_ocu a un choque de PIB
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8))
    for ax, rv in zip(axes, ["crec_ocu", "desempleo"]):
        yb = irf_orth[:, ORDER.index(rv), ORDER.index("crec_pib")]
        ye = irf_ex[:, ex_order.index(rv), ex_order.index("crec_pib")]
        ax.plot(range(horizon+1), yb, color=col, lw=1.6, label="Modelo base (5 var.)")
        ax.plot(range(horizon+1), ye, color="#555", lw=1.4, ls="--", label=f"+ {cfg['extra_label']} (6 var.)")
        ax.axhline(0, color="k", lw=.5); ax.set_title(f"Respuesta de {VARLABELS[rv]}\na un choque de actividad", fontsize=9)
        ax.legend(fontsize=7)
    fig.suptitle(f"Robustez del SVAR a la inclusion de {cfg['extra_label']} — {cfg['student']}", fontsize=10)
    savefig(fig, os.path.join(figdir, "08_robustez.png"))
    res["robust_irf_ocu"] = [round(float(x),4) for x in irf_ex[:, ex_order.index("crec_ocu"), ex_order.index("crec_pib")]][:8]
    res["robust_irf_deso"] = [round(float(x),4) for x in irf_ex[:, ex_order.index("desempleo"), ex_order.index("crec_pib")]][:8]

    with open(os.path.join(outdir, "results.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f"[{cfg['student']}] listo. nobs={res['nobs']} p={p} estable={res['stable']} -> {outdir}")
    return res

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3])
