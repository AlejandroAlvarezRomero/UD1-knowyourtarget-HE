"""Modo automático de reconocimiento pasivo, sin modelo de IA.

Ejecuta las herramientas activas en un orden fijo, guarda cada llamada en la
traza (con el mismo formato que el agente) y redacta un informe de evidencias.
Sirve de respaldo cuando el servicio de IA no está disponible y también para
auditar las herramientas sin gastar tokens.

No sustituye al agente: el informe resultante es una recopilación automática de
lo que devolvió cada herramienta, sin interpretación del modelo.
"""

import json
import re
from datetime import datetime

from alcance import en_alcance
from guard import fijar_scope

TIPOS_DNS = ("A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "CAA", "SRV")
CATEGORIAS_DORK = ("archivos", "paneles", "config")

PATRON_DOMINIO = re.compile(
    r"(?<![\w.-])((?:[a-z0-9-]+\.)+[a-z]{2,})(?![\w.-])", re.IGNORECASE
)
PATRON_EMAIL = re.compile(
    r"\b([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
)
PATRON_SECRETO = re.compile(
    r"([?&](?:state|code|token|access_token|id_token|session|sessionid|auth|"
    r"key|apikey|api_key|password|secret)=)[^&\s\"'<>]+",
    re.IGNORECASE,
)

SECCIONES = [
    ("Registro y DNS", ["whois_dominio", "dns_registros"]),
    ("Subdominios", ["subdominios_crtsh", "subdominios_subfinder"]),
    ("Infraestructura y servicios expuestos",
     ["netcraft_reporte", "servicios_expuestos"]),
    ("Ficheros públicos", ["ficheros_publicos"]),
    ("OSINT", ["google_dorks", "theharvester_osint"]),
]


def extraer_dominio(texto: str) -> str:
    """Devuelve el primer dominio que aparezca en el texto, o ''."""
    m = PATRON_DOMINIO.search(texto or "")
    return m.group(1).lower().rstrip(".") if m else ""


def enmascarar_emails(texto: str) -> str:
    """Deja solo la primera letra del usuario y el dominio del correo."""
    return PATRON_EMAIL.sub(lambda m: m.group(1) + "***@" + m.group(2), str(texto))


def redactar(texto: str) -> str:
    """Enmascara correos y valores de parámetros sensibles (tokens, sesiones...)."""
    texto = enmascarar_emails(texto)
    return PATRON_SECRETO.sub(lambda m: m.group(1) + "***", texto)


def llamadas(dominio: str) -> list[tuple[str, dict]]:
    """Orden fijo de llamadas pasivas para un dominio."""
    pasos = [("whois_dominio", {"dominio": dominio})]
    pasos += [("dns_registros", {"dominio": dominio, "tipo": tipo})
              for tipo in TIPOS_DNS]
    pasos += [
        ("subdominios_crtsh", {"dominio": dominio}),
        ("subdominios_subfinder", {"dominio": dominio}),
        ("netcraft_reporte", {"dominio": dominio}),
        ("ficheros_publicos", {"dominio": dominio}),
        ("servicios_expuestos", {"dominio": dominio}),
    ]
    pasos += [("google_dorks", {"dominio": dominio, "categoria": categoria})
              for categoria in CATEGORIAS_DORK]
    pasos.append(("theharvester_osint", {"dominio": dominio}))
    return pasos


def _bloque(resultado: str) -> str:
    """Texto seguro para un bloque de código Markdown."""
    return str(resultado).strip().replace("```", "'''")


def _estado(resultado: str) -> str:
    if resultado.startswith("BLOQUEADO"):
        return "bloqueado"
    if resultado.startswith("ERROR") or "\nERROR:" in resultado:
        return "error"
    return "ok"


def _informe(dominio: str, scope, resultados: list[tuple[str, dict, str]]) -> str:
    incluir, excluir = scope
    total = len(resultados)
    bloqueadas = sum(1 for _, _, r in resultados if _estado(r) == "bloqueado")
    errores = sum(1 for _, _, r in resultados if _estado(r) == "error")
    usadas = sorted({n for n, _, r in resultados if _estado(r) != "bloqueado"})
    fecha = datetime.now().astimezone().isoformat(timespec="seconds")

    lineas = [
        "# Informe de reconocimiento pasivo (modo automático sin IA)",
        "",
        f"> Generado el {fecha} por `reconocimiento.py` (sin modelo de IA).",
        "> Es una recopilación automática de las herramientas, no una redacción del",
        "> agente. Cada bloque indica la herramienta que respalda el dato. Úsalo como",
        "> evidencia o como respaldo si el servicio de IA no está disponible.",
        "",
        "## 1. Resumen ejecutivo",
        "",
        f"- Dominio analizado: `{dominio}`.",
        f"- Llamadas ejecutadas: {total}.",
        f"- Llamadas bloqueadas por el scope-guard: {bloqueadas}.",
        f"- Llamadas con error: {errores}.",
        "- Herramientas usadas: " + (", ".join(f"`{n}`" for n in usadas) or "ninguna") + ".",
        "- Solo reconocimiento pasivo: WHOIS, DNS, certificados, fuentes de terceros",
        "  y un GET a rutas públicas fijas.",
        "",
        "## 2. Alcance autorizado y activos analizados",
        "",
        "- Incluido: " + (", ".join(incluir) or "(vacío)") + ".",
        "- Excluido: " + (", ".join(excluir) or "ninguna exclusión explícita") + ".",
        f"- Objetivo de esta ejecución: `{dominio}`.",
        "",
    ]

    numero = 3
    for titulo, nombres in SECCIONES:
        lineas += [f"## {numero}. {titulo}", ""]
        encontrados = [x for x in resultados if x[0] in nombres]
        if not encontrados:
            lineas += ["Sin llamadas registradas.", ""]
        for nombre, args, resultado in encontrados:
            detalle = ", ".join(f"{k}={v}" for k, v in args.items() if k != "dominio")
            cabecera = f"### `{nombre}`" + (f" ({detalle})" if detalle else "")
            lineas += [
                cabecera,
                "",
                f"Fuente: `{nombre}`. Estado: {_estado(resultado)}.",
                "",
                "```text",
                redactar(_bloque(resultado)),
                "```",
                "",
            ]
        numero += 1

    lineas += [
        f"## {numero}. Observaciones y riesgos potenciales",
        "",
        "- Este modo no interpreta los datos: se limita a recopilarlos y citar la",
        "  herramienta que los devolvió.",
        "- Los puertos, CPEs y CVEs de `servicios_expuestos` son indicios de una",
        "  fuente pasiva, no vulnerabilidades confirmadas.",
        "- Los subdominios y URLs mostrados ya están filtrados por el alcance.",
        "- Los correos se muestran enmascarados; no se publican listas de datos",
        "  personales.",
        "- `ficheros_publicos` solo pidió rutas estándar fijas; no se crawleó ni se",
        "  fuzzeó ninguna ruta.",
        "",
        f"## {numero + 1}. Limitaciones y fuentes que fallaron",
        "",
    ]
    fallidas = [(n, r) for n, _, r in resultados if _estado(r) != "ok"]
    if not fallidas:
        lineas += ["- Ninguna llamada falló ni quedó bloqueada.", ""]
    else:
        for nombre, resultado in fallidas:
            lineas.append(f"- `{nombre}`: {_estado(resultado)}. "
                          f"{redactar(_bloque(resultado).splitlines()[0])[:300]}")
        lineas.append("")
    lineas += [
        "---",
        "",
        "Traza completa y auditable: `salida/traza.jsonl`.",
        "Para verla en formato legible: `.venv/bin/python ver_traza.py`.",
        "",
    ]
    return "\n".join(lineas)


def ejecutar(dominio: str, herramientas, scope, traza) -> str:
    """Ejecuta las herramientas en orden fijo y devuelve el informe en Markdown."""
    if not en_alcance(dominio, scope):
        raise ValueError(f"{dominio} está fuera del alcance autorizado.")

    fijar_scope(scope)
    por_nombre = {h.__name__: h for h in herramientas}
    traza.evento("inicio", objetivo=f"modo automático sobre {dominio}",
                 modelo="modo-automatico",
                 herramientas=sorted(por_nombre))

    resultados = []
    for paso, (nombre, args) in enumerate(llamadas(dominio), 1):
        herramienta = por_nombre.get(nombre)
        if herramienta is None:
            resultado = f"ERROR: la herramienta {nombre} no está activa."
        else:
            try:
                resultado = str(herramienta(**args))
            except Exception as e:  # los errores se registran, no rompen la ejecución
                resultado = f"ERROR: {nombre} falló: {e}"
        traza.evento(
            "herramienta", paso=paso, nombre=nombre,
            argumentos=json.dumps(args, ensure_ascii=False),
            resultado=resultado, bloqueado=resultado.startswith("BLOQUEADO"),
        )
        resultados.append((nombre, args, resultado))

    informe = _informe(dominio, scope, resultados)
    traza.evento("fin", paso=len(resultados), informe=informe,
                 tokens={"entrada": 0, "salida": 0})
    return informe
