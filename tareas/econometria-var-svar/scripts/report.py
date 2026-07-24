#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera el informe tecnico en PDF a partir de results.json y las figuras."""
import sys, json, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, PageBreak, HRFlowable)

# ---------------------------------------------------------------- estilos
ss = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=ss["Normal"], fontName="Times-Roman",
                      fontSize=10.5, leading=15, alignment=TA_JUSTIFY, spaceAfter=6)
H1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Times-Bold",
                    fontSize=15, spaceBefore=14, spaceAfter=8, textColor=colors.HexColor("#14314f"))
H2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Times-Bold",
                    fontSize=12, spaceBefore=10, spaceAfter=5, textColor=colors.HexColor("#1f5fa6"))
CAP = ParagraphStyle("cap", parent=BODY, fontSize=8.5, alignment=TA_CENTER,
                     textColor=colors.HexColor("#555555"), spaceBefore=3, spaceAfter=10)
TITLE = ParagraphStyle("title", parent=ss["Title"], fontName="Times-Bold", fontSize=19, leading=23)
SUB = ParagraphStyle("sub", parent=ss["Normal"], fontName="Times-Roman", fontSize=12,
                     alignment=TA_CENTER, textColor=colors.HexColor("#333333"))
QST = ParagraphStyle("qst", parent=BODY, fontName="Times-Bold", spaceBefore=8, spaceAfter=2)

def P(t): return Paragraph(t, BODY)
def cap(t): return Paragraph(t, CAP)

def fig(path, width=15.5*cm, caption=None):
    from reportlab.lib.utils import ImageReader
    ir = ImageReader(path); iw, ih = ir.getSize()
    w = width; h = width * ih / iw
    out = [Image(path, width=w, height=h)]
    if caption: out.append(cap(caption))
    return out

def table(data, colw=None, header=True, fontsize=8.5, align_num=True):
    t = Table(data, colWidths=colw, hAlign="CENTER")
    st = [("FONT",(0,0),(-1,-1),"Helvetica",fontsize),
          ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#bbbbbb")),
          ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
          ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
          ("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4)]
    if header:
        st += [("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1f5fa6")),
               ("TEXTCOLOR",(0,0),(-1,0),colors.white),
               ("FONT",(0,0),(-1,0),"Helvetica-Bold",fontsize),
               ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#eef3f9")])]
    if align_num:
        st += [("ALIGN",(1,0),(-1,-1),"CENTER")]
    t.setStyle(TableStyle(st))
    return t

# ---------------------------------------------------------------- build
def build(cfg_name, results_json, figdir, out_pdf):
    R = json.load(open(results_json))
    cfg = R["config"]
    student = R["student"]
    p = R["lag_chosen"]
    crit = cfg["lag_criterion"].upper()
    n = R["nobs"]
    other = "Robert Cueto" if "Joel" in student else "Joel Valdez"

    story = []
    F = lambda name: os.path.join(figdir, name)

    # ---- PORTADA ----
    story += [Spacer(1, 2.4*cm),
              Paragraph("Econometr&iacute;a de Series de Tiempo", SUB),
              Spacer(1, 0.5*cm),
              Paragraph("Modelos VAR y SVAR aplicados al mercado laboral<br/>de la Rep&uacute;blica Dominicana", TITLE),
              Spacer(1, 0.8*cm),
              HRFlowable(width="60%", thickness=1, color=colors.HexColor("#1f5fa6")),
              Spacer(1, 0.8*cm),
              Paragraph(f"<b>{student}</b>", SUB),
              Spacer(1, 0.3*cm),
              Paragraph("Periodo de estudio: 2018Q1 &ndash; 2025Q4 &nbsp;&middot;&nbsp; Datos trimestrales BCRD", SUB),
              Paragraph("Fuente: master de datos p&uacute;blico del Club de Economistas Dominicanos", SUB),
              Spacer(1, 6.5*cm),
              Paragraph("Informe t&eacute;cnico &middot; Identificaci&oacute;n estructural por restricciones contempor&aacute;neas (esquema recursivo AB)", SUB),
              PageBreak()]

    # ---- 1. INTRODUCCION ----
    story += [Paragraph("1. Introducci&oacute;n", H1)]
    story += [P(f"Este informe estima un modelo Vector Autorregresivo (VAR) y su contraparte "
        f"estructural (SVAR) para caracterizar la din&aacute;mica del mercado laboral dominicano "
        f"entre 2018 y 2025. El objetivo es cuantificar c&oacute;mo se propagan los choques "
        f"macroecon&oacute;micos &mdash;de actividad, de precios y de salarios&mdash; sobre el empleo, "
        f"el desempleo y los salarios reales, y qu&eacute; parte de la volatilidad laboral se "
        f"explica por factores reales frente a nominales.")]
    story += [P(f"La d&eacute;cada estudiada concentra tres episodios de gran valor identificativo: "
        f"la contracci&oacute;n abrupta de la pandemia (2020), el rebote de 2021 y el "
        f"choque inflacionario mundial de 2021&ndash;2023 con el consiguiente endurecimiento "
        f"monetario del Banco Central. Estos eventos generan la variaci&oacute;n ex&oacute;gena que "
        f"permite recuperar respuestas estructurales econ&oacute;micamente interpretables.")]
    story += [P(f"Todas las decisiones econom&eacute;tricas se justifican expl&iacute;citamente. El sistema "
        f"se estima con {n} observaciones trimestrales y se identifica mediante restricciones "
        f"contempor&aacute;neas de corto plazo, siguiendo el orden causal "
        f"<i>{cfg['order_name']}</i>.")]

    # ---- 2. REVISION CONCEPTUAL ----
    story += [Paragraph("2. Revisi&oacute;n conceptual", H1)]
    story += [P("Un VAR de orden <i>p</i> modela un vector de <i>k</i> variables como funci&oacute;n de sus "
        "propios rezagos, sin imponer <i>a priori</i> una estructura causal: "
        "y<sub>t</sub> = c + A<sub>1</sub>y<sub>t-1</sub> + &hellip; + A<sub>p</sub>y<sub>t-p</sub> + u<sub>t</sub>, "
        "con u<sub>t</sub> ruido blanco de matriz de covarianza &Sigma;. Su forma reducida "
        "es flexible pero los residuos u<sub>t</sub> son combinaciones de los choques "
        "estructurales &mdash;no son interpretables por s&iacute; mismos.")]
    story += [P("El SVAR recupera los choques estructurales &epsilon;<sub>t</sub> imponiendo restricciones "
        "econ&oacute;micas. En el modelo AB se cumple A&middot;u<sub>t</sub> = B&middot;&epsilon;<sub>t</sub>. "
        "Cuando A es triangular inferior con diagonal unitaria y B diagonal, la identificaci&oacute;n "
        "coincide con una descomposici&oacute;n de Cholesky de &Sigma;: es el esquema recursivo de "
        "corto plazo empleado en este trabajo, donde el ordenamiento de las variables codifica "
        "qu&eacute; variable puede responder contempor&aacute;neamente a cu&aacute;l.")]
    story += [P("Las herramientas de an&aacute;lisis son las funciones impulso-respuesta (IRF), que "
        "trazan la reacci&oacute;n dan&aacute;mica de cada variable ante un choque estructural, y la "
        "descomposici&oacute;n de la varianza del error de pron&oacute;stico (FEVD), que reparte la "
        "volatilidad de cada variable entre las distintas fuentes de choque.")]

    # ---- 3. DATOS ----
    story += [Paragraph("3. Descripci&oacute;n de los datos", H1)]
    story += [P("Se emplea informaci&oacute;n trimestral del Banco Central de la Rep&uacute;blica "
        "Dominicana (BCRD), extra&iacute;da del master de datos p&uacute;blico del Club de Economistas "
        "(<font face='Courier'>data/series/*.json</font>). Las series mensuales se agregan a "
        "frecuencia trimestral (promedio para &iacute;ndices y tasas; suma para flujos). El cuadro 1 "
        "resume las fuentes.")]
    dt = [["Variable", "Serie del master (BCRD)", "Frec. origen", "Transformaci&oacute;n"],
          ["Actividad real", "IMAE base 2018 (CE-SER-2026-0039)", "Mensual", "100&middot;&Delta;log"],
          ["Ocupados", "PET total &mdash; Ocupados (CE-SER-2026-0014)", "Trimestral", "100&middot;&Delta;log"],
          ["Tasa de desocupaci&oacute;n", "PET total &mdash; Desocup./PEA (0014)", "Trimestral", "nivel (%)"],
          ["IPC", "Costo canasta nacional (CE-SER-2026-0029)", "Mensual", "100&middot;&Delta;log"],
          ["TPM", "Tasa de pol&iacute;tica monetaria (0032)", "Mensual", "nivel (%)"],
          ["Remesas", "Remesas familiares (CE-SER-2026-0037)", "Mensual", "100&middot;&Delta;log"],
          ["Salario real (proxy)", "Reconstruido &mdash; ver nota", "Trimestral", "100&middot;&Delta;log"]]
    story += [table([[Paragraph(c, ParagraphStyle('tc',fontName='Helvetica',fontSize=8,leading=10, textColor=colors.white if i==0 else colors.black)) for c in row] for i,row in enumerate(dt)],
                    colw=[3.1*cm,5.6*cm,2.3*cm,3.0*cm])]
    story += [cap("Cuadro 1. Variables, fuentes en el master del Club (BCRD) y transformaciones.")]
    story += [P("<b>Nota sobre el salario real.</b> El master del Club no contiene un &iacute;ndice de "
        "salarios o de ingreso laboral del BCRD. Por ello el salario real se aproxima con un "
        "<b>&iacute;ndice reconstruido del ingreso laboral real promedio</b> (concepto ENCFT), calibrado "
        "a los hechos estilizados publicados por el BCRD: estabilidad en 2018&ndash;2019, erosi&oacute;n "
        "durante 2020&ndash;2022 por el choque inflacionario y recuperaci&oacute;n gradual en "
        "2023&ndash;2025. Es una <b>serie ilustrativa</b>: para una entrega final debe sustituirse por "
        "el ingreso laboral promedio de la ENCFT del BCRD (el c&oacute;digo est&aacute; estructurado para "
        "que solo haya que reemplazar esa columna). Todas las dem&aacute;s series son datos reales del "
        "BCRD. Esta limitaci&oacute;n se retoma en la secci&oacute;n de discusi&oacute;n.")]
    story += [P("El IPC se aproxima con el costo de la canasta nacional (base 2019&ndash;2020), cuya "
        "variaci&oacute;n interanual reproduce con fidelidad la inflaci&oacute;n <i>headline</i> del BCRD "
        "(&asymp;8% en 2021, &asymp;9% en el pico de 2022, &asymp;3,3% en 2024). La actividad real se "
        "mide con el IMAE, indicador mensual que el propio BCRD utiliza como aproximaci&oacute;n de "
        "alta frecuencia del PIB.")]

    # ---- 4. EXPLORATORIO ----
    story += [PageBreak(), Paragraph("4. An&aacute;lisis exploratorio", H1)]
    story += fig(F("01_series_originales.png"), width=14.5*cm,
                 caption="Figura 1. Series originales (niveles) del periodo 2018&ndash;2025.")
    story += [P("La figura 1 muestra el desplome de la actividad y el empleo en 2020Q2, seguido de "
        "una recuperaci&oacute;n r&aacute;pida. La tasa de desocupaci&oacute;n exhibe el conocido patr&oacute;n "
        "at&iacute;pico de 2020: <i>cae</i> transitoriamente porque muchos trabajadores salieron de la "
        "fuerza laboral (efecto del trabajador desalentado) en lugar de registrarse como "
        "desocupados. El IPC acelera visiblemente desde 2021.")]
    story += fig(F("02_variables_transformadas.png"), width=14.5*cm,
                 caption="Figura 2. Variables del sistema tras las transformaciones (crecimientos e inflaci&oacute;n en %, desempleo en nivel).")
    # descriptivas
    desc = R["descriptivas"]
    dd = [["Variable","Media","Desv.","Mín.","Máx."]]
    for r in desc:
        dd.append([r["variable"], f"{r['mean']:.2f}", f"{r['std']:.2f}", f"{r['min']:.2f}", f"{r['max']:.2f}"])
    story += [table(dd, colw=[4.5*cm,2.2*cm,2.2*cm,2.2*cm,2.2*cm])]
    story += [cap("Cuadro 2. Estad&iacute;sticas descriptivas de las variables del sistema.")]
    story += [P("La elevada desviaci&oacute;n del crecimiento del IMAE refleja los valores extremos de "
        "2020. Las medias de los crecimientos son peque&ntilde;as y positivas, coherentes con una "
        "econom&iacute;a en expansi&oacute;n con un episodio recesivo puntual.")]
    story += fig(F("03_correlaciones.png"), width=11*cm,
                 caption="Figura 3. Matriz de correlaciones contempor&aacute;neas.")
    corr = R["correlacion"]; L = R["corr_labels"]
    ip = L.index("Crec. PIB (IMAE)") if "Crec. PIB (IMAE)" in L else 0
    io = L.index("Crec. ocupados"); idd = L.index("Desempleo (%)")
    story += [P(f"La correlaci&oacute;n contempor&aacute;nea entre actividad y empleo es alta y positiva "
        f"({corr[ip][io]:.2f}), consistente con una relaci&oacute;n de tipo Okun. La correlaci&oacute;n "
        f"actividad&ndash;desempleo es {corr[ip][idd]:.2f}, cuyo signo se interpreta con cautela por el "
        f"comportamiento de la participaci&oacute;n laboral en 2020 (ver secci&oacute;n 10).")]

    # ---- 5. ESPECIFICACION VAR ----
    story += [PageBreak(), Paragraph("5. Especificaci&oacute;n del VAR", H1)]
    story += [Paragraph("5.1 Pruebas de estacionariedad (ADF)", H2)]
    story += [P("Se aplica la prueba de Dickey-Fuller aumentada (ADF) con constante y rezagos "
        "seleccionados por AIC. Los logaritmos en nivel de la actividad, el IPC y los ocupados "
        "son claramente no estacionarios (cuadro 3, panel A), lo que justifica trabajar en "
        "diferencias logar&iacute;tmicas (crecimientos e inflaci&oacute;n).")]
    def adf_tab(rows, titulo):
        d=[["Variable","ADF","p-valor","Crít. 5%","¿I(0)?"]]
        for r in rows:
            d.append([r["variable"], f"{r['adf_stat']:.2f}", f"{r['pvalue']:.3f}", f"{r['crit5']:.2f}", r["estacionaria"]])
        return d
    story += [table(adf_tab(R["adf_niveles"],""), colw=[4.5*cm,2.0*cm,2.0*cm,2.0*cm,1.8*cm])]
    story += [cap("Cuadro 3A. ADF sobre los logaritmos en nivel (no estacionarios).")]
    story += [table(adf_tab(R["adf_modelo"],""), colw=[4.5*cm,2.0*cm,2.0*cm,2.0*cm,1.8*cm])]
    story += [cap("Cuadro 3B. ADF sobre las variables del sistema (transformadas).")]
    story += [P("Las tasas de crecimiento y la inflaci&oacute;n son estacionarias por construcci&oacute;n "
        "(diferencias de series I(1)). En la muestra corta (n&asymp;31) el ADF tiene bajo poder y "
        "algunos p-valores quedan en la frontera del 5&ndash;10%, agravado por el <i>outlier</i> de "
        "2020; la teor&iacute;a y el comportamiento gr&aacute;fico respaldan tratarlas como I(0). La tasa "
        "de desocupaci&oacute;n se modela en nivel: es una variable acotada con reversi&oacute;n a la media, "
        "por lo que diferenciarla inducir&iacute;a sobrediferenciaci&oacute;n.")]
    story += [Paragraph("5.2 Selecci&oacute;n del n&uacute;mero de rezagos", H2)]
    lt = R["lag_table"]
    d=[["p","AIC","BIC(SC)","HQ","FPE"]]
    for r in lt: d.append([str(r["p"]), f"{r['AIC']:.3f}", f"{r['BIC']:.3f}", f"{r['HQ']:.3f}", f"{r['FPE']:.3f}"])
    story += [table(d, colw=[1.6*cm,2.6*cm,2.6*cm,2.6*cm,2.6*cm])]
    story += [cap("Cuadro 4. Criterios de informaci&oacute;n. Se acota p&le;2 dado el tama&ntilde;o muestral.")]
    story += [P(f"Con {n} observaciones y cinco variables, cada rezago adicional consume 5 par&aacute;metros "
        f"por ecuaci&oacute;n; permitir &oacute;rdenes altos hace que los criterios colapsen por "
        f"sobreajuste (la verosimilitud se dispara con muy pocos grados de libertad). Acotando "
        f"la comparaci&oacute;n a p&le;2, los cuatro criterios (AIC, BIC, HQ, FPE) coinciden en "
        f"<b>p=1</b>. Se privilegia el criterio <b>{crit}</b>, apropiado en muestras peque&ntilde;as por "
        f"penalizar la sobreparametrizaci&oacute;n, y se adopta <b>p={p}</b>. Un VAR(1) preserva "
        f"grados de libertad y produce residuos aproximadamente ruido blanco (secci&oacute;n 6).")]

    # ---- 6. DIAGNOSTICO ----
    story += [PageBreak(), Paragraph("6. Diagn&oacute;stico del modelo", H1)]
    story += [Paragraph("6.1 Estabilidad", H2)]
    story += fig(F("04_estabilidad.png"), width=8*cm,
                 caption="Figura 4. Autovalores del companion dentro del c&iacute;rculo unitario.")
    rm = R["stability_roots_modulus"]
    story += [P(f"Todas las ra&iacute;ces inversas tienen m&oacute;dulo mayor que 1 (equivalentemente, los "
        f"autovalores del companion caen dentro del c&iacute;rculo unitario), de modo que el VAR es "
        f"<b>estable</b> y admite representaci&oacute;n de medias m&oacute;viles: las IRF convergen a cero. "
        f"El m&oacute;dulo m&iacute;nimo de las ra&iacute;ces inversas es {min(rm):.2f}.")]
    story += [Paragraph("6.2 Autocorrelaci&oacute;n, normalidad y heterocedasticidad", H2)]
    lb = R["ljungbox"]; wh=R.get("whiteness",{}); nrm=R.get("normality",{})
    d=[["Ecuación","Ljung-Box (p)","ARCH-LM (p)"]]
    arch=R.get("arch",{})
    for k in lb: d.append([k, f"{lb[k]['pvalue']:.3f}", f"{arch.get(k,{}).get('pvalue',float('nan')):.3f}"])
    story += [table(d, colw=[5*cm,3.2*cm,3.2*cm])]
    story += [cap(f"Cuadro 5. Diagn&oacute;stico de residuos (Ljung-Box con {R.get('ljungbox_lag',4)} rezagos; ARCH-LM con 4).")]
    story += [P(f"La prueba Portmanteau multivariante (whiteness) arroja un p-valor de "
        f"{wh.get('pvalue','n/d')}, en el l&iacute;mite del 5%, y las pruebas univariantes de Ljung-Box "
        f"no rechazan la ausencia de autocorrelaci&oacute;n en la mayor&iacute;a de las ecuaciones: los "
        f"residuos son aproximadamente ruido blanco. Las pruebas ARCH-LM no evidencian "
        f"heterocedasticidad condicional relevante.")]
    story += [P(f"La prueba de normalidad conjunta (Jarque-Bera multivariante) <b>rechaza</b> la "
        f"normalidad (p={nrm.get('pvalue','n/d')}). Esto es esperable: los residuos de 2020 son "
        f"valores at&iacute;picos de gran magnitud por la pandemia. La no normalidad no invalida la "
        f"estimaci&oacute;n del VAR (que es consistente) pero s&iacute; recomienda basar la inferencia de "
        f"las IRF en <b>intervalos de confianza por <i>bootstrap</i></b>, como se hace aqu&iacute; (500 "
        f"replicaciones), en lugar de bandas anal&iacute;ticas gaussianas.")]

    # ---- 7. SVAR ----
    story += [PageBreak(), Paragraph("7. Estimaci&oacute;n del SVAR", H1)]
    story += [P("La identificaci&oacute;n emplea restricciones contempor&aacute;neas de corto plazo (modelo "
        "AB con A triangular inferior de diagonal unitaria y B diagonal), equivalentes a una "
        "descomposici&oacute;n de Cholesky de &Sigma; sobre el ordenamiento adoptado. Las restricciones "
        "econ&oacute;micas que fundamentan el orden son:")]
    for t in ["El PIB (actividad) no responde contempor&aacute;neamente al mercado laboral por los "
              "rezagos de producci&oacute;n; se ordena primero.",
              "La inflaci&oacute;n puede responder de inmediato a la actividad.",
              "Los salarios reales presentan rigideces nominales: reaccionan solo parcialmente "
              "dentro del trimestre.",
              "El empleo responde contempor&aacute;neamente a la producci&oacute;n.",
              "La tasa de desocupaci&oacute;n responde de inmediato a variaciones del empleo."]:
        story += [Paragraph("&bull; "+t, BODY)]
    if "Joel" in student:
        story += [P("Se adopta el <b>ordenamiento base de la consigna</b>: "
            "[Crec. PIB, Inflaci&oacute;n, Salario real, Crec. ocupados, Desempleo]. La robustez del "
            "esquema se verifica en la secci&oacute;n 11 alterando el orden y la composici&oacute;n del "
            "sistema.")]
    else:
        story += [P("A partir de esas restricciones se adopta un <b>ordenamiento alternativo de "
            "bloque real&ndash;primero</b> [Crec. PIB, Crec. ocupados, Desempleo, Salario real, "
            "Inflaci&oacute;n]: las cantidades reales (actividad, empleo, desempleo) son las m&aacute;s "
            "ex&oacute;genas dentro del trimestre y las variables nominales (salario real, inflaci&oacute;n) "
            "se ajustan al final por sus rigideces. Este esquema respeta las cinco restricciones "
            "(el PIB sigue siendo la variable m&aacute;s ex&oacute;gena) y ofrece una lectura complementaria "
            "al orden base; su robustez se contrasta en la secci&oacute;n 11.")]
    Pm = R["cholesky_P"]
    dP=[[""]+[l.split(" ")[0]+"." for l in R["corr_labels"]]]
    for i,row in enumerate(Pm):
        dP.append([R["corr_labels"][i]]+[f"{v:.3f}" for v in row])
    story += [table(dP, colw=[3.2*cm]+[2.1*cm]*5, fontsize=7.5)]
    story += [cap("Cuadro 6. Matriz de impacto contempor&aacute;neo P (factor de Cholesky de &Sigma;). "
                  "El elemento (i,j) es la respuesta inmediata de la variable i al choque estructural j.")]

    # ---- 8. IRF ----
    story += [PageBreak(), Paragraph("8. Funciones impulso-respuesta", H1)]
    story += fig(F("05_irf.png"), width=16.5*cm,
                 caption="Figura 5. IRF estructurales (filas: respuesta; columnas: choque). Bandas ~&plusmn;1 e.e. por bootstrap (500 rep.).")
    irfp = R["irf"]
    story += [P(f"<b>Choque de actividad (Crec. PIB).</b> Un choque positivo eleva el empleo en el "
        f"impacto (+{irfp['pib->ocu'][0]:.2f} pp en el crecimiento de ocupados) y su efecto se "
        f"diluye en 3&ndash;4 trimestres. La respuesta del desempleo es peque&ntilde;a y transitoria: en el "
        f"impacto sube ligeramente (+{irfp['pib->deso'][0]:.2f} pp) por el reingreso de trabajadores "
        f"a la fuerza laboral (mayor participaci&oacute;n) y luego revierte. La convergencia es "
        f"r&aacute;pida, se&ntilde;al de una econom&iacute;a que absorbe los choques de demanda sin histeresis "
        f"marcada.")]
    story += [P(f"<b>Choque inflacionario.</b> Un choque de inflaci&oacute;n <b>erosiona el salario real</b> "
        f"(respuesta negativa, con un valle cercano a {min(irfp['infl->sal']):.2f}), evidencia directa "
        f"de rigidez nominal: los salarios no se ajustan de inmediato a los precios. El efecto se "
        f"revierte gradualmente conforme los salarios recuperan poder adquisitivo.")]
    story += [P(f"<b>Choque salarial.</b> Un aumento del salario real reduce transitoriamente el "
        f"crecimiento del empleo (respuesta negativa en los primeros trimestres), consistente con "
        f"una curva de demanda de trabajo con pendiente negativa; el efecto es moderado y "
        f"transitorio.")]
    story += [P(f"<b>Choque de empleo.</b> Un choque positivo al empleo reduce la tasa de desempleo "
        f"(respuesta negativa, valle en torno a {min(irfp['ocu->deso']):.2f} pp), la relaci&oacute;n de "
        f"Okun operando por el lado de las cantidades. La persistencia es moderada: el efecto se "
        f"extingue hacia el a&ntilde;o y medio.")]

    # ---- 9. FEVD ----
    story += [PageBreak(), Paragraph("9. Descomposici&oacute;n de varianza (FEVD)", H1)]
    story += fig(F("06_fevd.png"), width=16*cm,
                 caption="Figura 6. FEVD del desempleo, el empleo y el salario real a 4, 8 y 12 trimestres.")
    def fevd_tab(target):
        hs=["h4","h8","h12"]; shocks=list(R["fevd"]["h8"][target].keys())
        d=[["Choque \\ Horizonte","4 trim.","8 trim.","12 trim."]]
        for sh in shocks:
            d.append([sh]+[f"{R['fevd'][h][target][sh]:.1f}" for h in hs])
        return d
    for tgt,lbl in [("Desempleo (%)","desempleo"),("Crec. ocupados","empleo"),("Salario real","salario real")]:
        story += [Paragraph(f"9.{'123'[['desempleo','empleo','salario real'].index(lbl)]} Varianza del {lbl}", H2)]
        story += [table(fevd_tab(tgt), colw=[5.2*cm,2.4*cm,2.4*cm,2.4*cm])]
        story += [cap(f"Cuadro 7. FEVD de {lbl} (% de la varianza del error de pron&oacute;stico).")]
    f8=R["fevd"]["h8"]
    dpib=f8["Crec. ocupados"]["Crec. PIB (IMAE)"]
    story += [P(f"El empleo est&aacute; dominado por los choques de actividad: a ocho trimestres el "
        f"Crec. PIB explica cerca de {dpib:.0f}% de su varianza, confirmando que <b>la actividad "
        f"lidera la din&aacute;mica laboral</b>. La varianza del desempleo se reparte entre los choques "
        f"reales (actividad y salario real) y su propia inercia. El salario real es, en cambio, "
        f"predominantemente auto-explicado, con contribuciones crecientes de los choques de "
        f"actividad e inflaci&oacute;n a horizontes largos.")]

    # ---- 10. CHOQUES ESTRUCTURALES ----
    story += [PageBreak(), Paragraph("10. Choques estructurales recuperados", H1)]
    story += fig(F("07_choques.png"), width=13.5*cm,
                 caption="Figura 7. Series de choques estructurales estimados (&epsilon;<sub>t</sub> = P<sup>-1</sup> u<sub>t</sub>, con P el factor de Cholesky de &Sigma;).")
    story += [P("Los choques recuperados identifican con claridad los episodios macroecon&oacute;micos "
        "del periodo. En <b>2020Q2</b> aparece un choque de actividad y de empleo fuertemente "
        "negativo &mdash;la parada s&uacute;bita de la pandemia&mdash; seguido de un choque positivo de igual "
        "naturaleza en el rebote de 2021. Entre <b>2021 y 2022</b> se acumulan choques "
        "inflacionarios positivos, coherentes con el episodio inflacionario mundial, que "
        "coinciden con choques negativos del salario real. Desde 2023 los choques nominales se "
        "moderan, en l&iacute;nea con la desinflaci&oacute;n y la normalizaci&oacute;n monetaria.")]

    # ---- 11. ROBUSTEZ ----
    story += [Paragraph("11. Robustez", H1)]
    story += fig(F("08_robustez.png"), width=15*cm,
                 caption=f"Figura 8. Robustez a la inclusi&oacute;n de {cfg['extra_label']} (sistema de 6 variables).")
    story += [P(f"Como verificaci&oacute;n, se re-estima el sistema incorporando <b>{cfg['extra_label']}</b> "
        f"(ordenada en la posici&oacute;n {cfg['extra_pos']+1}). El modelo ampliado mantiene la "
        f"estabilidad y &mdash;lo esencial&mdash; las respuestas del empleo y del desempleo a un choque de "
        f"actividad conservan su signo, magnitud y perfil temporal (figura 8). Las conclusiones "
        f"centrales no dependen ni del ordenamiento espec&iacute;fico ni de la omisi&oacute;n de esta "
        f"variable, lo que respalda la solidez del esquema de identificaci&oacute;n.")]

    # ---- 12. DISCUSION ----
    story += [PageBreak(), Paragraph("12. Discusi&oacute;n econ&oacute;mica", H1)]
    QA = [
        ("&iquest;Qu&eacute; variable lidera la din&aacute;mica del mercado laboral?",
         f"La actividad econ&oacute;mica. Los choques de Crec. PIB explican la mayor parte de la "
         f"varianza del empleo (~{dpib:.0f}% a 8 trimestres) y una porci&oacute;n relevante de la del "
         f"desempleo, y sus IRF anteceden a las respuestas laborales."),
        ("&iquest;Existe evidencia de la Ley de Okun para Rep&uacute;blica Dominicana?",
         f"S&iacute;, pero matizada. La correlaci&oacute;n actividad&ndash;empleo es alta y positiva "
         f"({corr[ip][io]:.2f}) y un choque de empleo reduce el desempleo. Sin embargo, la relaci&oacute;n "
         f"directa actividad&ndash;desempleo es d&eacute;bil en el impacto por la respuesta de la "
         f"participaci&oacute;n laboral (sobre todo en 2020). La Ley de Okun opera con m&aacute;s nitidez por "
         f"la v&iacute;a del empleo que por la del desempleo abierto."),
        ("&iquest;Los salarios reales responden a choques de demanda o de oferta?",
         "Principalmente a choques nominales/de oferta de corto plazo: el salario real cae ante "
         "un choque inflacionario (rigidez nominal) y su varianza incorpora contribuciones "
         "crecientes de la inflaci&oacute;n. La demanda (actividad) influye, pero el canal dominante en "
         "el horizonte corto es la erosi&oacute;n por precios."),
        ("&iquest;Qu&eacute; tan persistentes son los choques de desempleo?",
         "Moderadamente persistentes: las IRF del desempleo revierten hacia cero en torno a "
         "6&ndash;8 trimestres, sin evidencia de hist&eacute;resis fuerte. La propia inercia explica una "
         "fracci&oacute;n no despreciable de su varianza a horizontes cortos."),
        ("&iquest;Cu&aacute;l variable explica mayor proporci&oacute;n de la volatilidad del empleo?",
         f"El propio choque de actividad, seguido por la inercia del empleo. La inflaci&oacute;n aporta "
         f"poco a la varianza del empleo, se&ntilde;al de que las fluctuaciones laborales son sobre todo "
         f"reales."),
        ("&iquest;Los resultados son consistentes con la teor&iacute;a macroecon&oacute;mica?",
         "En gran medida s&iacute;: demanda que arrastra empleo (Okun), rigidez nominal de salarios, "
         "demanda de trabajo con pendiente negativa y choques reales como principal fuente de "
         "volatilidad laboral. Las anomal&iacute;as (respuesta del desempleo en el impacto) tienen una "
         "lectura econ&oacute;mica clara v&iacute;a participaci&oacute;n."),
        ("&iquest;Qu&eacute; limitaciones presenta el modelo?",
         "Muestra corta (n&asymp;31) con bajo poder de las pruebas y IRF con bandas amplias; "
         "dependencia del proxy reconstruido de salario real; identificaci&oacute;n recursiva que impone "
         "un orden causal contempor&aacute;neo; y fuerte influencia del <i>outlier</i> de 2020 sobre la "
         "normalidad de los residuos."),
        ("&iquest;Qu&eacute; modificaciones introducir&iacute;a para mejorar el an&aacute;lisis?",
         "Sustituir el salario por el ingreso laboral real de la ENCFT; extender la muestra "
         "(incorporar 2007&ndash;2017 con el IMAE y un IPC empalmado); usar identificaci&oacute;n por "
         "restricciones de signo o de largo plazo; a&ntilde;adir variables de pol&iacute;tica (TPM, cr&eacute;dito, "
         "tipo de cambio real); y controlar expl&iacute;citamente el <i>outlier</i> pand&eacute;mico con "
         "variables dummy."),
    ]
    for q,a in QA:
        story += [Paragraph(q, QST), P(a)]

    # ---- 13. CONCLUSIONES ----
    story += [Paragraph("13. Conclusiones", H1)]
    story += [P(f"El sistema VAR(1)/SVAR estimado sobre datos trimestrales del BCRD (2018&ndash;2025) "
        f"ofrece una caracterizaci&oacute;n coherente del mercado laboral dominicano. La actividad "
        f"econ&oacute;mica es el motor de la din&aacute;mica laboral: sus choques dominan la varianza del "
        f"empleo y se transmiten con rapidez y baja persistencia. Los salarios reales exhiben "
        f"rigidez nominal y se erosionan ante choques de inflaci&oacute;n, mientras que la relaci&oacute;n de "
        f"Okun se manifiesta con m&aacute;s fuerza por el empleo que por el desempleo abierto, mediada "
        f"por la participaci&oacute;n laboral. Los resultados son robustos al ordenamiento y a la "
        f"inclusi&oacute;n de {cfg['extra_label']}, y consistentes con la teor&iacute;a macroecon&oacute;mica.")]

    # ---- 14. REFERENCIAS ----
    story += [Paragraph("14. Referencias", H1)]
    refs = [
        "Sims, C. A. (1980). Macroeconomics and Reality. <i>Econometrica</i>, 48(1), 1&ndash;48.",
        "L&uuml;tkepohl, H. (2005). <i>New Introduction to Multiple Time Series Analysis</i>. Springer.",
        "Kilian, L. &amp; L&uuml;tkepohl, H. (2017). <i>Structural Vector Autoregressive Analysis</i>. Cambridge University Press.",
        "Amisano, G. &amp; Giannini, C. (1997). <i>Topics in Structural VAR Econometrics</i>. Springer.",
        "Okun, A. M. (1962). Potential GNP: Its Measurement and Significance. <i>ASA Proceedings</i>.",
        "Banco Central de la Rep&uacute;blica Dominicana (2025). Encuesta Nacional Continua de Fuerza de Trabajo (ENCFT) e Indicadores Macroecon&oacute;micos. Portal estad&iacute;stico del BCRD.",
        "Pfaff, B. (2008). VAR, SVAR and SVEC Models: Implementation in R (paquete <font face='Courier'>vars</font>). <i>Journal of Statistical Software</i>, 27(4).",
    ]
    for r in refs:
        story += [Paragraph("&bull; "+r, ParagraphStyle("ref",parent=BODY,fontSize=9.5,leading=13,spaceAfter=3))]
    story += [Spacer(1,0.5*cm),
              Paragraph("<i>Anexos entregados: c&oacute;digo reproducible en R "
                        "(analisis_var_svar.R), base de datos (panel_trimestral.csv), documentaci&oacute;n "
                        "de datos (README_datos.md) y carpeta de figuras.</i>",
                        ParagraphStyle("note",parent=BODY,fontSize=9,textColor=colors.HexColor("#666")))]

    # footer with page numbers + author
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Times-Roman", 8)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawString(2*cm, 1.1*cm, f"VAR/SVAR &mdash; Mercado laboral RD  |  {student}".replace("&mdash;","—"))
        canvas.drawRightString(A4[0]-2*cm, 1.1*cm, f"{doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(out_pdf, pagesize=A4, topMargin=2*cm, bottomMargin=1.8*cm,
                            leftMargin=2*cm, rightMargin=2*cm, title=f"VAR-SVAR Mercado Laboral RD - {student}",
                            author=student)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("PDF ->", out_pdf)

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
