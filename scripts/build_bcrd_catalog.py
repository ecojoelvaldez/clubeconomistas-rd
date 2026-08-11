#!/usr/bin/env python3
"""Genera data/papers_bcrd_concurso.json.

Fuente: Concurso Anual de Economía Biblioteca «Juan Pablo Duarte» del Banco
Central de la República Dominicana (BCRD). Los trabajos premiados se compilan
en la serie «Nueva literatura económica dominicana» (NLED).

Cada entrada apunta al documento accesible más específico que se pudo verificar
(item del Repositorio Cultural del BCRD, PDF del CDN institucional o la colección
completa de la serie). No se aloja ningún PDF en este repositorio.
"""

import json
import pathlib
import re
import unicodedata

REPO = "https://repositoriocultural.bancentral.gov.do/items/"
CDN = "https://cdn.bancentral.gov.do/documents/biblioteca/documents/"
COLECCION = ("https://repositoriocultural.bancentral.gov.do/collections/"
             "145206e2-4a45-4a07-ac7a-0f905fd4d4f9")
RESUMENES = "https://www.bancentral.gov.do/a/d/6084-resumenes-de-los-trabajos-ganadores"

# Enlace del volumen anual de la serie NLED, cuando se pudo verificar.
VOLUMEN = {
    "1998": REPO + "f74e5891-83e9-42da-be5a-d3549f9d5fdb",
    "2000": REPO + "2c97789b-01e6-4baf-a8ab-6fe633cdac17",
    "2005": REPO + "b2b0abe5-275b-437d-b402-7e30d0186b0b",
    "2012": CDN + "libros/Nueva_Literatura_Economica/2012.pdf",
    "2013": CDN + "libros/Nueva_Literatura_Economica/2013.pdf",
    "2014": REPO + "835f0137-1fc7-489e-bcd4-9ed809773a27",
    "2017": CDN + "Nueva_Literatura_Economica_2017.pdf",
    "2020": REPO + "cb10361c-e2ec-406d-aa01-8ebc2b0766f9",
    "2021": REPO + "255097d0-b61d-4886-ae0b-9007847389d3",
    "2023": CDN + "NLED2023.pdf",
}

PREMIO = {
    1: "Primer premio",
    2: "Segundo premio",
    3: "Tercer premio",
    4: "Cuarto premio",
    5: "Quinto premio",
    0: "Mención de honor",
}

# (año, lugar, título, [autores], tema)
GANADORES = [
    # --- 2025 (40.ª edición) ---
    ("2025", 1, "Riesgos en competencia y movilidad laboral: características y determinantes de las transiciones laborales en República Dominicana",
     ["Amanda Carolina Lebrón", "Natanael Ventura Jiménez"], "mercado_laboral"),
    ("2025", 2, "Reformas impositivas en un modelo de crecimiento endógeno con capital humano calibrado para República Dominicana",
     ["Yanna Cristina Dishmey Marte"], "finanzas_publicas"),
    ("2025", 3, "Desigualdad y segmentación territorial como determinantes del impacto del crecimiento en la pobreza: evidencia desde paneles espaciales en la República Dominicana",
     ["Cornelio Antonio Polanco Acosta", "Nerys Federico Ramírez Mordán"], "desarrollo"),
    ("2025", 4, "Impacto del cambio climático en el crecimiento económico y la estabilidad financiera en la República Dominicana",
     ["Manuel Alberto Pérez Pérez", "Ardanys González Marcano"], "macroeconomia"),
    ("2025", 5, "Mapeo multisectorial y predicción macroeconómica de la adopción de pagos móviles: un estudio con Graph Attention Networks y Random Forest",
     ["Peterson Marcellus Delgado"], "sistema_financiero"),

    # --- 2024 ---
    ("2024", 1, "¿Do you speak english? Evaluación del impacto del programa «Inglés de inmersión» para la competitividad de la República Dominicana",
     ["Marvin Antonio Cardoza Espinoza"], "desarrollo"),
    ("2024", 3, "Impacto de la política monetaria en la asunción de riesgos y la estabilidad financiera en la República Dominicana: evidencia y estrategias de mitigación desde un enfoque de paneles dinámicos",
     ["Manuel Alberto Pérez Pérez"], "politica_monetaria"),

    # --- 2023 ---
    ("2023", 1, "Identificación de los vínculos internacionales de la inflación en República Dominicana y Centroamérica: un enfoque bayesiano de vectores globales con selección estocástica",
     ["Fidel Ernesto Morla Martínez"], "politica_monetaria"),

    # --- 2022 ---
    ("2022", 3, "Dinámica de la liquidez del mercado cambiario de República Dominicana: un análisis de cambio de régimen bajo cadenas de Markov",
     ["Georsh Maicol Paulino Victoriano", "José Vidal Cruz Mejía"], "sistema_financiero"),

    # --- 2021 ---
    ("2021", 1, "Topología del sistema de pago de alto valor de la República Dominicana",
     ["Natanael Ventura Jiménez"], "sistema_financiero"),

    # --- 2020 ---
    ("2020", 1, "Comunicados de política monetaria del Banco Central como instrumentos complementarios de política: un análisis semántico para el caso dominicano",
     ["Liliana Eugenia Cruz Quezada"], "politica_monetaria"),
    ("2020", 2, "Reglas de política monetaria y evaluación de bienestar en una economía pequeña y abierta con fricciones financieras: evidencia para República Dominicana desde un enfoque DSGE neokeynesiano",
     ["Manuel Alberto Pérez Pérez"], "politica_monetaria"),
    ("2020", 3, "Caracterización del riesgo de tasa de interés de la cartera de inversión de los bancos múltiples y su importancia en el análisis de la estabilidad financiera en la República Dominicana",
     [], "sistema_financiero"),

    # --- 2019 ---
    ("2019", 1, "Impacto de largo plazo de un programa de transferencias condicionadas: el caso de la República Dominicana",
     ["José Antonio Pellerano Guzmán"], "desarrollo"),
    ("2019", 5, "Incidencia de los conglomerados financieros en la actividad bancaria: tasas de interés, competencia y retorno de conglomerado",
     ["Carlos Alberto Delgado Urbáez"], "sistema_financiero"),

    # --- 2018 (32.ª edición) ---
    ("2018", 1, "Impacto macroeconómico de una política monetaria con metas de inflación",
     ["Ariadne Maridena Checo de los Santos", "Fadua Carolina Camacho Noyola"], "politica_monetaria"),
    ("2018", 2, "Jornada extendida: efectos sobre la oferta laboral femenina dominicana",
     ["José Alexander García de Peña", "Jomayra Patricia Mones Prebisterio"], "mercado_laboral"),
    ("2018", 4, "Una aplicación de la descomposición Blinder-Oaxaca junto a regresiones por cuantiles de influencia recentrada al sector formal e informal y sus determinantes",
     ["Juan Bautista Rodríguez Núñez", "Isaac Enmanuel Guerra Salazar"], "mercado_laboral"),
    ("2018", 5, "Shocks de renta y asignación del tiempo entre trabajo y estudios de los niños y adolescentes de la República Dominicana",
     ["Eva Rosmery Rodríguez Cuevas"], "desarrollo"),

    # --- 2017 (31.ª edición) ---
    ("2017", 1, "Explicando la brecha entre el salario real y la productividad laboral en la República Dominicana: análisis macroeconómico y recomendaciones de políticas basadas en microsimulaciones",
     ["Nabil Sojel López Hawa", "Miguel Alejandro Jiménez Polanco"], "mercado_laboral"),
    ("2017", 2, "Caracterización y dinámica de la desigualdad en la República Dominicana",
     ["Nerys Federico Ramírez Mordán"], "desarrollo"),

    # --- 2016 (30.ª edición) ---
    ("2016", 1, "Determinantes del desempleo en la República Dominicana: dinámica temporal y microsimulaciones",
     ["Nerys Federico Ramírez Mordán"], "mercado_laboral"),
    ("2016", 2, "Análisis intertemporal de la hoja de balance de un banco central: el caso dominicano",
     ["Francisco Alberto Ramírez de León", "Raúl Ovalle"], "politica_monetaria"),
    ("2016", 3, "Una estimación del costo en bienestar de la inflación para República Dominicana",
     ["Oscar Iván Pascual Vásquez"], "politica_monetaria"),
    ("2016", 4, "Riqueza e inclusión financiera: un acercamiento a los costos de exclusión financiera en la República Dominicana",
     ["Carlos Alberto Delgado Urbáez", "Ana Emilia Pimentel Rodríguez"], "sistema_financiero"),
    ("2016", 5, "Educación financiera y la planeación para el retiro laboral en la República Dominicana: análisis a partir de modelos de máxima verosimilitud para variables cualitativas",
     ["Pilar del Carmen Dolores Mateo Mejía", "Antonio María Giraldi Monción"], "finanzas"),

    # --- 2014 ---
    ("2014", 1, "Reglas versus discreción en la política fiscal: introducción al caso dominicano",
     ["Raúl Ovalle", "Francisco Alberto Ramírez de León"], "finanzas_publicas"),
    ("2014", 2, "Análisis del mercado laboral con datos de panel: impacto de la cesantía",
     ["Luis T. Reyes Martínez", "José Manuel Michel"], "mercado_laboral"),
    ("2014", 3, "La economía no observada de la República Dominicana: tamaño, causas y consecuencias",
     ["Fidel Ernesto Morla Martínez"], "macroeconomia"),
    ("2014", 4, "Análisis de la inflación y la conducción de la política monetaria en la República Dominicana",
     ["Gabriela Amelia Tejada Duarte"], "politica_monetaria"),

    # --- 2012 ---
    ("2012", 1, "Evaluación del impacto de los shocks de política fiscal en República Dominicana",
     [], "finanzas_publicas"),

    # --- 2000 ---
    ("2000", 1, "Sistema proactivo de supervisión financiera",
     ["Felipe Antonio Llaugel"], "sistema_financiero"),
    ("2000", 2, "Demanda de salud en la República Dominicana: una estimación econométrica",
     ["Luis Scheker"], "desarrollo"),
    ("2000", 3, "Una nota sobre las crisis económicas y los programas de estabilización en la República Dominicana",
     ["Peter A. Prazmowski"], "macroeconomia"),
]

# Volúmenes anuales de la serie NLED (compilan los trabajos premiados del año).
VOLUMENES_ANUALES = [
    "1996", "1997", "1998", "1999", "2000", "2001", "2002", "2003", "2004",
    "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013",
    "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022",
    "2023", "2024",
]


def slug(text):
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:70]


def enlace(year):
    return VOLUMEN.get(year, COLECCION)


def main():
    items = []

    for year, lugar, title, authors, topic in GANADORES:
        items.append({
            "id": f"bcrd-{year}-{lugar}-{slug(title)}",
            "title": title,
            "authors": authors,
            "topic": topic,
            "type": f"Concurso BCRD · {PREMIO[lugar]}",
            "source": "BCRD · Concurso Biblioteca Juan Pablo Duarte",
            "year": year,
            "date": f"{year}-12-31",
            "source_url": enlace(year),
            "handle": RESUMENES,
            "award": PREMIO[lugar],
            "collection": "Nueva literatura económica dominicana",
            "repro": False,
        })

    for year in VOLUMENES_ANUALES:
        items.append({
            "id": f"bcrd-nled-{year}",
            "title": f"Nueva literatura económica dominicana {year}: trabajos premiados del Concurso de Economía Biblioteca «Juan Pablo Duarte»",
            "authors": ["Banco Central de la República Dominicana"],
            "topic": "macroeconomia",
            "type": "Concurso BCRD · Volumen anual",
            "source": "BCRD · Concurso Biblioteca Juan Pablo Duarte",
            "year": year,
            "date": f"{year}-12-31",
            "source_url": enlace(year),
            "handle": COLECCION,
            "collection": "Nueva literatura económica dominicana",
            "repro": False,
        })

    out = pathlib.Path(__file__).resolve().parent.parent / "data" / "papers_bcrd_concurso.json"
    out.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(items)} entradas -> {out}")


if __name__ == "__main__":
    main()
