"""Herramientas iniciales: proceso y HTTP simulados, sin red ni tokens."""

import io
import json
import subprocess
import sys
import urllib.error
from pathlib import Path
from unittest.mock import Mock

import pytest

RAIZ = Path(__file__).parents[1]
for carpeta in ("", "alcance", "motor", "herramientas"):
    sys.path.insert(0, str(RAIZ / carpeta))

import guard
import lanzar
import tus_herramientas as tools
from prompt import construir


@pytest.fixture(autouse=True)
def scope(monkeypatch):
    monkeypatch.setattr(guard, "SCOPE", (["empresa.com", "*.empresa.com"], ["blog.empresa.com"]))


def test_herramientas_disponibles_en_prompt_y_motor(tmp_path):
    assert [h.__name__ for h in lanzar.HERRAMIENTAS] == [
        "whois_dominio", "dns_registros", "subdominios_crtsh",
        "subdominios_subfinder", "netcraft_reporte", "ficheros_publicos",
        "servicios_expuestos", "google_dorks", "theharvester_osint",
    ]
    instrucciones = construir("{alcance}\n{herramientas}", guard.SCOPE, lanzar.HERRAMIENTAS)
    agente = lanzar.Agente(object(), instrucciones, lanzar.HERRAMIENTAS, guard.SCOPE,
                          lanzar.Traza(tmp_path / "traza.jsonl"))
    assert len(agente.esquemas) == 9
    assert all(h.__name__ in instrucciones for h in lanzar.HERRAMIENTAS)


@pytest.mark.parametrize("herramienta", [tools.dns_registros, tools.subdominios_crtsh])
@pytest.mark.parametrize("dominio", ["otraempresa.com", "blog.empresa.com"])
def test_scope_bloquea_antes_de_cualquier_consulta(monkeypatch, herramienta, dominio):
    proceso = Mock(side_effect=AssertionError("No debe ejecutar un proceso"))
    http = Mock(side_effect=AssertionError("No debe acceder a la red"))
    monkeypatch.setattr(tools.subprocess, "run", proceso)
    monkeypatch.setattr(tools.urllib.request, "urlopen", http)
    assert herramienta(dominio=dominio).startswith("BLOQUEADO")
    proceso.assert_not_called()
    http.assert_not_called()


def test_dns_consulta_sin_shell_y_con_timeout(monkeypatch):
    proceso = Mock(return_value=subprocess.CompletedProcess([], 0, "ns1.empresa.com.\n", ""))
    monkeypatch.setattr(tools.subprocess, "run", proceso)
    assert tools.dns_registros(dominio="empresa.com", tipo="ns") == "ns1.empresa.com."
    proceso.assert_called_once_with(["dig", "+short", "NS", "empresa.com"],
                                    capture_output=True, text=True, timeout=20)


def test_dns_rechaza_tipo_no_permitido(monkeypatch):
    proceso = Mock()
    monkeypatch.setattr(tools.subprocess, "run", proceso)
    assert tools.dns_registros(dominio="empresa.com", tipo="AXFR").startswith("ERROR")
    proceso.assert_not_called()


@pytest.mark.parametrize("error", [FileNotFoundError("dig"), subprocess.TimeoutExpired("dig", 20)])
def test_dns_errores_como_texto(monkeypatch, error):
    monkeypatch.setattr(tools.subprocess, "run", Mock(side_effect=error))
    assert tools.dns_registros(dominio="empresa.com").startswith("ERROR")


def test_dns_no_confunde_error_del_proceso_con_ausencia_de_registros(monkeypatch):
    monkeypatch.setattr(tools.subprocess, "run", Mock(return_value=
                        subprocess.CompletedProcess([], 9, "", "consulta fallida")))
    assert "consulta fallida" in tools.dns_registros(dominio="empresa.com")


@pytest.mark.parametrize("salida", ["", "x" * 5000])
def test_dns_sin_registros_o_salida_recortada(monkeypatch, salida):
    monkeypatch.setattr(tools.subprocess, "run", Mock(return_value=
                        subprocess.CompletedProcess([], 0, salida, "")))
    resultado = tools.dns_registros(dominio="empresa.com")
    assert "Sin registros" in resultado if not salida else "recortado" in resultado


def test_crtsh_consulta_publica_deduplica_y_filtra(monkeypatch):
    datos = [{"name_value": "*.empresa.com\nAPI.empresa.com\napi.empresa.com"},
             {"name_value": "blog.empresa.com\notro.net\nwww.empresa.com"}]
    http = Mock(return_value=io.BytesIO(json.dumps(datos).encode()))
    monkeypatch.setattr(tools.urllib.request, "urlopen", http)
    resultado = tools.subdominios_crtsh(dominio="empresa.com")
    assert resultado.splitlines() == [
        "3 subdominios en alcance (2 filtrados por estar fuera):",
        "api.empresa.com", "empresa.com", "www.empresa.com",
    ]
    req = http.call_args.args[0]
    assert req.full_url == "https://crt.sh/?q=%25.empresa.com&output=json"
    assert http.call_args.kwargs == {"timeout": 90}


@pytest.mark.parametrize("datos", [[], [{"name_value": "x.empresa.com\ny.empresa.com"}]])
def test_crtsh_respeta_scope_sin_comodin(monkeypatch, datos):
    monkeypatch.setattr(guard, "SCOPE", (["empresa.com"], []))
    monkeypatch.setattr(tools.urllib.request, "urlopen", Mock(return_value=
                        io.BytesIO(json.dumps(datos).encode())))
    resultado = tools.subdominios_crtsh(dominio="empresa.com")
    assert resultado.startswith("0 subdominios en alcance")
    assert "x.empresa.com" not in resultado


@pytest.mark.parametrize("contenido", [b"<html>error</html>", b'{}', b'[null]', b'[{"name_value": null}]'])
def test_crtsh_respuesta_invalida_como_texto(monkeypatch, contenido):
    monkeypatch.setattr(tools.urllib.request, "urlopen", Mock(return_value=io.BytesIO(contenido)))
    assert tools.subdominios_crtsh(dominio="empresa.com").startswith("ERROR")


def test_crtsh_caido_recomienda_herramienta_existente(monkeypatch):
    monkeypatch.setattr(tools.time, "sleep", Mock())
    monkeypatch.setattr(tools.urllib.request, "urlopen", Mock(side_effect=TimeoutError("agotado")))
    resultado = tools.subdominios_crtsh(dominio="empresa.com")
    assert resultado.startswith("ERROR")
    assert "subdominios_subfinder" in resultado
    assert "subdominios_subfinder" in [h.__name__ for h in lanzar.HERRAMIENTAS]


def test_crtsh_reintenta_si_falla_la_primera_vez(monkeypatch):
    monkeypatch.setattr(tools.time, "sleep", Mock())
    datos = [{"name_value": "www.empresa.com"}]
    http = Mock(side_effect=[
        urllib.error.HTTPError("https://crt.sh/", 502, "Bad Gateway", {}, None),
        io.BytesIO(json.dumps(datos).encode()),
    ])
    monkeypatch.setattr(tools.urllib.request, "urlopen", http)
    resultado = tools.subdominios_crtsh(dominio="empresa.com")
    assert "www.empresa.com" in resultado
    assert http.call_count == 2


def test_crtsh_recorta_resultados_largos(monkeypatch):
    datos = [{"name_value": "\n".join(f"host{i:04}.empresa.com" for i in range(1000))}]
    monkeypatch.setattr(tools.urllib.request, "urlopen", Mock(return_value=
                        io.BytesIO(json.dumps(datos).encode())))
    assert "recortado" in tools.subdominios_crtsh(dominio="empresa.com")


# ---------------------------------------------------------------------------
# Herramientas nuevas
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("herramienta", [
    tools.subdominios_subfinder, tools.netcraft_reporte, tools.ficheros_publicos,
    tools.servicios_expuestos, tools.google_dorks, tools.theharvester_osint,
])
def test_scope_bloquea_nuevas_herramientas(monkeypatch, herramienta):
    proceso = Mock(side_effect=AssertionError("No debe ejecutar un proceso"))
    http = Mock(side_effect=AssertionError("No debe acceder a la red"))
    abrir = Mock(side_effect=AssertionError("No debe abrir red"))
    monkeypatch.setattr(tools.subprocess, "run", proceso)
    monkeypatch.setattr(tools.urllib.request, "urlopen", http)
    monkeypatch.setattr(tools, "_abrir", abrir)
    assert herramienta(dominio="otraempresa.com").startswith("BLOQUEADO")
    proceso.assert_not_called()
    http.assert_not_called()
    abrir.assert_not_called()


@pytest.mark.parametrize("tipo", ["CAA", "SRV"])
def test_dns_acepta_caa_y_srv(monkeypatch, tipo):
    proceso = Mock(return_value=subprocess.CompletedProcess([], 0, "valor\n", ""))
    monkeypatch.setattr(tools.subprocess, "run", proceso)
    assert tools.dns_registros(dominio="empresa.com", tipo=tipo) == "valor"
    proceso.assert_called_once_with(["dig", "+short", tipo, "empresa.com"],
                                    capture_output=True, text=True, timeout=20)


def test_subfinder_lista_sin_shell_y_filtra(monkeypatch):
    salida = ("www.empresa.com\nAPI.empresa.com\nblog.empresa.com\n"
              "otro.net\n*.empresa.com\n")
    proceso = Mock(return_value=subprocess.CompletedProcess([], 0, salida, ""))
    monkeypatch.setattr(tools.subprocess, "run", proceso)
    resultado = tools.subdominios_subfinder(dominio="empresa.com")
    assert "www.empresa.com" in resultado
    assert "api.empresa.com" in resultado
    assert "blog.empresa.com" not in resultado
    assert "otro.net" not in resultado
    argumentos, opciones = proceso.call_args
    assert argumentos[0][0] == "subfinder"
    assert "shell" not in opciones
    assert opciones["timeout"] == 150


@pytest.mark.parametrize("error", [
    FileNotFoundError("subfinder"),
    subprocess.TimeoutExpired("subfinder", 150),
])
def test_subfinder_errores_como_texto(monkeypatch, error):
    monkeypatch.setattr(tools.subprocess, "run", Mock(side_effect=error))
    assert tools.subdominios_subfinder(dominio="empresa.com").startswith("ERROR")


def test_subfinder_recorta_resultados_largos(monkeypatch):
    salida = "\n".join(f"host{i:04}.empresa.com" for i in range(1000))
    monkeypatch.setattr(tools.subprocess, "run", Mock(return_value=
                        subprocess.CompletedProcess([], 0, salida, "")))
    assert "recortado" in tools.subdominios_subfinder(dominio="empresa.com")


NETCRAFT_HTML = """
<table>
<tr><th>Hosting company</th><td>Cloudflare</td></tr>
<tr><th>Hosting country</th><td>US</td></tr>
<tr><th>IPv4 address</th><td><span>1.2.3.4</span></td></tr>
<tr><th>Nameserver</th><td>ns1.empresa.com</td></tr>
<tr><th>Domain registrar</th><td>MarkMonitor</td></tr>
<tr><th>DNS Security Extensions</th><td>Enabled</td></tr>
</table>
"""


def test_netcraft_parsea_tabla(monkeypatch):
    http = Mock(return_value=io.BytesIO(NETCRAFT_HTML.encode()))
    monkeypatch.setattr(tools.urllib.request, "urlopen", http)
    resultado = tools.netcraft_reporte(dominio="empresa.com")
    assert "Hosting company: Cloudflare" in resultado
    assert "IPv4 address: 1.2.3.4" in resultado
    assert "Nameserver: ns1.empresa.com" in resultado
    assert "DNS Security Extensions: Enabled" in resultado


def test_netcraft_respuesta_invalida_como_texto(monkeypatch):
    monkeypatch.setattr(tools.urllib.request, "urlopen", Mock(return_value=
                        io.BytesIO(b"<html>sin tabla</html>")))
    assert tools.netcraft_reporte(dominio="empresa.com").startswith("ERROR")


class RespuestaFalsa:
    def __init__(self, texto, status=200):
        self._datos = texto.encode()
        self.status = status

    def read(self, n=-1):
        return self._datos if n < 0 else self._datos[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_ficheros_publicos_solo_rutas_fijas(monkeypatch):
    llamadas = []

    def abrir(req, timeout=0):
        llamadas.append(req.full_url)
        if req.full_url.endswith("/robots.txt"):
            return RespuestaFalsa("User-agent: *\nDisallow: /admin\n")
        if req.full_url.endswith("/.well-known/security.txt"):
            return RespuestaFalsa("Contact: mailto:security@empresa.com\n")
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr(tools, "_abrir", abrir)
    resultado = tools.ficheros_publicos(dominio="empresa.com")
    assert "Disallow: /admin" in resultado
    assert "security@empresa.com" in resultado
    assert "HTTP 404" in resultado
    assert len(llamadas) == 4
    assert all(u.startswith("https://empresa.com/") for u in llamadas)
    assert all(p in llamadas for p in [
        "https://empresa.com/robots.txt",
        "https://empresa.com/.well-known/security.txt",
        "https://empresa.com/security.txt",
        "https://empresa.com/sitemap.xml",
    ])


def test_ficheros_publicos_recorta(monkeypatch):
    monkeypatch.setattr(tools, "_abrir", lambda req, timeout=0: RespuestaFalsa("x" * 50_000))
    assert "recortado" in tools.ficheros_publicos(dominio="empresa.com")


def test_en_alcance_url_respeta_scope(monkeypatch):
    assert tools._en_alcance_url("https://api.empresa.com/x")
    assert not tools._en_alcance_url("https://otro.net/x")
    assert not tools._en_alcance_url("sin-esquema")


def test_servicios_expuestos_consulta_internetdb_y_filtra(monkeypatch):
    monkeypatch.delenv("SHODAN_API_KEY", raising=False)

    def dig(cmd, **kwargs):
        if cmd[2] == "A":
            return subprocess.CompletedProcess(cmd, 0, "1.2.3.4\n", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(tools.subprocess, "run", Mock(side_effect=dig))
    datos = {
        "ip": "1.2.3.4", "ports": [443, 80],
        "hostnames": ["www.empresa.com", "otro.net"],
        "cpes": ["cpe:/a:nginx"], "tags": ["cdn"],
        "vulns": ["CVE-2020-1234"],
    }
    monkeypatch.setattr(tools.urllib.request, "urlopen", Mock(return_value=
                        io.BytesIO(json.dumps(datos).encode())))
    resultado = tools.servicios_expuestos(dominio="empresa.com")
    assert "1.2.3.4" in resultado
    assert "80, 443" in resultado
    assert "www.empresa.com" in resultado
    assert "otro.net" not in resultado
    assert "CVE-2020-1234" in resultado


def test_servicios_expuestos_sin_ips(monkeypatch):
    monkeypatch.setattr(tools.subprocess, "run", Mock(return_value=
                        subprocess.CompletedProcess([], 0, "", "")))
    assert tools.servicios_expuestos(dominio="empresa.com").startswith("Sin direcciones")


def test_servicios_expuestos_404_como_texto(monkeypatch):
    def dig(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, "1.2.3.4\n" if cmd[2] == "A" else "", "")

    monkeypatch.setattr(tools.subprocess, "run", Mock(side_effect=dig))
    monkeypatch.setattr(tools.urllib.request, "urlopen", Mock(side_effect=
                        urllib.error.HTTPError("https://internetdb.shodan.io/1.2.3.4",
                                               404, "Not Found", {}, None)))
    assert "Sin datos en InternetDB" in tools.servicios_expuestos(dominio="empresa.com")


def test_servicios_expuestos_shodan_api_no_filtra_clave(monkeypatch):
    monkeypatch.setenv("SHODAN_API_KEY", "clave-secreta")

    def dig(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, "1.2.3.4\n" if cmd[2] == "A" else "", "")

    def http(req, timeout=0):
        if "internetdb" in req.full_url:
            return io.BytesIO(json.dumps({"ip": "1.2.3.4", "ports": [443]}).encode())
        return io.BytesIO(json.dumps({"org": "Sony", "ports": [443]}).encode())

    monkeypatch.setattr(tools.subprocess, "run", Mock(side_effect=dig))
    monkeypatch.setattr(tools.urllib.request, "urlopen", http)
    resultado = tools.servicios_expuestos(dominio="empresa.com")
    assert "Shodan API" in resultado
    assert "org=Sony" in resultado
    assert "clave-secreta" not in resultado


DDG_HTML = """
<a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.empresa.com%2Fadmin">Admin</a>
<a class="result__snippet">Panel de administración</a>
<a class="result__a" href="https://otro.net/x">Otro sitio</a>
"""


def test_google_dorks_usa_ddg_si_no_hay_claves(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CSE_ID", raising=False)
    http = Mock(return_value=io.BytesIO(DDG_HTML.encode()))
    monkeypatch.setattr(tools.urllib.request, "urlopen", http)
    resultado = tools.google_dorks(dominio="empresa.com", consulta="inurl:admin")
    assert "www.empresa.com/admin" in resultado
    assert "Panel de administración" in resultado
    assert "otro.net" not in resultado
    req = http.call_args.args[0]
    assert "site%3Aempresa.com" in req.data.decode()
    assert "inurl%3Aadmin" in req.data.decode()


def test_google_dorks_no_permite_cambiar_de_sitio(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CSE_ID", raising=False)
    http = Mock(return_value=io.BytesIO(DDG_HTML.encode()))
    monkeypatch.setattr(tools.urllib.request, "urlopen", http)
    tools.google_dorks(dominio="empresa.com", consulta="site:otro.net inurl:admin")
    req = http.call_args.args[0]
    assert "otro.net" not in req.data.decode()


def test_google_dorks_usa_google_cse_si_hay_claves(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "clave-google")
    monkeypatch.setenv("GOOGLE_CSE_ID", "cx-123")
    datos = {"items": [
        {"title": "Admin", "link": "https://www.empresa.com/admin", "snippet": "Panel"},
        {"title": "Otro", "link": "https://otro.net/x", "snippet": "Fuera"},
    ]}
    monkeypatch.setattr(tools.urllib.request, "urlopen", Mock(return_value=
                        io.BytesIO(json.dumps(datos).encode())))
    resultado = tools.google_dorks(dominio="empresa.com")
    assert "Google CSE" in resultado
    assert "www.empresa.com/admin" in resultado
    assert "otro.net" not in resultado
    assert "clave-google" not in resultado


def test_google_dorks_categoria_invalida():
    assert tools.google_dorks(dominio="empresa.com", categoria="nope").startswith("ERROR")


HARVESTER_SALIDA = """
[*] Target: empresa.com
[*] Emails found: 2
----------------------
john@empresa.com
jane@empresa.com
[*] Hosts found: 3
---------------------
www.empresa.com
blog.empresa.com
otro.net
[*] IPs found: 2
-------------------
1.2.3.4
5.6.7.8
[*] ASNS found: 1
--------------------
AS123
[*] Interesting Urls found: 2
--------------------
https://www.empresa.com/admin
https://otro.net/x
"""


def test_theharvester_parsea_y_enmascara(monkeypatch):
    proceso = Mock(return_value=subprocess.CompletedProcess([], 0, HARVESTER_SALIDA, ""))
    monkeypatch.setattr(tools.subprocess, "run", proceso)
    resultado = tools.theharvester_osint(dominio="empresa.com", limite=50)
    assert "j***@empresa.com" in resultado
    assert "john@empresa.com" not in resultado
    assert "www.empresa.com" in resultado
    assert "blog.empresa.com" not in resultado
    assert "otro.net" not in resultado
    assert "1.2.3.4" in resultado
    assert "AS123" in resultado
    assert "https://www.empresa.com/admin" in resultado
    argumentos, opciones = proceso.call_args
    assert argumentos[0][0] == "theHarvester"
    assert "shell" not in opciones
    assert opciones["timeout"] == 150


def test_theharvester_rechaza_fuentes_activas(monkeypatch):
    proceso = Mock(side_effect=AssertionError("No debe ejecutar"))
    monkeypatch.setattr(tools.subprocess, "run", proceso)
    assert tools.theharvester_osint(dominio="empresa.com", fuentes="nmap").startswith("ERROR")
    proceso.assert_not_called()


@pytest.mark.parametrize("error", [
    FileNotFoundError("theHarvester"),
    subprocess.TimeoutExpired("theHarvester", 150),
])
def test_theharvester_errores_como_texto(monkeypatch, error):
    monkeypatch.setattr(tools.subprocess, "run", Mock(side_effect=error))
    assert tools.theharvester_osint(dominio="empresa.com").startswith("ERROR")


def test_theharvester_sin_correos(monkeypatch):
    salida = "[*] No emails found.\n\n[*] No hosts found.\n"
    monkeypatch.setattr(tools.subprocess, "run", Mock(return_value=
                        subprocess.CompletedProcess([], 0, salida, "")))
    resultado = tools.theharvester_osint(dominio="empresa.com")
    assert "Correos encontrados: 0" in resultado
