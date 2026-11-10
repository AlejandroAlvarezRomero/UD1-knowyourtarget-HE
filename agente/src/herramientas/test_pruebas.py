"""Documento de pruebas de alcance e instrucciones, sin red ni modelo."""

import sys
from pathlib import Path

RAIZ = Path(__file__).parents[1]
for carpeta in ("", "alcance", "motor", "herramientas"):
    sys.path.insert(0, str(RAIZ / carpeta))

import pruebas
from prompt import construir

PLANTILLA = """# Prompt
## Objetivo y alcance
{alcance}
## Herramientas disponibles
{herramientas}
## Orden de trabajo
1. Revisar.
## Límites
BLOQUEADO: fuera. Solo reconocimiento pasivo. Prohibido escanear.
## Informe
Termina con un informe.
"""


def herramienta(nombre, doc="Hace una comprobación.", protegida=True):
    def f(**kwargs):
        return ""
    f.__name__ = nombre
    f.__doc__ = doc
    f.protegida = protegida
    return f


HERRAMIENTAS = [
    herramienta("whois_dominio", "Consulta el registro WHOIS."),
    herramienta("dns_registros", "Consulta registros DNS."),
]


def generar(tmp_path, scope=(["empresa.com", "*.empresa.com"], []),
            herramientas=None, plantilla=PLANTILLA):
    herramientas = herramientas or HERRAMIENTAS
    (tmp_path / "scope.txt").write_text("empresa.com\n*.empresa.com\n",
                                        encoding="utf-8")
    (tmp_path / "instrucciones.md").write_text(plantilla, encoding="utf-8")
    instrucciones = construir(plantilla, scope, herramientas)
    return pruebas.generar(
        scope, herramientas, plantilla, instrucciones,
        tmp_path / "scope.txt", tmp_path / "instrucciones.md", modo="test",
    )


def test_genera_documento_completo(tmp_path):
    informe = generar(tmp_path)
    assert "# Pruebas de alcance e instrucciones" in informe
    assert "Resultado global: **OK" in informe
    assert "## 3. Comprobaciones de `scope.txt`" in informe
    assert "## 4. Comprobaciones de `instrucciones.md`" in informe
    assert "`whois_dominio`" in informe
    assert "| `whois_dominio` | sí | sí |" in informe
    assert "## Anexo: prompt construido" in informe
    assert "Autorizado: empresa.com" in informe


def test_detecta_placeholder_que_falta(tmp_path):
    plantilla = PLANTILLA.replace("{alcance}", "sin placeholder")
    informe = generar(tmp_path, plantilla=plantilla)
    assert "Resultado global: **FALLO**" in informe
    assert "La plantilla contiene {alcance}" in informe


def test_detecta_herramienta_sin_proteger(tmp_path):
    herramientas = [herramienta("whois_dominio", protegida=False)]
    informe = generar(tmp_path, herramientas=herramientas)
    assert "Resultado global: **FALLO**" in informe
    assert "Todas las herramientas están protegidas" in informe
    assert "`whois_dominio` | no | sí" in informe


def test_exclusion_valida(tmp_path):
    scope = (["empresa.com", "*.empresa.com"], ["blog.empresa.com"])
    informe = generar(tmp_path, scope=scope)
    assert "!blog.empresa.com" in informe
    assert "Resultado global: **OK" in informe


def test_regla_invalida(tmp_path):
    scope = (["empresa.com", "no valido!!"], [])
    informe = generar(tmp_path, scope=scope)
    assert "Resultado global: **FALLO**" in informe
    assert "Todas las reglas tienen formato válido" in informe
