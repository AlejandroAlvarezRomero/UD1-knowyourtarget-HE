"""Lanza el agente de reconocimiento.

    # Clave con límite de gasto puesto en el proveedor, en el entorno o en .env:
    echo 'AAP_API_KEY=...' > .env && chmod 600 .env      # y AAP_URL si no es OpenRouter
    python lanzar.py "Investiga empresa.com"
"""

import argparse
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).parent
for carpeta in ("alcance", "motor", "herramientas"):
    sys.path.insert(0, str(RAIZ / carpeta))

from agente import Agente, LimiteAlcanzado  # noqa: E402
from alcance import cargar, en_alcance      # noqa: E402
from modelo import Modelo                   # noqa: E402
from prompt import construir                # noqa: E402
from pruebas import generar as generar_pruebas  # noqa: E402
from traza import Traza                     # noqa: E402
from whois import whois_dominio             # noqa: E402
from tus_herramientas import (              # noqa: E402
    dns_registros,
    subdominios_crtsh,
    subdominios_subfinder,
    netcraft_reporte,
    ficheros_publicos,
    servicios_expuestos,
    google_dorks,
    theharvester_osint,
)

HERRAMIENTAS = [
    whois_dominio,
    dns_registros,
    subdominios_crtsh,
    subdominios_subfinder,
    netcraft_reporte,
    ficheros_publicos,
    servicios_expuestos,
    google_dorks,
    theharvester_osint,
]


def cargar_env(ruta: Path) -> None:
    """Lee CLAVE=valor de .env sin pisar lo que ya esté en el entorno."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if "=" in linea and not linea.lstrip().startswith("#"):
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip().strip("\"'"))


def main():
    cargar_env(RAIZ / ".env")
    p = argparse.ArgumentParser()
    p.add_argument("objetivo", nargs="?", help="lo que le pides al agente")
    p.add_argument("--modelo", default=os.environ.get("AAP_MODELO", "openai/gpt-4o-mini"))
    p.add_argument("--max-pasos", type=int, default=20)
    p.add_argument("--max-tokens", type=int, default=80_000)
    p.add_argument("--ver-prompt", action="store_true",
                   help="muestra el prompt de sistema ya montado y sale (no llama al modelo)")
    p.add_argument("--sin-ia", action="store_true",
                   help="ejecuta las herramientas en orden fijo sin llamar al modelo (respaldo)")
    p.add_argument("--dominio",
                   help="dominio objetivo para --sin-ia (si no, se toma del objetivo)")
    a = p.parse_args()

    scope = cargar(RAIZ / "scope.txt")
    plantilla = (RAIZ / "instrucciones.md").read_text(encoding="utf-8")
    instrucciones = construir(plantilla, scope, HERRAMIENTAS)

    if a.ver_prompt:
        print(instrucciones)
        return

    salida = RAIZ / "salida"
    salida.mkdir(parents=True, exist_ok=True)
    pruebas = generar_pruebas(
        scope, HERRAMIENTAS, plantilla, instrucciones,
        RAIZ / "scope.txt", RAIZ / "instrucciones.md",
        modo="sin IA" if a.sin_ia else "IA",
    )
    (salida / "pruebas.md").write_text(pruebas, encoding="utf-8")

    if a.sin_ia:
        from reconocimiento import ejecutar as ejecutar_automatico, extraer_dominio

        dominio = (a.dominio or extraer_dominio(a.objetivo or "")).strip().lower()
        if not dominio:
            p.error("--sin-ia necesita --dominio o un objetivo que contenga un dominio")
        if not en_alcance(dominio, scope):
            p.error(f"{dominio} está fuera del alcance autorizado (revisa scope.txt)")
        traza = Traza(salida / "traza.jsonl")
        informe = ejecutar_automatico(dominio, HERRAMIENTAS, scope, traza)
        (salida / "informe.md").write_text(informe, encoding="utf-8")
        print(informe)
        print(f"\nDocumentos: {salida / 'informe.md'}, {salida / 'traza.jsonl'} "
              f"y {salida / 'pruebas.md'}", file=sys.stderr)
        return

    if not a.objetivo:
        p.error("falta el objetivo (o usa --ver-prompt para ver el prompt)")

    traza = Traza(salida / "traza.jsonl")
    agente = None
    modelo = None
    try:
        modelo = Modelo(a.modelo)
        agente = Agente(
            modelo=modelo,
            instrucciones=instrucciones,
            herramientas=HERRAMIENTAS,
            scope=scope,
            traza=traza,
            max_pasos=a.max_pasos,
            max_tokens=a.max_tokens,
        )
        informe = agente.ejecutar(a.objetivo)
    except LimiteAlcanzado as e:
        informe = (
            "# Informe incompleto\n\n"
            f"La ejecución se detuvo: {e}.\n\n"
            f"- Objetivo: {a.objetivo}\n"
            f"- Modelo: {modelo.nombre if modelo else a.modelo}\n"
            f"- Traza completa: `salida/traza.jsonl`\n\n"
            "Revisa la traza para ver las herramientas ejecutadas y los datos obtenidos."
        )
        traza.evento("error", motivo="limite", mensaje=str(e))
        (salida / "informe.md").write_text(informe, encoding="utf-8")
        print(informe)
        print(f"Parado: {e}", file=sys.stderr)
        print(f"Documentos: {salida / 'informe.md'}, {salida / 'traza.jsonl'} "
              f"y {salida / 'pruebas.md'}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        informe = (
            "# Informe no generado\n\n"
            f"La ejecución falló: {e}\n\n"
            f"- Objetivo: {a.objetivo}\n"
            f"- Modelo: {modelo.nombre if modelo else a.modelo}\n"
            f"- Traza: `salida/traza.jsonl`\n"
        )
        traza.evento("error", motivo="excepcion", mensaje=str(e))
        (salida / "informe.md").write_text(informe, encoding="utf-8")
        print(informe)
        print(f"Error: {e}", file=sys.stderr)
        print(f"Documentos: {salida / 'informe.md'}, {salida / 'traza.jsonl'} "
              f"y {salida / 'pruebas.md'}", file=sys.stderr)
        sys.exit(1)

    (salida / "informe.md").write_text(informe, encoding="utf-8")
    print(informe)
    print(f"\nTokens: {agente.tokens}", file=sys.stderr)
    print(f"Documentos: {salida / 'informe.md'}, {salida / 'traza.jsonl'} "
          f"y {salida / 'pruebas.md'}", file=sys.stderr)


if __name__ == "__main__":
    main()
