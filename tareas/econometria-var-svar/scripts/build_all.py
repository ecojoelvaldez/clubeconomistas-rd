#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Orquesta la construccion completa de ambos entregables."""
import os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEST_ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "entregables")
STUDENTS = {"joel": "joel-valdez", "robert": "robert-cueto"}

def run(*a):
    print("+", " ".join(a))
    subprocess.check_call([sys.executable, *a], cwd=HERE)

# 1. panel maestro (desde el panel provisto por el usuario + remesas del master)
run("build_panel.py", os.path.join(HERE, "panel_master.csv"), os.path.join(HERE, "panel_usuario.csv"))

for key, folder in STUDENTS.items():
    out = os.path.join(HERE, f"out_{key}")
    dest = os.path.join(DEST_ROOT, folder)
    os.makedirs(os.path.join(dest, "figuras"), exist_ok=True)
    os.makedirs(os.path.join(dest, "data"), exist_ok=True)
    # 2. analisis (figuras + results.json)
    run("analysis.py", key, os.path.join(HERE, "panel_master.csv"), out)
    # 3. R script
    run("make_rscript.py", key, os.path.join(out, "results.json"),
        os.path.join(dest, "analisis_var_svar.R"))
    # 4. PDF
    run("report.py", key, os.path.join(out, "results.json"),
        os.path.join(out, "figuras"), os.path.join(dest, "informe.pdf"))
    # 5. figuras
    for f in os.listdir(os.path.join(out, "figuras")):
        shutil.copy(os.path.join(out, "figuras", f), os.path.join(dest, "figuras", f))
    # 6. datos
    shutil.copy(os.path.join(HERE, "panel_master.csv"), os.path.join(dest, "data", "panel_trimestral.csv"))
    shutil.copy(os.path.join(HERE, "panel_usuario.csv"), os.path.join(dest, "data", "panel_usuario.csv"))
    shutil.copy(os.path.join(HERE, "README_datos.md"), os.path.join(dest, "data", "README_datos.md"))
    shutil.copy(os.path.join(HERE, "build_panel.py"), os.path.join(dest, "data", "build_panel.py"))
    print(f"== {folder} listo -> {dest}")

print("\nTODO LISTO en", DEST_ROOT)
