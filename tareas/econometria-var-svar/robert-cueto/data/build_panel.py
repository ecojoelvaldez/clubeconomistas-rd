#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construye el panel trimestral 2016Q1-2025Q4 del mercado laboral dominicano.

Base: panel provisto (panel_usuario.csv), cuyas columnas de ocupados y tasa de
desocupacion COINCIDEN exactamente con las series del BCRD del master del Club
(CE-SER-2026-0014). Aporta ademas el dato REAL de salario (salario por hora en
RD$ e indice de salario real) y extiende la cobertura de PIB e IPC a 2016.

Se complementa con las remesas familiares del master del Club (CE-SER-2026-0037)
para el ejercicio de robustez.

Salida: panel_master.csv con el esquema que consume analysis.py:
  imae (=PIB indice s.a.), ocupados, pea, desocupados, tasa_deso, ipc, tpm,
  remesas, sal_real_idx, sal_nom_idx, y transformaciones log.
"""
import json, os, sys
import numpy as np
import pandas as pd

REPO = "/home/user/clubeconomistas-rd"
HERE = os.path.dirname(os.path.abspath(__file__))
QMAP = {"I": 1, "II": 2, "III": 3, "IV": 4}

def load_remesas():
    with open(os.path.join(REPO, "data", "series", "CE-SER-2026-0037.json")) as f:
        d = json.load(f)
    df = pd.DataFrame(d["observations"]); df["date"] = pd.to_datetime(df["date"])
    s = df[df["variable"] == "remesas_familiares_recibidas"][["date", "value"]].set_index("date")["value"].sort_index()
    q = s.resample("QE").sum()
    return q

def main(user_csv, dest):
    u = pd.read_csv(user_csv)
    u["q"] = u["quarter"].map(QMAP)
    per = pd.PeriodIndex([pd.Period(year=int(y), quarter=int(q), freq="Q") for y, q in zip(u["year"], u["q"])])
    u["date"] = per.to_timestamp(how="end").normalize() + pd.offsets.QuarterEnd(0)
    u = u.set_index("date").sort_index()

    p = pd.DataFrame(index=u.index)
    p["imae"]        = u["pib_indice_sa"]          # actividad real: PIB indice desestacionalizado
    p["ocupados"]    = u["ocupados"]
    p["tasa_deso"]   = u["tasa_desocupacion"]
    p["ipc"]         = u["ipc_promedio_trim"]
    p["tpm"]         = u["tpm_promedio_trim"]
    p["salario_hora"] = u["salario_hora_rd"]        # salario nominal por hora (RD$) - REAL
    # indice de salario real (base: nivel implicito). Su 100*dlog reproduce
    # exactamente el crecimiento del salario real = 100*d(salario_real_log).
    p["sal_real_idx"] = u["salario_hora_rd"] / u["ipc_promedio_trim"] * 100.0
    p["sal_nom_idx"]  = u["salario_hora_rd"]

    # remesas del master del Club (para robustez)
    rem = load_remesas()
    p = p.join(rem.rename("remesas"))

    # transformaciones
    p["lpib"]     = np.log(p["imae"])
    p["locu"]     = np.log(p["ocupados"])
    p["lipc"]     = np.log(p["ipc"])
    p["lsalnom"]  = np.log(p["sal_nom_idx"])
    p["lsalreal"] = np.log(p["sal_real_idx"])
    p.index.name = "date"

    d = os.path.dirname(dest)
    if d: os.makedirs(d, exist_ok=True)
    p.round(6).to_csv(dest)
    print("Panel guardado en", dest)
    print("Rango:", p.index.min().date(), "->", p.index.max().date(), "| Nobs:", len(p))
    print("NaNs:", p[["imae","ocupados","tasa_deso","ipc","tpm","remesas","sal_real_idx"]].isna().sum().to_dict())

if __name__ == "__main__":
    user_csv = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "panel_usuario.csv")
    main(user_csv, sys.argv[1])
