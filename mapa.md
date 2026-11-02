# MAPA DE RECONOCIMIENTO: PlayStation (Sony Interactive Entertainment)

## Resumen
La infraestructura pública de PlayStation presenta un altísimo nivel de madurez y fortificación perimetral. Operan un entorno híbrido y global sostenido principalmente por Amazon Web Services (AWS) y la CDN de Akamai, con políticas de seguridad estrictas (DMARC `p=reject`, HSTS, y bloqueo de herramientas CLI mediante WAF). Durante el escaneo pasivo se consolidaron más de 1.500 subdominios, exponiendo una amplia arquitectura de microservicios y APIs. No se identificaron fugas críticas de información ni servicios administrativos (SSH/RDP) expuestos, lo que obliga a orientar la fase activa hacia la lógica de negocio y vulnerabilidades web en aplicaciones de terceros o entornos de desarrollo (*stage/dev*).

## Dominios y subdominios (Muestra representativa)
*Basado en las consolidaciones de subfinder, crt.sh y theHarvester.*

| Subdominio | IP Detectada | En Alcance | Posible Función |
| :--- | :--- | :--- | :--- |
| `www.playstation.com` | `54.215.24.50` | Sí | Portal web principal corporativo y de cara al cliente. |
| `accounts.idmapper.api.playstation.com` | `23.200.88.59` | Sí | Microservicio de backend para la autenticación y mapeo de IDs. |
| `blog.us.playstation.com` | `66.35.205.126` | Sí | Portal de noticias y comunidad de usuarios. |
| `stage.adaptorapi.playstation.com` | `184.169.224.49` | Sí | Entorno de pre-producción (stage) para pruebas de API. |
| `laco-user-data-retrieval.api...` | Oculta por CDN | Sí | Endpoint de telemetría y recuperación de datos de usuario. |
| `playstation.zendesk.com` | N/A | No (Tercero) | Portal de soporte técnico alojado en SaaS externo. |

## Infraestructura y servicios
*Basado en consultas DNS, Netcraft y Shodan InternetDB.*

*   **Hosting y Red:** Infraestructura cloud nativa alojada en **AWS (EC2, Route 53)** con balanceadores de carga (Elastic Load Balancing). Todo el tráfico perimetral es gestionado y mitigado por la CDN y el WAF de **Akamai**.
*   **Tecnologías Web:** Los servidores web exponen cabeceras seguras (X-Frame-Options, X-Content-Type-Options) y operan con HTML5, JavaScript y el framework visual D3.js.
*   **Servicios Expuestos:** La IP principal de la web (`54.215.24.50`) solo expone los puertos estándar **80 (HTTP) y 443 (HTTPS)**. Shodan no reporta vulnerabilidades (CVEs) públicas pasivas.
*   **Correo y Terceros:** Correo corporativo gestionado integralmente bajo **Microsoft 365** (protección Outlook). Alta integración de servicios SaaS verificados por DNS (Zoom, Klaviyo, Google Workspace) y un uso intensivo del CRM **Salesforce**.

## Correos y personas
*Basado en la ejecución de theHarvester y Dorks de LinkedIn.*

*   **Patrón y Direcciones:** Debido a las restricciones de API de las fuentes abiertas y la madurez del objetivo, no se han recolectado direcciones en texto plano. Históricamente, el patrón corporativo asume formatos estándar (`nombre.apellido@playstation.com`), fuertemente protegidos por filtros anti-spam y Microsoft Defender.
*   **Organización:** La búsqueda pasiva (Dorks) en LinkedIn revela una estructura departamental segmentada, destacando perfiles técnicos especializados en **DevOps, Seguridad de la Información (InfoSec) y Cloud Architecture**. Esto indica que cualquier ataque de ingeniería social o *phishing* enfrentaría a personal altamente capacitado.

## Puntos de interés (Fase Activa)
Para iniciar la fase activa (interactuando con los servidores bajo las reglas del programa), se priorizarán los siguientes tres vectores, derivados de la información pasiva:

1.  **Entornos de pre-producción (*Stage/Dev/QA*):** 
    *   Por qué: Subdominios como `stage.adaptorapi.playstation.com` o `dev.api.bridges.playstation.com` (descubiertos por theHarvester) suelen tener versiones de código más recientes, funcionalidades no publicadas o políticas de seguridad y WAF menos restrictivas que los entornos de producción.
2.  **El directorio `/explore/testing/` y rutas internas:**
    *   Por qué: Identificado explícitamente como bloqueado (`Disallow`) en el archivo `robots.txt`. Los directorios de pruebas suelen contener *endpoints* abandonados, credenciales por defecto o información de depuración debug que facilitan la escalada de privilegios. 
3.  **Arquitectura de APIs y Telemetría:**
    *   Por qué: Subdominios como `telemetry-cii.api.playstation.com` o `accounts.idmapper.api...` indican un diseño basado en microservicios. Las APIs son el vector más productivo en programas modernos para probar vulnerabilidades de lógica de negocio, manipulación de parámetros y BOLA (Broken Object Level Authorization).