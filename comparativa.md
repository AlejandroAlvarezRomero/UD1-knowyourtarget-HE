# Comparativa: reconocimiento manual y agente

## 1. Fuentes comparadas

- **Parte 1:** `cuaderno.md` y `mapa.md`,
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

### Omisión

- No consultó el registro DMARC: en el cuaderno aparece la consulta a
  `_dmarc.playstation.com`, pero no hay una llamada equivalente en la traza.
- La búsqueda automática no reproduce exactamente todas las dorks manuales.

### Error o diferencia de fuente

- Las IPs y los recuentos de subdominios pueden cambiar con el tiempo.
- Netcraft, crt.sh, Subfinder y DNS no garantizan resultados idénticos en
  fechas distintas.

### Invención o inferencia no respaldada

El informe del agente incluye valoraciones como «configuración de seguridad
razonable», «resiliencia» o «ambientes que deberían estar protegidos». Son
interpretaciones, no vulnerabilidades confirmadas. La Parte 1 también contiene
inferencias similares, por ejemplo asumir patrones de correo o priorizar
vectores para una fase activa.

No hay evidencia de una vulnerabilidad inventada, pero expresiones como
«configuración de seguridad razonable» no son hechos devueltos por una fuente:
son interpretaciones del modelo y deben etiquetarse como tales.

### Intento fuera de alcance

La traza principal entregada no contiene un intento fuera de alcance. El
documento de pruebas anterior hacía referencia a una ejecución distinta que no
se conserva junto a la traza actual; por eso no se usa como evidencia en esta
comparativa.

## 5. Prueba del scope-guard

El código aplica una lista blanca y tiene pruebas unitarias del bloqueo, pero
la traza principal no contiene un intento fuera de alcance. No se debe afirmar
que el modelo reaccionó a ese caso si no hay una traza de esa ejecución.

## 6. Métricas de la ejecución del agente

- Llamadas de herramientas en la ejecución principal: 21 de 24 máximas.
- Tokens de entrada: 41.148.
- Tokens de salida: 6.436.
- Coste en euros: no aparece en la traza ni en la salida del proveedor.
- Tiempo exacto: no quedó registrado; no se puede reconstruir con precisión.

## 7. Conclusión

El agente ahorra trabajo repetitivo, sobre todo al consultar varias fuentes y
ordenar los resultados. El trabajo manual fue mejor al registrar DMARC y al
dar contexto a cada consulta. No usaría el informe del agente sin revisarlo:
confirmaría la fuente de cada afirmación, separaría hechos de inferencias y
revisaría de nuevo que cada activo siga dentro del alcance.
