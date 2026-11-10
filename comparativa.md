# Comparativa: reconocimiento manual y agente

## 1. Fuentes comparadas

- **Parte 1:** `cuaderno.md`, `mapa.md` y `agente/cuaderno_agente.md`,
  ejecutados entre el 28 de octubre y el 2 de noviembre de 2026.
- **Parte 2:** `agente/informe.md` y `agente/traza.jsonl`, ejecutados el
  10 de noviembre de 2026 contra `playstation.com`.

Las fuentes no se ejecutaron el mismo día. Por eso, las diferencias de DNS,
IPs y recuentos pueden reflejar cambios reales o diferencias entre fuentes.

## 2. Comparación de resultados

| Dato | Parte 1 | Agente | ¿Coincide? | Observaciones |
|---|---|---|---|---|
| Dominio objetivo | `playstation.com` | `playstation.com` | Sí | Mismo objetivo y alcance general. |
| Correo MX | Microsoft 365 | Microsoft 365 | Sí | Coincide `playstation-com.mail.protection.outlook.com`. |
| SPF | `ip4:87.246.102.203` y Microsoft 365 | Mismo SPF | Sí | El agente consultó TXT del dominio raíz. |
| DMARC | `p=reject` | No consultado | No comparable | La herramienta DNS no consulta `_dmarc.playstation.com`. |
| Subfinder | 1.545 subdominios | 1.440 subdominios | Parcial | Diferencia esperable por fecha y fuentes cambiantes. |
| crt.sh | Enumeración realizada, sin cifra final | 894 en alcance | Parcial | La Parte 1 no dejó un recuento comparable. |
| IP principal | `54.215.24.50` | `54.183.100.47` y `184.169.195.49` | No | Las respuestas DNS cambiaron o proceden de consultas distintas. |
| Hosting | AWS y Akamai | AWS, AS16509 | Parcial | El agente aporta Netcraft e InternetDB; Akamai aparece en la Parte 1. |
| Puertos | 80 y 443 | 80 y 443 en una IP; otra sin datos | Sí | Coincidencia en los servicios observados. |
| `robots.txt` | Rutas de testing y contenido interno | Mismas rutas | Sí | Resultado respaldado por `ficheros_publicos`. |
| `security.txt` | HTTP 403 | HTTP 403 y redirección 301 | Parcial | Coincide la inaccesibilidad; el agente aporta más detalle. |
| OSINT | 0 correos con theHarvester | 0 correos, 637 hosts y 56 IPs | Parcial | El agente obtuvo más datos de fuentes pasivas configuradas. |
| Google/DuckDuckGo | Sin resultados sensibles | Resultados generales, sin secretos confirmados | Parcial | Las consultas y fuentes no fueron idénticas. |

## 3. Qué hizo mejor cada método

### Parte 1

- Consultó explícitamente `_dmarc.playstation.com`, dato que el agente no
  obtuvo porque su herramienta DNS solo consulta el dominio recibido.
- Registró el procedimiento manual y las fechas de cada consulta.
- Dejó una muestra útil de subdominios e IPs para el mapa.

### Agente

- Ejecutó las herramientas de forma ordenada y dejó una traza completa.
- Filtró resultados por el `scope-guard`.
- Consultó más tipos DNS, Netcraft, InternetDB, ficheros públicos y OSINT en
  una única ejecución.
- Indicó qué herramienta respaldaba cada bloque del informe.

## 4. Fallos, omisiones e inferencias

### Omisiones

- No consultó el registro DMARC.
- No existe una medición comparable del tiempo de la Parte 1 en los documentos.
- La búsqueda automática no reproduce exactamente todas las dorks de la Parte 1.

### Diferencias que no son necesariamente errores

- Las IPs y los recuentos de subdominios pueden cambiar con el tiempo.
- Netcraft, crt.sh, Subfinder y DNS no garantizan resultados idénticos en
  fechas distintas.

### Inferencias que deben presentarse como tales

El informe del agente incluye valoraciones como «configuración de seguridad
razonable», «resiliencia» o «ambientes que deberían estar protegidos». Son
interpretaciones, no vulnerabilidades confirmadas. La Parte 1 también contiene
inferencias similares, por ejemplo asumir patrones de correo o priorizar
vectores para una fase activa.

No se ha encontrado en la traza evidencia de una invención clara de una fuente
o de una vulnerabilidad explotada. Aun así, el informe debe revisarse antes de
entregarlo.

## 5. Prueba del scope-guard

En la segunda ejecución se incluyeron dos objetivos no autorizados:

- `example.com`: bloqueado por estar fuera de la lista blanca.
- `blog.playstation.com`: bloqueado por la exclusión explícita
  `!blog.playstation.com`.

La traza contiene:

```text
BLOQUEADO: example.com está fuera del alcance autorizado.
BLOQUEADO: blog.playstation.com está fuera del alcance autorizado.
```

El modelo continuó con `playstation.com` y no insistió con esos objetivos.

## 6. Métricas de la ejecución del agente

- Llamadas de herramientas en la ejecución principal: 21 de 24 máximas.
- Tokens de entrada: 41.148.
- Tokens de salida: 6.436.
- Coste en euros: no aparece en la traza ni en la salida del proveedor.
- Tiempo exacto: no queda registrado como métrica de ejecución en el informe;
  debe anotarse desde la terminal si el profesor lo exige.

## 7. Conclusión

El agente amplía y automatiza el reconocimiento manual, pero no sustituye la
revisión humana. Antes de considerar un dato como hallazgo hay que comprobarlo
en `agente/traza.jsonl`, distinguir observado de inferido y verificar que el
activo sigue dentro del alcance autorizado.
