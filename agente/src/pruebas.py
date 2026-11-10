"""Genera el documento de pruebas de alcance e instrucciones.

Cada ejecución deja `salida/pruebas.md` con las comprobaciones de:
- `scope.txt`: reglas válidas, casos dentro/fuera y normalización de URLs.
- `instrucciones.md`: placeholders, prompt construido, herramientas activas y
  avisos si se han perdido secciones o límites importantes.

No llama al modelo ni hace peticiones de red: solo comprueba los archivos y las
funciones que ya usa el agente.
"""

import hashlib
import ipaddress
import re
from datetime import datetime
from pathlib import Path

from alcance import en_alcance, normalizar

PATRON_DOMINIO = re.compile(
    r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}"
)
PATRON_PLACEHOLDER = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

SECCIONES_PROMPT = (
    "## Objetivo y alcance",
    "## Herramientas disponibles",
    "## Orden de trabajo",
    "## Límites",
    "## Informe",
)
CLAVES_PROMPT = ("BLOQUEADO", "pasivo", "Prohibido", "informe")


def _sha256(ruta: Path) -> str:
    try:
        return hashlib.sha256(ruta.read_bytes()).hexdigest()
    except OSError:
        return "no disponible"


def _celda(texto) -> str:
    return str(texto).replace("|", "\\|").replace("\n", " ")[:300]


def _bloque(texto: str) -> str:
    return str(texto).strip().replace("```", "'''").replace("~~~", "~ ~ ~")


def _tipo(regla: str) -> str:
    if regla.startswith("*."):
        return "comodín"
    if "/" in regla:
        return "rango CIDR"
    try:
        ipaddress.ip_address(regla)
        return "IP"
    except ValueError:
        return "dominio"


def _valida(regla: str) -> bool:
    if not regla:
        return False
    if "/" in regla:
        try:
            ipaddress.ip_network(regla, strict=False)
            return True
        except ValueError:
            return False
    base = regla[2:] if regla.startswith("*.") else regla
    try:
        ipaddress.ip_address(base)
        return True
    except ValueError:
        return bool(PATRON_DOMINIO.fullmatch(base))


def _muestra(regla: str) -> str:
    """Objetivo de ejemplo que debería entrar por esa regla."""
    if regla.startswith("*."):
        return "prueba." + regla[2:]
    if "/" in regla:
        return str(ipaddress.ip_network(regla, strict=False).network_address)
    return regla


def _dominio_base(incluir: list[str]) -> str:
    for regla in incluir:
        base = regla[2:] if regla.startswith("*.") else regla
        if "/" not in base and PATRON_DOMINIO.fullmatch(base):
            return base
    return ""


def _anadir(comprobaciones, nombre, estado, detalle=""):
    comprobaciones.append({"nombre": nombre, "estado": estado, "detalle": detalle})


def _scope(comprobaciones, scope, ruta: Path):
    incluir, excluir = scope
    _anadir(comprobaciones, "scope.txt existe", "OK" if ruta.exists() else "fallo",
            str(ruta))
    _anadir(comprobaciones, "scope.txt tiene inclusiones",
            "OK" if incluir else "fallo", f"{len(incluir)} inclusiones")

    invalidas = [r for r in incluir + excluir if not _valida(r)]
    _anadir(comprobaciones, "Todas las reglas tienen formato válido",
            "OK" if not invalidas else "fallo",
            "correcto" if not invalidas else ", ".join(invalidas[:10]))

    duplicadas = sorted({r for r in incluir + excluir
                         if (incluir + excluir).count(r) > 1})
    _anadir(comprobaciones, "Sin reglas duplicadas",
            "OK" if not duplicadas else "aviso",
            "ninguna" if not duplicadas else ", ".join(duplicadas[:10]))

    huerfanas = [r for r in excluir if not en_alcance(r, (incluir, []))]
    _anadir(comprobaciones, "Las exclusiones afectan a alguna inclusión",
            "OK" if not huerfanas else "aviso",
            "ninguna huérfana" if not huerfanas else ", ".join(huerfanas[:10]))

    for regla in incluir:
        muestra = _muestra(regla)
        dentro = en_alcance(muestra, scope)
        if dentro:
            estado, detalle = "OK", f"{muestra} entra"
        elif en_alcance(muestra, (incluir, [])):
            estado, detalle = "aviso", f"{muestra} lo excluye una regla !"
        else:
            estado, detalle = "fallo", f"{muestra} no entra"
        _anadir(comprobaciones, f"Regla de inclusión: {regla}", estado, detalle)

    base = _dominio_base(incluir)
    negativos = ["example.invalid", "sub.example.invalid", ""]
    if base:
        negativos.append(f"{base}.example.invalid")
    for objetivo in negativos:
        fuera = not en_alcance(objetivo, scope)
        _anadir(comprobaciones, f"Fuera de alcance: {objetivo or '(vacío)'}",
                "OK" if fuera else "fallo",
                "se queda fuera" if fuera else "entra por error")

    if incluir:
        muestra = _muestra(incluir[0])
        if ":" not in muestra:
            url = f"https://{muestra}:443/ruta?x=1"
            dentro = en_alcance(url, scope)
            _anadir(comprobaciones, "Normalización de URL con puerto y ruta",
                    "OK" if dentro else "fallo",
                    f"{url} -> {normalizar(url)}")


def _prompt(comprobaciones, scope, herramientas, plantilla, instrucciones,
            ruta: Path):
    incluir, excluir = scope
    _anadir(comprobaciones, "instrucciones.md existe",
            "OK" if ruta.exists() else "fallo", str(ruta))
    _anadir(comprobaciones, "La plantilla contiene {alcance}",
            "OK" if "{alcance}" in plantilla else "fallo",
            "encontrado" if "{alcance}" in plantilla else "falta")
    _anadir(comprobaciones, "La plantilla contiene {herramientas}",
            "OK" if "{herramientas}" in plantilla else "fallo",
            "encontrado" if "{herramientas}" in plantilla else "falta")

    restantes = [p for p in ("{alcance}", "{herramientas}") if p in instrucciones]
    _anadir(comprobaciones, "El prompt final no deja placeholders sin sustituir",
            "OK" if not restantes else "fallo",
            "sustituidos" if not restantes else ", ".join(restantes))

    desconocidos = sorted(set(PATRON_PLACEHOLDER.findall(instrucciones)))
    _anadir(comprobaciones, "Sin placeholders desconocidos en el prompt final",
            "OK" if not desconocidos else "aviso",
            "ninguno" if not desconocidos else ", ".join(desconocidos))

    faltan_alcance = [r for r in incluir + excluir if r not in instrucciones]
    _anadir(comprobaciones, "El prompt incluye todo el alcance",
            "OK" if not faltan_alcance else "fallo",
            "completo" if not faltan_alcance else ", ".join(faltan_alcance[:10]))

    sin_nombre = [h.__name__ for h in herramientas if h.__name__ not in instrucciones]
    _anadir(comprobaciones, "El prompt incluye todas las herramientas",
            "OK" if not sin_nombre else "fallo",
            f"{len(herramientas)} herramientas" if not sin_nombre
            else ", ".join(sin_nombre))

    nombres = [h.__name__ for h in herramientas]
    duplicadas = sorted({n for n in nombres if nombres.count(n) > 1})
    _anadir(comprobaciones, "Herramientas con nombres únicos",
            "OK" if not duplicadas else "fallo",
            "ninguna repetida" if not duplicadas else ", ".join(duplicadas))

    sin_proteger = [h.__name__ for h in herramientas
                    if not getattr(h, "protegida", False)]
    _anadir(comprobaciones, "Todas las herramientas están protegidas por el scope-guard",
            "OK" if not sin_proteger else "fallo",
            "todas protegidas" if not sin_proteger else ", ".join(sin_proteger))

    for titulo in SECCIONES_PROMPT:
        _anadir(comprobaciones, f"Sección del prompt: {titulo}",
                "OK" if titulo in instrucciones else "aviso",
                "presente" if titulo in instrucciones else "no encontrada")

    bajo = instrucciones.lower()
    faltan_claves = [c for c in CLAVES_PROMPT if c.lower() not in bajo]
    _anadir(comprobaciones, "El prompt mantiene los avisos clave",
            "OK" if not faltan_claves else "aviso",
            "todos presentes" if not faltan_claves else ", ".join(faltan_claves))

    _anadir(comprobaciones, "El prompt tiene contenido suficiente",
            "OK" if len(instrucciones) >= 500 else "aviso",
            f"{len(instrucciones)} caracteres")


def _tabla(comprobaciones) -> list[str]:
    lineas = ["| # | Comprobación | Resultado | Detalle |",
              "|---|---|---|---|"]
    for i, c in enumerate(comprobaciones, 1):
        lineas.append(f"| {i} | {_celda(c['nombre'])} | {c['estado']} | "
                      f"{_celda(c['detalle'])} |")
    return lineas


def generar(scope, herramientas, plantilla: str, instrucciones: str,
            ruta_scope: str | Path, ruta_instrucciones: str | Path,
            modo: str = "IA") -> str:
    """Devuelve el Markdown de `pruebas.md`."""
    ruta_scope = Path(ruta_scope)
    ruta_instrucciones = Path(ruta_instrucciones)
    incluir, excluir = scope

    comprobaciones_scope = []
    comprobaciones_prompt = []
    _scope(comprobaciones_scope, scope, ruta_scope)
    _prompt(comprobaciones_prompt, scope, herramientas, plantilla, instrucciones,
            ruta_instrucciones)
    comprobaciones = comprobaciones_scope + comprobaciones_prompt

    fallos = sum(1 for c in comprobaciones if c["estado"] == "fallo")
    avisos = sum(1 for c in comprobaciones if c["estado"] == "aviso")
    resultado = "FALLO" if fallos else ("OK con avisos" if avisos else "OK")
    fecha = datetime.now().astimezone().isoformat(timespec="seconds")

    lineas = [
        "# Pruebas de alcance e instrucciones",
        "",
        f"> Generado el {fecha} · modo: {modo}.",
        "> Comprueba `scope.txt` y el prompt construido desde `instrucciones.md`.",
        "> No llama al modelo ni hace peticiones de red.",
        "",
        "## 1. Resultado",
        "",
        f"- Resultado global: **{resultado}**.",
        f"- Comprobaciones: {len(comprobaciones)} "
        f"({len(comprobaciones) - fallos - avisos} OK, {avisos} avisos, "
        f"{fallos} fallos).",
        f"- Alcance: {len(incluir)} inclusiones y {len(excluir)} exclusiones.",
        f"- Herramientas activas: {len(herramientas)}.",
        f"- Prompt construido: {len(instrucciones)} caracteres.",
        "",
        "## 2. Archivos comprobados",
        "",
        "| Archivo | SHA-256 |",
        "|---|---|",
        f"| `{_celda(ruta_scope.name)}` | `{_sha256(ruta_scope)}` |",
        f"| `{_celda(ruta_instrucciones.name)}` | "
        f"`{_sha256(ruta_instrucciones)}` |",
        "",
        "## 3. Comprobaciones de `scope.txt`",
        "",
    ]
    lineas += _tabla(comprobaciones_scope)
    lineas += ["", "### 3.1 Reglas cargadas", "",
               "| # | Regla | Tipo |", "|---|---|---|"]
    for i, regla in enumerate(incluir, 1):
        lineas.append(f"| {i} | `{_celda(regla)}` | {_tipo(regla)} |")
    for i, regla in enumerate(excluir, 1):
        lineas.append(f"| !{len(incluir) + i} | `!{_celda(regla)}` | exclusión |")
    lineas += ["", "## 4. Comprobaciones de `instrucciones.md`", ""]
    lineas += _tabla(comprobaciones_prompt)
    lineas += ["", "### 4.1 Herramientas activas", "",
               "| Herramienta | Protegida | En el prompt |", "|---|---|---|"]
    for h in herramientas:
        lineas.append(f"| `{h.__name__}` | "
                      f"{'sí' if getattr(h, 'protegida', False) else 'no'} | "
                      f"{'sí' if h.__name__ in instrucciones else 'no'} |")
    lineas += [
        "",
        "## 5. Cómo reproducir",
        "",
        "```bash",
        "python3 lanzar.py --ver-prompt      # ver el prompt construido",
        "python3 -m pytest",
        "```",
        "",
        "## Anexo: prompt construido",
        "",
        "```text",
        _bloque(instrucciones),
        "```",
        "",
    ]
    return "\n".join(lineas)
