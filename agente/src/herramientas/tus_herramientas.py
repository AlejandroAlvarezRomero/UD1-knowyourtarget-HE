"""Herramientas de reconocimiento. AQUÍ ESTÁN LAS HERRAMIENTAS ACTIVAS.

Reglas de todas las herramientas:
- Una tarea por función.
- Protegidas por el scope-guard con @protegida.
- Sin shell: lista de argumentos, nunca shell=True.
- Con tiempo máximo y salida recortada.
- Errores como texto, nunca excepciones hacia el motor.
- Los resultados que son nombres/URLs se filtran por el alcance.

whois_dominio está en whois.py. El resto vive aquí.
"""

import ipaddress
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from html import unescape

from guard import protegida, filtrar
from whois import recortar

UA = "aap-recon/1.0 (educativo; IES Rafael Alberti)"
TIPOS_DNS = {"A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "CAA", "SRV"}
MAX_SALIDA = 5000


# ---------------------------------------------------------------------------
# Utilidades HTTP
# ---------------------------------------------------------------------------

def _leer(respuesta, maximo: int) -> str:
    """Lee como texto y recorta por bytes para no llenar el contexto del modelo."""
    datos = respuesta.read(maximo + 1)
    texto = datos.decode("utf-8", "replace")
    if len(datos) > maximo:
        texto = texto[:maximo] + f"\n[... recortado: respuesta mayor de {maximo} bytes]"
    return texto


def _http(url: str, timeout: int = 30, maximo: int = 5_000_000) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return _leer(r, maximo)


def _http_post(url: str, datos: dict, timeout: int = 30, maximo: int = 2_000_000) -> str:
    cuerpo = urllib.parse.urlencode(datos).encode()
    req = urllib.request.Request(
        url, data=cuerpo,
        headers={"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return _leer(r, maximo)


def _host(url: str) -> str:
    try:
        return urllib.parse.urlsplit(url).hostname or ""
    except ValueError:
        return ""


def _en_alcance_url(url: str) -> bool:
    """True si el host de la URL está en el alcance actual."""
    host = _host(url)
    if not host:
        return False
    dentro, _ = filtrar([host])
    return bool(dentro)


class _RedirigeSoloAlcance(urllib.request.HTTPRedirectHandler):
    """Sigue redirecciones solo si el destino está en alcance y mantiene la ruta."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        destino = urllib.parse.urljoin(req.full_url, newurl)
        origen = urllib.parse.urlsplit(req.full_url)
        nuevo = urllib.parse.urlsplit(destino)
        if not _en_alcance_url(destino):
            return None
        if nuevo.path.rstrip("/") != origen.path.rstrip("/"):
            return None
        return super().redirect_request(req, fp, code, msg, headers, destino)


def _abrir(req, timeout: int):
    """Abre una petición con la política de redirecciones del agente."""
    return urllib.request.build_opener(_RedirigeSoloAlcance()).open(req, timeout=timeout)


# ---------------------------------------------------------------------------
# DNS
# ---------------------------------------------------------------------------

@protegida(objetivo="dominio")
def dns_registros(dominio: str, tipo: str = "A") -> str:
    """Consulta registros DNS con dig. tipo: A, AAAA, MX, NS, TXT, CNAME, SOA, CAA o SRV.
    Devuelve los valores, uno por línea."""
    tipo = tipo.upper()
    if tipo not in TIPOS_DNS:
        return f"ERROR: tipo DNS no válido ({tipo}). Usa uno de: {', '.join(sorted(TIPOS_DNS))}."
    try:
        r = subprocess.run(["dig", "+short", tipo, dominio],
                           capture_output=True, text=True, timeout=20)
    except subprocess.TimeoutExpired:
        return "ERROR: dig no respondió en 20 segundos."
    except OSError as e:
        return recortar(f"ERROR: no se pudo ejecutar dig: {e}")
    if r.returncode != 0:
        return recortar(f"ERROR: dig falló ({r.returncode}): {r.stderr.strip() or 'sin detalles'}")
    salida = recortar(r.stdout.strip())
    return salida or f"Sin registros {tipo} para {dominio}."


# ---------------------------------------------------------------------------
# Subdominios
# ---------------------------------------------------------------------------

@protegida(objetivo="dominio")
def subdominios_crtsh(dominio: str) -> str:
    """Enumera subdominios de un dominio por transparencia de certificados (crt.sh).
    Pasivo: no toca el objetivo. Devuelve solo los subdominios dentro del alcance."""
    url = f"https://crt.sh/?q=%25.{urllib.parse.quote(dominio)}&output=json"
    datos, ultimo = None, None
    for intento in range(2):
        try:
            datos = json.loads(_http(url, timeout=90))
            break
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            ultimo = e
            if intento == 0:
                time.sleep(2)  # crt.sh devuelve 502/429 con frecuencia
        except Exception as e:
            ultimo = e
            break
    if datos is None:
        return (f"ERROR: crt.sh no respondió ({type(ultimo).__name__}). crt.sh suele ir lento; "
                "puedes reintentar más tarde o usar subdominios_subfinder.")
    if not isinstance(datos, list) or any(
        not isinstance(fila, dict) or not isinstance(fila.get("name_value"), str)
        for fila in datos
    ):
        return "ERROR: crt.sh devolvió un formato de certificados inesperado."
    nombres = set()
    for fila in datos:
        for n in str(fila.get("name_value", "")).splitlines():
            n = n.strip().lstrip("*.").lower()
            if n:
                nombres.add(n)
    dentro, fuera = filtrar(sorted(nombres))
    cab = f"{len(dentro)} subdominios en alcance ({fuera} filtrados por estar fuera):\n"
    return recortar(cab + "\n".join(dentro), maximo=MAX_SALIDA)


@protegida(objetivo="dominio")
def subdominios_subfinder(dominio: str) -> str:
    """Enumera subdominios con subfinder usando fuentes pasivas.
    Devuelve solo los subdominios dentro del alcance; no resuelve ni toca el objetivo."""
    comando = ["subfinder", "-d", dominio, "-silent", "-timeout", "10",
               "-max-time", "2", "-nc", "-duc"]
    try:
        r = subprocess.run(comando, capture_output=True, text=True, timeout=150)
    except subprocess.TimeoutExpired:
        return "ERROR: subfinder no terminó en 150 segundos."
    except FileNotFoundError:
        return "ERROR: subfinder no está instalado."
    except OSError as e:
        return recortar(f"ERROR: no se pudo ejecutar subfinder: {e}")
    if r.returncode != 0 and not r.stdout.strip():
        return recortar(f"ERROR: subfinder falló ({r.returncode}): "
                        f"{r.stderr.strip()[:300] or 'sin detalles'}")
    nombres = set()
    for linea in r.stdout.splitlines():
        n = linea.strip().lower().lstrip("*.")
        if n and re.fullmatch(r"[a-z0-9._-]+", n):
            nombres.add(n)
    dentro, fuera = filtrar(sorted(nombres))
    cab = f"{len(dentro)} subdominios en alcance ({fuera} filtrados por estar fuera):\n"
    return recortar(cab + "\n".join(dentro), maximo=MAX_SALIDA)


# ---------------------------------------------------------------------------
# Netcraft y ficheros públicos
# ---------------------------------------------------------------------------

CAMPOS_NETCRAFT = [
    "Site title", "Site rank", "Description", "Date first seen",
    "Primary language", "Netblock Owner", "Hosting company", "Hosting country",
    "IPv4 address", "IPv4 autonomous systems", "IPv6 address", "Reverse DNS",
    "Domain", "Nameserver", "Domain registrar", "DNS admin",
    "Top Level Domain", "DNS Security Extensions",
]


def _texto_html(fragmento: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", fragmento)).split())


def _tabla_netcraft(html: str) -> dict:
    """Extrae las parejas <th>etiqueta</th><td>valor</td> del informe de Netcraft."""
    campos = {}
    for fila in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        m = re.search(r"<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", fila, re.S | re.I)
        if not m:
            continue
        etiqueta = _texto_html(m.group(1))
        valor = _texto_html(m.group(2))
        if etiqueta and valor:
            campos.setdefault(etiqueta, []).append(valor)
    return campos


@protegida(objetivo="dominio")
def netcraft_reporte(dominio: str) -> str:
    """Consulta el informe público de Netcraft de un dominio: hosting, IP, ASN,
    nameservers, registrador y DNSSEC. Es una fuente pasiva de terceros."""
    url = f"https://sitereport.netcraft.com/?url=https://{urllib.parse.quote(dominio, safe='')}"
    try:
        html = _http(url, timeout=30, maximo=500_000)
    except urllib.error.HTTPError as e:
        return f"ERROR: Netcraft respondió HTTP {e.code}."
    except Exception as e:
        return f"ERROR: Netcraft no respondió ({type(e).__name__})."
    campos = _tabla_netcraft(html)
    if not campos:
        return ("ERROR: Netcraft no devolvió una tabla de datos "
                "(puede requerir JavaScript o haber cambiado el formato).")
    lineas = [f"Informe Netcraft de {dominio}:"]
    for etiqueta in CAMPOS_NETCRAFT:
        if etiqueta in campos:
            lineas.append(f"{etiqueta}: " + "; ".join(campos[etiqueta]))
    return recortar("\n".join(lineas))


RUTAS_PUBLICAS = ["/robots.txt", "/.well-known/security.txt", "/security.txt", "/sitemap.xml"]


@protegida(objetivo="dominio")
def ficheros_publicos(dominio: str) -> str:
    """Lee ficheros públicos estándar de un host en alcance: robots.txt,
    .well-known/security.txt, security.txt y sitemap.xml. Solo hace un GET a esas
    rutas fijas: no crawlea, no fuzzea y no sigue redirecciones fuera de alcance."""
    bloques = []
    for ruta in RUTAS_PUBLICAS:
        url = f"https://{dominio}{ruta}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with _abrir(req, timeout=15) as r:
                estado = getattr(r, "status", 200)
                texto = _leer(r, 20_000)
            bloques.append(f"### {url} (HTTP {estado})\n{texto.strip()}")
        except urllib.error.HTTPError as e:
            bloques.append(f"### {url} (HTTP {e.code})")
        except Exception as e:
            bloques.append(f"### {url} (ERROR: {type(e).__name__})")
    return recortar("\n\n".join(bloques), maximo=6000)


# ---------------------------------------------------------------------------
# Servicios expuestos (Shodan InternetDB / Shodan API)
# ---------------------------------------------------------------------------

def _ips_de(dominio: str) -> list[str]:
    """Resuelve A/AAAA con dig y valida las direcciones. No escanea nada."""
    ips, vistos = [], set()
    for tipo in ("A", "AAAA"):
        try:
            r = subprocess.run(["dig", "+short", tipo, dominio],
                               capture_output=True, text=True, timeout=20)
        except (subprocess.TimeoutExpired, OSError):
            continue
        if r.returncode != 0:
            continue
        for linea in r.stdout.splitlines():
            ip = linea.strip()
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                continue
            if ip not in vistos:
                vistos.add(ip)
                ips.append(ip)
    return ips[:5]


def _shodan_api(ip: str, clave: str) -> str:
    url = ("https://api.shodan.io/shodan/host/" + urllib.parse.quote(ip)
           + "?" + urllib.parse.urlencode({"key": clave, "minify": "true"}))
    try:
        datos = json.loads(_http(url, timeout=20, maximo=300_000))
    except urllib.error.HTTPError as e:
        return f"Shodan API: HTTP {e.code} (la clave no se muestra)."
    except Exception as e:
        return f"Shodan API: error ({type(e).__name__})."
    if not isinstance(datos, dict):
        return "Shodan API: formato inesperado."
    campos = []
    for k in ("org", "isp", "os", "country_name", "last_update"):
        if datos.get(k):
            campos.append(f"{k}={datos[k]}")
    puertos = datos.get("ports") or []
    if puertos:
        campos.append("puertos=" + ",".join(str(p) for p in sorted(puertos)[:50]))
    return "Shodan API: " + "; ".join(campos) if campos else "Shodan API: sin datos."


def _internetdb(ip: str, clave: str | None) -> str:
    lineas = [f"## {ip}"]
    try:
        datos = json.loads(_http(f"https://internetdb.shodan.io/{ip}",
                                 timeout=20, maximo=200_000))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return f"## {ip}\nSin datos en InternetDB."
        return f"## {ip}\nERROR: InternetDB respondió HTTP {e.code}."
    except Exception as e:
        return f"## {ip}\nERROR: InternetDB no respondió ({type(e).__name__})."
    if not isinstance(datos, dict):
        return f"## {ip}\nERROR: InternetDB devolvió un formato inesperado."
    puertos = datos.get("ports") or []
    if puertos:
        lineas.append("Puertos: " + ", ".join(str(p) for p in sorted(puertos)[:50]))
    hosts = [h for h in (datos.get("hostnames") or []) if isinstance(h, str)]
    dentro, fuera = filtrar(sorted(set(hosts)))
    if dentro:
        lineas.append("Hostnames en alcance: " + ", ".join(dentro[:20]))
    if fuera:
        lineas.append(f"({fuera} hostnames fuera de alcance omitidos)")
    cpes = [c for c in (datos.get("cpes") or []) if isinstance(c, str)]
    if cpes:
        lineas.append("CPEs: " + "; ".join(cpes[:10]))
    tags = [t for t in (datos.get("tags") or []) if isinstance(t, str)]
    if tags:
        lineas.append("Tags: " + ", ".join(tags[:10]))
    vulns = [v for v in (datos.get("vulns") or []) if isinstance(v, str)]
    if vulns:
        lineas.append("Vulns: " + ", ".join(vulns[:20]))
    if clave:
        lineas.append(_shodan_api(ip, clave))
    return "\n".join(lineas)


@protegida(objetivo="dominio")
def servicios_expuestos(dominio: str) -> str:
    """Consulta Shodan InternetDB para las IPs del dominio (y Shodan API si hay
    SHODAN_API_KEY). Devuelve puertos, hostnames, CPEs, tags y CVEs vistos por
    Shodan. Es pasivo: no escanea ni conecta con el objetivo."""
    ips = _ips_de(dominio)
    if not ips:
        return f"Sin direcciones IP para {dominio} (dig no devolvió A/AAAA)."
    bloques = [f"IPs de {dominio}: {', '.join(ips)} (máximo 5)"]
    clave = os.environ.get("SHODAN_API_KEY")
    for ip in ips:
        bloques.append(_internetdb(ip, clave))
    return recortar("\n\n".join(bloques), maximo=MAX_SALIDA)


# ---------------------------------------------------------------------------
# Google dorks y theHarvester
# ---------------------------------------------------------------------------

CATEGORIAS_DORK = {
    "archivos": "(filetype:env OR filetype:sql OR filetype:bak OR filetype:log OR filetype:zip OR filetype:tar.gz)",
    "paneles": '(inurl:admin OR inurl:login OR inurl:dashboard OR intitle:"index of")',
    "config": "(inurl:config OR inurl:.git OR inurl:.env OR inurl:backup)",
    "documentos": "(filetype:pdf OR filetype:doc OR filetype:docx OR filetype:xlsx OR filetype:csv)",
    "errores": '(intitle:"error" OR inurl:debug OR inurl:phpinfo)',
    "todo": "",
}


def _limpiar_consulta(texto: str) -> str:
    """Quita site: para que el modelo no pueda cambiar el dominio de la búsqueda."""
    texto = " ".join(str(texto or "").split())
    texto = re.sub(r"(?i)\bsite:\S+", "", texto)
    return texto[:200].strip()


def _url_ddg(href: str) -> str:
    if href.startswith("//"):
        href = "https:" + href
    partes = urllib.parse.urlsplit(href)
    if partes.netloc.endswith("duckduckgo.com") and partes.path.startswith("/l/"):
        q = urllib.parse.parse_qs(partes.query)
        if q.get("uddg"):
            return q["uddg"][0]
    return href


def _resultados_ddg(html: str) -> list[dict]:
    resultados, resumenes = [], []
    for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", html, re.S | re.I):
        attrs, texto = m.groups()
        if "result__a" in attrs.lower():
            href = re.search(r'href=["\']([^"\']+)["\']', attrs)
            if not href:
                continue
            url = _url_ddg(unescape(href.group(1)))
            titulo = _texto_html(texto)
            if url and titulo:
                resultados.append({"titulo": titulo, "url": url, "resumen": ""})
        elif "result__snippet" in attrs.lower():
            resumenes.append(_texto_html(texto))
    for i, r in enumerate(resultados):
        if i < len(resumenes):
            r["resumen"] = resumenes[i]
    return resultados


def _resultados_google(q: str) -> list[dict] | None:
    clave = os.environ.get("GOOGLE_API_KEY")
    cx = os.environ.get("GOOGLE_CSE_ID")
    if not (clave and cx):
        return None
    url = "https://www.googleapis.com/customsearch/v1?" + urllib.parse.urlencode({
        "key": clave, "cx": cx, "q": q, "num": 10,
    })
    try:
        datos = json.loads(_http(url, timeout=20, maximo=500_000))
    except Exception:
        return None
    if not isinstance(datos, dict):
        return None
    items = datos.get("items") or []
    return [
        {"titulo": i.get("title", ""), "url": i.get("link", ""),
         "resumen": i.get("snippet", "")}
        for i in items if isinstance(i, dict)
    ]


def _solo_alcance(resultados: list[dict]) -> list[dict]:
    salida = []
    for r in resultados:
        host = _host(r.get("url", ""))
        if host and filtrar([host])[0]:
            salida.append(r)
    return salida


@protegida(objetivo="dominio")
def google_dorks(dominio: str, consulta: str = "", categoria: str = "archivos") -> str:
    """Busca dorks de un dominio en Google Custom Search (si hay GOOGLE_API_KEY
    y GOOGLE_CSE_ID) o en DuckDuckGo como respaldo. categoria: archivos, paneles,
    config, documentos, errores o todo. Devuelve solo URLs dentro del alcance.
    Es pasivo: no descarga los resultados, solo los busca."""
    if categoria not in CATEGORIAS_DORK:
        return ("ERROR: categoría no válida. Usa: "
                + ", ".join(sorted(CATEGORIAS_DORK)) + ".")
    dork = _limpiar_consulta(consulta) or CATEGORIAS_DORK[categoria]
    q = f"site:{dominio} {dork}".strip()
    resultados = _resultados_google(q)
    motor = "Google CSE"
    if resultados is None:
        motor = "DuckDuckGo"
        try:
            html = _http_post("https://html.duckduckgo.com/html/",
                              {"q": q}, timeout=25, maximo=1_000_000)
            resultados = _resultados_ddg(html)
        except Exception as e:
            return f"ERROR: la búsqueda no respondió ({type(e).__name__})."
    resultados = _solo_alcance(resultados)
    if not resultados:
        return f"Sin resultados en alcance para: {q}"
    lineas = [f"Consulta ({motor}): {q}", f"Resultados en alcance: {len(resultados)}"]
    for i, r in enumerate(resultados[:10], 1):
        lineas.append(f"{i}. {r['titulo']}\n   {r['url']}")
        if r.get("resumen"):
            lineas.append(f"   {r['resumen'][:300]}")
    return recortar("\n".join(lineas), maximo=MAX_SALIDA)


FUENTES_HARVESTER = {
    "crtsh", "otx", "urlscan", "duckduckgo", "commoncrawl",
    "waybackarchive", "rapiddns", "hackertarget", "threatcrowd",
    "subdomaincenter", "shodanInternetDB",
}


def _seccion_harvester(texto: str, titulo: str) -> list[str]:
    lineas = texto.splitlines()
    dentro, salida = False, []
    for linea in lineas:
        s = linea.strip()
        if s.lower().startswith("[*]") and titulo.lower() in s.lower():
            dentro = True
            continue
        if not dentro:
            continue
        if not s:
            if salida:
                break
            continue
        if s.startswith("[*]") or (s and set(s) <= {"-"}):
            if salida:
                break
            continue
        salida.append(s)
    return salida


def _enmascarar_email(email: str) -> str:
    email = email.strip().strip(".,;")
    usuario, _, dominio = email.partition("@")
    if not dominio:
        return "***"
    return ((usuario[:1] + "***@") if usuario else "***@") + dominio


@protegida(objetivo="dominio")
def theharvester_osint(dominio: str,
                       fuentes: str = "crtsh,otx,urlscan,duckduckgo",
                       limite: int = 50) -> str:
    """Ejecuta theHarvester con fuentes pasivas y devuelve subdominios, correos
    enmascarados, IPs, ASNs y URLs en alcance. No hace fuerza bruta ni resolución DNS.
    fuentes: lista separada por comas de fuentes pasivas permitidas (por defecto
    crtsh,otx,urlscan,duckduckgo)."""
    pedidas = [f.strip().lower() for f in str(fuentes).split(",") if f.strip()]
    no_validas = [f for f in pedidas if f not in FUENTES_HARVESTER]
    if not pedidas or no_validas:
        return ("ERROR: fuentes no permitidas: "
                f"{', '.join(no_validas) or '(ninguna)'}. Usa: "
                + ", ".join(sorted(FUENTES_HARVESTER)) + ".")
    try:
        limite = max(1, min(int(limite), 200))
    except (TypeError, ValueError):
        return "ERROR: limite debe ser un número entre 1 y 200."
    comando = ["theHarvester", "-d", dominio, "-b", ",".join(pedidas),
               "-l", str(limite), "-q"]
    try:
        r = subprocess.run(comando, capture_output=True, text=True, timeout=150)
    except subprocess.TimeoutExpired:
        return "ERROR: theHarvester no terminó en 150 segundos."
    except FileNotFoundError:
        return "ERROR: theHarvester no está instalado."
    except OSError as e:
        return recortar(f"ERROR: no se pudo ejecutar theHarvester: {e}")
    salida = (r.stdout or "") + ("\n" + r.stderr if r.stderr else "")
    if r.returncode != 0 and not r.stdout.strip():
        return recortar(f"ERROR: theHarvester falló ({r.returncode}): "
                        f"{r.stderr.strip()[:300] or 'sin detalles'}")

    hosts = [h.lower() for h in _seccion_harvester(salida, "Hosts found")
             if " " not in h and "." in h]
    dentro, fuera = filtrar(sorted(set(hosts)))
    emails = [e for e in _seccion_harvester(salida, "Emails found")
              if "@" in e and "no emails" not in e.lower()]
    ips = _seccion_harvester(salida, "IPs found")
    asns = _seccion_harvester(salida, "ASNS found")
    urls = [u for u in _seccion_harvester(salida, "Interesting Urls found")
            if _en_alcance_url(u)]

    lineas = [f"theHarvester sobre {dominio} (fuentes: {', '.join(pedidas)})"]
    lineas.append(f"Hosts en alcance: {len(dentro)}"
                  + (f" ({fuera} fuera omitidos)" if fuera else ""))
    if dentro:
        lineas.append("\n".join(dentro[:50]))
    if emails:
        lineas.append(f"Correos encontrados: {len(emails)} (enmascarados)")
        lineas.append("\n".join(_enmascarar_email(e) for e in emails[:5]))
    else:
        lineas.append("Correos encontrados: 0")
    if ips:
        lineas.append(f"IPs vistas en fuentes ({len(ips)}, sin escanear): "
                      + ", ".join(ips[:20]))
    if asns:
        lineas.append(f"ASNs: {', '.join(asns[:20])}")
    if urls:
        lineas.append("URLs en alcance: " + ", ".join(urls[:10]))
    return recortar("\n".join(lineas), maximo=MAX_SALIDA)

