

# Informe de Reconocimiento Pasivo — playstation.com

## 1. Resumen ejecutivo

Se ha realizado un reconocimiento pasivo completo del dominio **playstation.com** dentro del alcance autorizado. El dominio, registrado desde 1997 y caducando en 2027, se aloja en infraestructura de **Amazon Web Services (AS16509)** en la región US West (Northern California). DNSSEC está habilitado. El DNS apunta a dos IPs: `54.183.100.47` y `184.169.195.49`. No hay registros AAAA (IPv6) para el dominio raíz.

Se identificaron **más de 1.400 subdominios** mediante fuentes pasivas (crt.sh y subfinder), lo que refleja una infraestructura compleja con múltiples ambientes (producción, QA, stage, dev), regiones geográficas y servicios especializados (APIs, autenticación, tienda, blogs, CMS). El correo electrónico utiliza **Microsoft 365** (MX: `playstation-com.mail.protection.outlook.com`). El fichero `security.txt` no es accesible (HTTP 403), lo cual es un hallazgo relevante.

---

## 2. Alcance autorizado y activos analizados

**Alcance autorizado:** playstation.com, *.playstation.com, *.playstation.net, *.sonyentertainmentnetwork.com, *.api.playstation.com, api.direct.playstation.com, ca.account.sony.com, checkout.playstation.com, compete.playstation.com, direct.playstation.com, my.account.sony.com, my.playstation.com, profile.playstation.com, ps5.np.playstation.net, session-share.playstation.com, social.playstation.com, store.playstation.com, transact.playstation.com, wallets.api.playstation.com, web.np.playstation.com, www.playstation.com

**Activo principal analizado:** playstation.com

---

## 3. Registro y DNS

### 3.1 WHOIS (whois_dominio)

| Campo | Valor |
|---|---|
| Dominio | PLAYSTATION.COM |
| Fecha de alta | 1997-01-14 |
| Fecha de caducidad | 2027-01-13 |
| Última modificación | 2025-11-22 |
| Registrador | 1387 (1API.net) |
| Nameservers | NS-1039.AWSDNS-01.ORG, NS-1962.AWSDNS-53.CO.UK, NS-43.AWSDNS-05.COM, NS-957.AWSDNS-55.NET |
| Estado | client transfer prohibited |

### 3.2 Registros DNS (dns_registros)

| Tipo | Valor |
|---|---|
| **A** | `54.183.100.47`, `184.169.195.49` |
| **AAAA** | Sin registros |
| **MX** | `0 playstation-com.mail.protection.outlook.com.` |
| **NS** | `ns-957.awsdns-55.net`, `ns-43.awsdns-05.com`, `ns-1962.awsdns-53.co.uk`, `ns-1039.awsdns-01.org` |
| **TXT** | SPF: `v=spf1 ip4:87.246.102.203 include:spf.protection.outlook.com -all` — Verificaciones Google: `google-site-verification=aEdBdVDkKTaRUDChDEPvdP2N6z9E03HUwt1m3DFrMLM`, `google-site-verification=aXJbZWvjKbMdlnvrN9_KlR9DNwd5-z95vH6FXINY1D8`, `google-site-verification=7eytTX-XM-Cr33smkPKzmS5-_qh_sdsZq9r2CKdsmlI`, `google-site-verification=Zkdrq-IwUOSWBd0a4HsaCM6o7yVF3rx3Qf4ZtPcEGGI` — Verificaciones Microsoft: `MS=ms74424052` — Verificaciones Zoom: `Zoom_10355089` — Verificaciones Klaviyo: `klaviyo-site-verification=W4TZZC`, `klaviyo-site-verification=VgVXUB` — Múltiples registros Salesforce/CRM (`00DWG...`, `00DV9...`, `00DWF...`) — Otros: `reclaim-jcsmyd9pix7fz04ehflgsgovo93wq6yz` |
| **SOA** | `ns-957.awsdns-55.net awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400` |
| **CAA** | Sin registros |
| **CNAME** | Sin registros |
| **SRV** | Sin registros |

---

## 4. Subdominios

### 4.1 crt.sh — subdominios_crtsh

**894 subdominios** identificados dentro del alcance. Muestras representativas por categoría:

- **APIs:** `api.playstation.com`, `accounts.api.playstation.com`, `api.direct.playstation.com`, `auth.api.playstation.com`, `a1-np.api.playstation.com`, `c1-np.api.playstation.com`
- **Ambientes de desarrollo/QA:** `api.direct-qa.playstation.com`, `api.direct-stage.playstation.com`, `api.direct-stage2.playstation.com`, `api.direct-stage3.playstation.com`
- **Regiones:** `ae.playstation.com`, `au.playstation.com`, `br.playstation.com`, `ca.playstation.com`, `jp.playstation.com`, `asia.playstation.com`, `latam.playstation.com`, `eu.playstation.com`
- **Tienda y checkout:** `store.playstation.com`, `checkout.playstation.com`, `direct.playstation.com`
- **Blogs regionales:** `blog.playstation.com`, `blog.es.playstation.com`, `blog.de.playstation.com`, `blog.fr.playstation.com`, `blog.us.playstation.com`, `blog.asia.playstation.com`
- **CMS/AUTHOR:** `author.playstation.com`, `cms-publisher.direct.playstation.com`, `cms-author.direct.playstation.com`
- **Soporte:** `support.playstation.com`, `camera-adaptor.support.playstation.com`
- **CDN:** `cdn.playstation.com`, `cdn.us.playstation.com`, `cdn.jp.playstation.com`, `cdn.latam.playstation.com`

### 4.2 Subfinder — subdominios_subfinder

**1.440 subdominios** identificados. Subfinder proporciona una visión más amplia con:

- **AI/Estudios:** `ai.bridges.playstation.com`, `ai.staging.studios.playstation.com`, `andromeda.ai.studios.playstation.com`, `argocd.ai.studios.playstation.com`, `audio.studios.playstation.com`
- **Bridges:** `api.bridges.playstation.com`, `ai.api.bridges.playstation.com`
- **Chat:** `chat.playstation.com`, `chat.studios.playstation.com`, `chat.ai.studios.playstation.com`
- **Careers:** `careers.playstation.com`
- **Wraith:** `author.wraith.playstation.com`, `authoring.limitbreak.wraith.playstation.com`
- **Más regiones y ambientes:** `api.direct.d1-np.playstation.com`, `api.direct.d1-pmgt.playstation.com`, `api.direct.q1-np.playstation.com`

**Observación:** La superposición entre crt.sh y subfinder es significativa, pero subfinder aporta subdominios adicionales relacionados con AI, ArgocD/Kubernetes, y servicios de chat.

---

## 5. Infraestructura y servicios expuestos

### 5.1 Netcraft — netcraft_reporte

| Campo | Valor |
|---|---|
| Site rank | 193,951 |
| Primera vez visto | March 2014 |
| Netblock Owner | Amazon Technologies Inc. |
| Hosting | Amazon - US West (Northern California) datacenter |
| País | US |
| IPv4 | 54.183.100.47 |
| IPv6 | No presente |
| Reverse DNS | ec2-54-183-100-47.us-west-1.compute.amazonaws.com |
| ASN | AS16509 |
| Nameserver | ns-957.awsdns-55.net |
| Registrador | 1api.net |
| DNS admin | [email protected] |
| DNSSEC | Enabled |

### 5.2 Servicios expuestos — servicios_expuestos (Shodan InternetDB)

**IP 54.183.100.47:** Sin datos en InternetDB.

**IP 184.169.195.49:**
- **Puertos:** 80 (HTTP), 443 (HTTPS)
- **Hostnames en alcance:** `playstation.com`, `us.playstation.com`, `www.playstation.com`, `www.us.playstation.com`
- **CPEs:** `cpe:/a:amazon:elastic_load_balancing` (Amazon Elastic Load Balancing)
- **Tags:** cloud

**Inferencia:** La infraestructura principal utiliza Amazon ELB como balanceador de carga. No se observan puertos adicionales expuestos (22, 8080, 3306, etc.), lo cual indica una configuración de seguridad razonable.

---

## 6. Ficheros públicos — ficheros_publicos

### 6.1 robots.txt (HTTP 200)

```
User-agent: *
Disallow: */explore/testing/
Disallow: */community/community-score*
Disallow: */?category*
Disallow: */content/usergenerated/asi/mongo/content/sites/activitystreams/activities/community/*
Disallow: */search/?q*
Disallow: */content/experience-fragments/global_pdc/*
Crawl-delay: 5

User-agent: AhrefsBot
Crawl-delay: 10
User-agent: YandexBot
Crawl-delay: 10
User-agent: bingbot
Crawl-delay: 10

User-agent: *
Disallow: */sitemap_gpdc.xml

User-agent: Algolia Crawler
Allow: */sitemap_gpdc.xml

User-agent: PetalBot
Disallow: /

Sitemap: https://www.playstation.com/sitemap_index.xml
```

**Observaciones:**
- Se bloquean rutas de testing, community score, búsqueda dinámica y contenido generado por usuarios.
- `PetalBot` (motor de búsqueda de Huawei) está completamente bloqueado.
- Se restringe el sitemap GPDC solo para Algolia Crawler.

### 6.2 security.txt (HTTP 403 / HTTP 301)

- **`.well-known/security.txt`:** HTTP 403 (Forbidden) — **No accesible**.
- **`security.txt`:** HTTP 301 (Redirection) — Redirige pero no se sigue fuera de alcance.

**Hallazgo relevante:** El fichero `security.txt`, estándar para programas de bug bounty y contacto de seguridad, no es accesible directamente. Esto impide conocer la política de divulgación de vulnerabilidades de PlayStation.

### 6.3 sitemap.xml (HTTP 404)

- **`sitemap.xml`:** HTTP 404 — No encontrado en la raíz.
- El sitemap real está en `https://www.playstation.com/sitemap_index.xml` (indicado en robots.txt).

---

## 7. OSINT

### 7.1 Google Dorks — google_dorks

**Categoría "todo" (10 resultados):**

| # | Título | URL | Resumen |
|---|---|---|---|
| 1 | PlayStation® Official Site | https://www.playstation.com/en-us/ | Página principal: PS5, juegos, Plus, accesorios |
| 2 | Latest | Official PlayStation™Store US | https://store.playstation.com/en-us/ | Tienda oficial y PlayStation Plus |
| 3 | Your account for PlayStation | https://www.playstation.com/en-us/your-account-for-playstation/ | Información sobre cuentas y beneficios |
| 4 | PS4 | https://www.playstation.com/en-us/ps4/ | Página de PS4 |
| 5 | Official PlayStation™Store US | https://store.playstation.com/pages/en-us/en-/ | Términos y privacidad de la tienda |
| 6 | PlayStation® Official Site (Indonesia) | https://www.playstation.com/en-id/ | Versión en indonesio |
| 7 | Buy & Pre-order | https://direct.playstation.com/en-us | Compra directa de consoles y accesorios |
| 8 | PlayStation Support | https://www.playstation.com/en-us/support/ | Soporte y avisos importantes |
| 9 | Play Has No Limits - PS5 | https://www.playstation.com/en-us/ps5/ | Página de PS5 y DualSense |
| 10 | PlayStation®Plus | https://www.playstation.com/en-us/ps-plus/ | Suscripción Plus Essential/Extra/Premium |

**Categoría "archivos" (10 resultados):** Similar a "todo", sin archivos sensibles expuestos directamente.

**Categoría "paneles" (10 resultados):** Muestra páginas de panel de usuario (`Hello, My Orders Payments Addresses My Profile Sign Out`) en `direct.playstation.com`.

**Categoría "config" (10 resultados):** Resultado similar, sin ficheros de configuración expuestos.

**Categoría "documentos":** Sin resultados en alcance.

### 7.2 theHarvester — theharvester_osint

- **Hosts en alcance:** 637
- **Correos encontrados:** 0 (enmascarados/no encontrados)
- **IPs vistas en fuentes (56):** Incluye rangos de Cloudflare (AS13335), Google (AS15169), AWS (AS16509), Akamai (AS20940), Fastly (AS54113), y otros.
- **ASNs identificados:** AS13335 (Cloudflare), AS133800, AS14618 (Amazon), AS15169 (Google), AS16509 (AWS), AS16625 (Akamai), AS20940 (Akamai), AS211183, AS2635 (GTT), AS27647 (Mega), AS29182 (Fastly), AS51167, AS54113 (Fastly), AS58487
- **URLs en alcance destacadas:**
  - `https://core-entitlements.e1-np.api.playstation.com/` — API de entitlements
  - `https://ivaldi.playstation.com/campaigns/...` — Servicio de campañas/micrositios
  - `https://store.playstation.com/ar-sa/...`, `https://store.playstation.com/en-ca/...` — Tienda regional
  - `https://www.playstation.com/en-us/games/grand-theft-auto-vi/` — Página de GTA VI

**Observación:** La diversidad de ASNs indica el uso de múltiples CDNs y proveedores de servicios cloud: **AWS, Cloudflare, Google Cloud, Akamai, Fastly**.

---

## 8. Observaciones y riesgos potenciales

### 8.1 Infraestructura cloud distribuida
La infraestructura utiliza múltiples proveedores: AWS (principal, con EC2 y ELB), Cloudflare, Google Cloud, Akamai y Fastly. Esto proporciona resiliencia pero incrementa la superficie de configuración y gestión de certificados.

### 8.2 Ausencia de IPv6 (AAAA)
El dominio raíz no tiene registros AAAA (dns_registros). Esto es un indicador de que el acceso IPv6 podría no estar habilitado o estar gestionado de forma diferente.

### 8.3 security.txt inaccesible (ficheros_publicos)
El fichero `.well-known/security.txt` devuelve HTTP 403. Esto impide que investigadores de seguridad encuentren fácilmente el canal de reporte de vulnerabilidades y la política de bug bounty de PlayStation. **Recomendación:** Verificar si existe un programa de bug bounty por separado (ej. Bugcrowd, HackerOne) o si el security.txt debería estar accesible.

### 8.4 SPF restrictivo (dns_registros)
El registro SPF es `v=spf1 ip4:87.246.102.203 include:spf.protection.outlook.com -all`, con `-all` (hard fail). Esto es correcto desde el punto de vista de seguridad, aunque solo incluye una IP explícita (`87.246.102.203`) además de Outlook 365.

### 8.5 Verificaciones múltiples de terceros (dns_registros)
Se observan verificaciones de Google Search Console (4 keys), Microsoft (`MS=ms74424052`), Zoom (`Zoom_10355089`), Klaviyo (marketing email, 2 keys) y numerosos registros de Salesforce/CRM. Esto indica integración con múltiples servicios SaaS.

### 8.6 Exposición de APIs (servicios_expuestos)
Solo los puertos 80 y 443 están expuestos en la IP principal. No se detectan puertos de gestión o bases de datos expuestos directamente, lo cual es positivo.

### 8.7 Ambientes de no-producción expuestos (subdominios_crtsh, subdominios_subfinder)
Se identificaron numerosos subdominios de QA, stage y dev: `*-qa.playstation.com`, `*-stage.playstation.com`, `*-stage2.playstation.com`, `*-stage3.playstation.com`, `*-vega-dev1.playstation.com`. Estos ambientes deberían estar adecuadamente protegidos (autenticación, no indexables) ya que están certificados públicamente.

### 8.8 CNAME y SRV ausentes
No hay registros CNAME ni SRV para el dominio raíz, lo cual es esperable para un sitio web moderno que resuelve directamente a IPs.

---

## 9. Limitaciones y fuentes que fallaron

| Herramienta | Estado | Observación |
|---|---|---|
| whois_dominio | ✅ OK | Datos completos |
| dns_registros (A, AAAA, MX, NS, TXT, SOA, CAA, CNAME, SRV) | ✅ OK | Todos consultados |
| subdominios_crtsh | ✅ OK | 894 subdominios |
| subdominios_subfinder | ✅ OK | 1.440 subdominios |
| netcraft_reporte | ✅ OK | Informe completo |
| servicios_expuestos | ✅ OK | Shodan InternetDB consultado |
| ficheros_publicos (robots.txt) | ✅ OK | HTTP 200 |
| ficheros_publicos (security.txt) | ⚠️ 403 | No accesible |
| ficheros_publicos (sitemap.xml) | ⚠️ 404 | No en raíz; sitemap real en `/sitemap_index.xml` |
| google_dorks | ✅ OK | DuckDuckGo como fuente |
| theharvester_osint | ✅ OK | 637 hosts, 56 IPs, múltiples ASNs |

**Llamadas totales:** 21 de 24 máximas.

---

*Informe generado el 2026-11-10 mediante reconocimiento pasivo autorizado.*