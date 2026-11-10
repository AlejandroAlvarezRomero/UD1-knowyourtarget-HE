# Alcance de la Auditoría: PlayStation (Sony Interactive Entertainment)

**Programa:** https://hackerone.com/playstation
<br>
**Fecha de consulta:** 28 de octubre de 2026

## Dentro del alcance (In Scope)
El programa permite auditar una amplia superficie de ataque mediante dominios comodín (wildcards), cubriendo subdominios, APIs y redes de entretenimiento de Sony.

**Dominios comodín principales:**
* *.playstation.com
* *.playstation.net
* *.sonyentertainmentnetwork.com
* *.api.playstation.com

**Otros dominios específicos incluidos:**
* my.account.sony.com
* ca.account.sony.com

(Hardware como PS4/PS5 y las aplicaciones móviles Android/iOS están en el alcance del programa, pero quedan excluidos de esta auditoría web).

## Fuera de alcance (Out of Scope)
PlayStation excluye explícitamente los siguientes vectores y vulnerabilidades:
* Vulnerabilidades en servicios SaaS de terceros que escapan a su control.
* Ataques de ingeniería social contra empleados o ataques físicos a oficinas.
* Uso de cuentas de empleados comprometidas o credenciales robadas.
* Ataques de fuerza bruta y denegación de servicio (DoS) en redes/web.
* Informes generados por escáneres automáticos o herramientas de explotación.
* Secuestro de Route 53 NS.
* Problemas de bajo impacto: falta de cabeceras de seguridad, limitación de velocidad sin impacto, fingerprinting, revelación de errores, clickjacking o envenenamiento de caché no crítico.

## Reglas aplicadas en este proyecto

- Solo se han usado técnicas pasivas: consulta de fuentes públicas, DNS,
  transparencia de certificados y fuentes de terceros. La única consulta HTTP
  directa se limita a ficheros públicos estándar (`robots.txt` y
  `security.txt`).
- No se han realizado escaneos de puertos, pruebas de vulnerabilidades,
  fuerza bruta, fuzzing, denegación de servicio ni contacto con personas.
- Si apareciera información sensible, no se copiaría ni explotaría: se
  anotaría de forma mínima y se comunicaría por el canal del programa.
- Antes de cualquier fase posterior se debe revisar de nuevo la política
  vigente, incluidos requisitos de identificación y límites de peticiones.

