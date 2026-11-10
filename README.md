# Auditoría de Reconocimiento Pasivo: PlayStation (Sony Interactive Entertainment)

Repositorio oficial del proyecto de reconocimiento pasivo y OSINT desarrollado en el marco del curso de especialización en ciberseguridad.

##  Autor
* **Nombre:** Alejandro Álvarez Romero
* **Institución:** IES Rafael Alberti (Cádiz)
* **Contexto:** Práctica académica de reconocimiento y huella digital sobre entorno real en programa público de Bug Bounty (HackerOne).

---

##  Objetivo Elegido
* **Plataforma:** [HackerOne - PlayStation]
* **Alcance Autorizado:** 
  * `*.playstation.com`
  * `*.playstation.net`
  * `*.sonyentertainmentnetwork.com`
  * `*.api.playstation.com`
  * `my.account.sony.com`
  * `ca.account.sony.com`

---

##  Estructura y Enlaces de la Documentación

La documentación del proyecto se encuentra estructurada en fases secuenciales:

1. **[Alcance y Reglas (`alcance.md`)](./alcance.md)**
   <br>
   
   * Definición formal del objetivo, límites del programa de recompensas, dominios in-scope y exclusiones explícitas según HackerOne.

<br>

1. **[Cuaderno de Trabajo (`cuaderno.md`)](./cuaderno.md)**
<br>

   * Registro cronológico detallado de la ejecución en entorno Kali Linux siguiendo estrictamente la estructura exigida (`Cuándo · objetivo · qué hiciste · qué salió`). 
   * Incluye Whois, registros DNS (MX, TXT, DMARC), enumeración de subdominios (`subfinder`, `crt.sh`), huella tecnológica (Netcraft), análisis de ficheros (`robots.txt`), consulta de servicios (Shodan InternetDB), Google Dorks y OSINT de personal.
  <br>

1. **[Mapa de Inteligencia (`mapa.md`)](./mapa.md)**
   <br>
   * Documento ejecutivo de síntesis para el equipo antes de la fase activa.
   * Contiene el resumen perimetral, la tabla representativa de subdominios e IPs, análisis de la infraestructura cloud (AWS / Akamai), evaluación de perfiles de empleados y la priorización táctica de los 3 vectores iniciales para el laboratorio activo.

4. **Parte 2: agente**

   * [Código del agente](./agente/src/)
   * [Pruebas de alcance y prompt](./agente/pruebas.md)
   * [Plantilla del prompt](./agente/instrucciones.md)
   * [Traza JSONL](./agente/traza.jsonl)
   * La traza se puede convertir a formato legible con `agente/src/ver_traza.py`.
   * [Informe generado por la IA](./agente/informe.md)

5. **[Comparativa (`comparativa.md`)](./comparativa.md)**

   Compara la investigación manual de la Parte 1 con la ejecución del agente,
   incluyendo coincidencias, diferencias, omisiones, inferencias, métricas y
   la prueba del `scope-guard`.

El `scope.txt` de la raíz y el de `agente/src/` son idénticos. La ejecución
principal se conserva en `agente/`; no se incluyen claves ni credenciales.
