"""WHOIS: proceso simulado y reintento de RDAP, sin red ni tokens."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

RAIZ = Path(__file__).parents[1]
for carpeta in ("", "alcance", "motor", "herramientas"):
    sys.path.insert(0, str(RAIZ / carpeta))

import guard
import whois


@pytest.fixture(autouse=True)
def scope(monkeypatch):
    monkeypatch.setattr(guard, "SCOPE", (["empresa.com"], []))


def test_whois_usa_la_orden_si_responde(monkeypatch):
    proceso = Mock(return_value=subprocess.CompletedProcess(
        [], 0, "Domain Name: EMPRESA.COM\n", ""))
    rdap = Mock(side_effect=AssertionError("no debe usar RDAP"))
    monkeypatch.setattr(whois.subprocess, "run", proceso)
    monkeypatch.setattr(whois, "_rdap_una_vez", rdap)
    assert whois.whois_dominio(dominio="empresa.com").startswith("Domain Name")
    rdap.assert_not_called()


def test_whois_reintenta_rdap_una_vez(monkeypatch):
    monkeypatch.setattr(whois.subprocess, "run", Mock(return_value=
                        subprocess.CompletedProcess([], 1, "", "puerto cerrado")))
    rdap = Mock(side_effect=[ConnectionError("reset"), "Dominio: EMPRESA.COM"])
    monkeypatch.setattr(whois, "_rdap_una_vez", rdap)
    monkeypatch.setattr(whois.time, "sleep", Mock())
    assert whois.whois_dominio(dominio="empresa.com") == "Dominio: EMPRESA.COM"
    assert rdap.call_count == 2


def test_whois_error_final_como_texto(monkeypatch):
    monkeypatch.setattr(whois.subprocess, "run", Mock(return_value=
                        subprocess.CompletedProcess([], 1, "", "puerto cerrado")))
    monkeypatch.setattr(whois, "_rdap_una_vez", Mock(side_effect=ConnectionError("reset")))
    monkeypatch.setattr(whois.time, "sleep", Mock())
    resultado = whois.whois_dominio(dominio="empresa.com")
    assert resultado.startswith("ERROR")
    assert "RDAP" in resultado


def test_whois_bloquea_antes_de_ejecutar(monkeypatch):
    proceso = Mock(side_effect=AssertionError("no debe ejecutar"))
    monkeypatch.setattr(whois.subprocess, "run", proceso)
    assert whois.whois_dominio(dominio="otro.net").startswith("BLOQUEADO")
    proceso.assert_not_called()
