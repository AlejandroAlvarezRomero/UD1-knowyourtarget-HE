"""Modo automático sin IA: informe y traza sin red ni modelo."""

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parents[1]
for carpeta in ("", "alcance", "motor", "herramientas"):
    sys.path.insert(0, str(RAIZ / carpeta))

import reconocimiento
from traza import Traza

SCOPE = (["empresa.com", "*.empresa.com"], ["blog.empresa.com"])


def herramienta(nombre, resultado):
    def f(**kwargs):
        return resultado
    f.__name__ = nombre
    f.protegida = True
    return f


def todas(resultado="dato"):
    nombres = ["whois_dominio", "dns_registros", "subdominios_crtsh",
               "subdominios_subfinder", "netcraft_reporte", "ficheros_publicos",
               "servicios_expuestos", "google_dorks", "theharvester_osint"]
    return [herramienta(n, resultado) for n in nombres]


def test_extraer_dominio():
    assert reconocimiento.extraer_dominio(
        "Analiza playstation.com y www.playstation.com") == "playstation.com"
    assert reconocimiento.extraer_dominio("sin dominio") == ""


def test_redacta_correos_y_parametros_sensibles():
    texto = ("https://x.test/auth?state=abc123&code=XYZ&page=1 "
             "Contacto: security@empresa.com")
    limpio = reconocimiento.redactar(texto)
    assert "abc123" not in limpio
    assert "XYZ" not in limpio
    assert "state=***" in limpio
    assert "code=***" in limpio
    assert "page=1" in limpio
    assert "s***@empresa.com" in limpio
    assert "security@empresa.com" not in limpio


def test_genera_informe_traza_y_enmascara(tmp_path):
    resultados = {
        "whois_dominio": "Registrador: MarkMonitor",
        "dns_registros": "1.2.3.4",
        "subdominios_crtsh": "api.empresa.com",
        "subdominios_subfinder": "www.empresa.com",
        "netcraft_reporte": "Hosting company: Cloudflare",
        "ficheros_publicos": "Contact: security@empresa.com",
        "servicios_expuestos": "Puertos: 443",
        "google_dorks": "1. Admin https://www.empresa.com/admin",
        "theharvester_osint": "j***@empresa.com",
    }
    herramientas = [herramienta(n, r) for n, r in resultados.items()]
    traza = Traza(tmp_path / "traza.jsonl")

    informe = reconocimiento.ejecutar("empresa.com", herramientas, SCOPE, traza)

    assert informe.startswith("# Informe de reconocimiento pasivo")
    assert "Fuente: `dns_registros`" in informe
    assert "1.2.3.4" in informe
    assert "s***@empresa.com" in informe
    assert "security@empresa.com" not in informe
    assert "Traza completa" in informe

    eventos = [json.loads(l) for l in
               (tmp_path / "traza.jsonl").read_text(encoding="utf-8").splitlines()]
    assert eventos[0]["tipo"] == "inicio"
    assert eventos[0]["modelo"] == "modo-automatico"
    assert eventos[-1]["tipo"] == "fin"
    assert sum(e["tipo"] == "herramienta" for e in eventos) == 19
    assert all(e["bloqueado"] is False for e in eventos
               if e["tipo"] == "herramienta")


def test_fuera_de_alcance_no_ejecuta(tmp_path):
    def no_llamar(**kwargs):
        raise AssertionError("no debe ejecutarse")

    herramientas = todas()
    herramientas[0] = no_llamar
    with pytest.raises(ValueError):
        reconocimiento.ejecutar("otro.net", herramientas, SCOPE,
                                Traza(tmp_path / "traza.jsonl"))


def test_herramienta_ausente_aparece_como_error(tmp_path):
    traza = Traza(tmp_path / "traza.jsonl")
    informe = reconocimiento.ejecutar(
        "empresa.com", [herramienta("whois_dominio", "dato")], SCOPE, traza)

    assert "no está activa" in informe
    assert "## 9. Limitaciones" in informe
    assert "`dns_registros`: error" in informe
