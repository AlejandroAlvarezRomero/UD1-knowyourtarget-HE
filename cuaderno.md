# CUADERNO RECONOCIMIENTO PASIVO

Recordamos a que programa le hacemos el reconocimiento:

**Programa:** https://hackerone.com/playstation
<br>
**Fecha de consulta:** 28 de octubre de 2026

---

`Todo el reconocimiento se ha realizado en una maquina virtual de Kali Linux`  

<br>

## REGISTRO DOMINIO

2026-10-28 20:27  objetivo: playstation.com (in scope)
$ whois playstation.com
-> Fechas: Creado 1997-01-14, Expira 2027-01-13; Registrador: 1API GmbH; Servidores DNS: AWS (ns-1039.awsdns-01.org...); Contactos: Ocultos (REDACTED FOR PRIVACY).
Siguiente paso: consultar DNS para relacionar el dominio con su correo y sus servidores autoritativos.

<br>

## REGISTRO DNS

2026-10-28 20:31  objetivo: playstation.com (in scope)
$ dig +short mx playstation.com
-> 0 playstation-com.mail.protection.outlook.com.
Siguiente paso: revisar TXT y DMARC sin enviar correo ni realizar pruebas de entrega.

2026-10-28 20:33  objetivo: playstation.com (in scope)
$ dig +short TXT playstation.com
-> Correo corporativo: Microsoft (v=spf1 ip4:87.246.102.203 include:spf.protection.outlook.com -all)
-> Huella tecnológica: Google, Microsoft 365, Zoom, Klaviyo y CRM de Salesforce (múltiples registros).
Siguiente paso: comprobar la política DMARC y anotar los terceros como dependencias observadas, no como fallos.

2026-10-28 20:37  objetivo: playstation.com (in scope)
$ dig +short TXT _dmarc.playstation.com
-> v=DMARC1; p=reject; rua=mailto:efa17af05523914@rep.dmarcanalyzer.com... (política de rechazo estricta).
Siguiente paso: pasar a enumeración pasiva de subdominios y contrastar los resultados entre dos fuentes.

<br>

## SUBDOMINIOS

2026-10-28 20:51  objetivo: playstation.com (in scope)
$ subfinder -d playstation.com -silent 
-> 1.545 subdominios descubiertos; la mayor parte se encuentra dentro del comodín *.playstation.com (en alcance).
Siguiente paso: contrastar la enumeración con crt.sh y conservar solo nombres que coincidan con el alcance.

2026-11-02 13:30  objetivo: playstation.com (in scope)
$ curl -s 'https://crt.sh/?q=%25.playstation.com&output=json' | jq -r '.[].name_value' | sort -u
-> Múltiples subdominios históricos y activos extraídos de certificados SSL/TLS públicos. La inmensa mayoría validados dentro del alcance del comodín *.playstation.com.
Siguiente paso: elegir una muestra representativa para el mapa; no resolver masivamente ni conectar a los hosts.


## HUELLA TECNOLÓGICA

2026-11-02 13:33   objetivo: www.playstation.com (in scope)
$ Consulta pasiva en web: sitereport.netcraft.com/?url=https://playstation.com
-> Proveedor de red / Hosting: Amazon Web Services y el CDN de Akamai
-> Cabeceras de Seguridad: Strict-Transport-Security, X-Frame-Options Same Origin y X-Content-Type-Options.
-> Tecnologías: HTML5, JavaScript y framework visual D3.js.
Siguiente paso: consultar únicamente ficheros públicos estándar del portal principal.


## FICHEROS EXPUESTOS

2026-11-02 13:41  objetivo: www.playstation.com (in scope)
$ curl -s https://www.playstation.com/robots.txt
-> Revela rutas sensibles no indexables, destacando un directorio de pruebas (*/explore/testing/) y arquitectura interna relacionada con Mongo DB .
Siguiente paso: anotarlo como ruta no indexada; no abrirla ni intentar comprobar si es accesible.

2026-11-02 13:43 objetivo: www.playstation.com (in scope)
$ curl -s https://www.playstation.com/.well-known/security.txt
-> El servidor (CDN/WAF) devuelve un error 403 Access Denied, bloqueando la lectura del fichero de políticas de seguridad.
Siguiente paso: registrar el 403 como observación y consultar InternetDB para la IP ya publicada por fuentes pasivas.

## SERVICIOS EXPUESTOS

2026-11-02 13:57 objetivo: 54.215.24.50 / www.playstation.com (in scope)
$ curl -s https://internetdb.shodan.io/54.215.24.50
-> Puertos expuestos: 80 y 443 (HTTP/HTTPS estándar).
-> Infraestructura: Balanceador de carga de AWS (cpe:/a:amazon:elastic_load_balancing) en entorno cloud.
Siguiente paso: incorporar el dato al mapa como información pasiva, sin inferir que toda la infraestructura use esa IP.

## GOOGLE DORKS

2026-11-02 14:04  objetivo: playstation.com (in scope)
$ Búsquedas en Google: site:playstation.com inurl:login / site:playstation.com intitle:"index of" / site:playstation.com filetype:pdf / Y algunos mas comandos ofrecidos por la IA.
-> Resultados: 0 resultados en las búsquedas sensibles. El servidor no expone listados de directorios ("index of") ni documentos críticos en texto plano, lo que demuestra un control estricto sobre la indexación de los motores de búsqueda.
Siguiente paso: dejar constancia de que una búsqueda sin resultados no demuestra ausencia de exposición; continuar con OSINT de personas sin contactar a nadie.


## CORREOS Y EMPLEADOS 

2026-11-02 14:15 objetivo: playstation.com (in scope)
$ theHarvester -d playstation.com -b all -l 200
-> Resultados: 0 correos y 0 perfiles de LinkedIn detectados debido a la ausencia de API Keys comerciales configuradas.
Siguiente paso: documentar la limitación de la fuente y no inventar direcciones ni patrones de correo.

2026-11-02 14:24 objetivo: Empleados de PlayStation (in scope)
$ Búsqueda pasiva en Google: site:linkedin.com
-> Resultados: Se logran identificar perfiles de ingenieros de seguridad y DevOps en los resultados de búsqueda de Google.
Siguiente paso: resumir solo roles públicos en el mapa, sin nombres, enlaces personales ni contacto.





