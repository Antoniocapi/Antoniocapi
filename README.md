# FM27 · Salamanca CF UDS: herramienta de gestión

Herramienta local en Python para gestionar la partida con el modelo de Voulgaris (CD Castellón). Los informes se generan en Markdown y Excel, en `informes/`, con la fecha de juego en el nombre.

## Por dónde empezar

1. **Panel de analista** (privado, en claude.ai): es el sitio principal. Tiene pestañas:
   - **Inicio**: qué hacer ahora, ordenado por urgencia.
   - **Partidos**: xG y resultados, próximos rivales.
   - **Táctica**: once propuesto y cambios en las instrucciones.
   - **Plantilla**: notas, sueldos y la acción de cada jugador.
   - **Contratos**: cláusulas, renovaciones y sueldos por encima del tope.
   - **Cantera**: jóvenes con futuro y dónde deben jugar.
   - **Liga**: clasificación y métricas frente a la media.
2. **Informes** (`informes/`): lo mismo en Markdown y Excel, por fecha de juego.
3. **Datos** (`data/`): lo transcrito de tus capturas. Las notas de cada captura están en `data/capturas/NOTAS_TRANSCRIPCION.md`.
4. **Análisis editable** (`data/analisis/`): tareas, once propuesto y cambios de táctica. Si cambias algo, el panel lo recoge en la siguiente actualización.

## Instalación (una vez)

```
pip install -r requirements.txt
```

## Flujo de trabajo

1. Haces capturas de las vistas del FM y las guardas en `data/capturas/`.
2. Las capturas se transcriben a CSV en `data/plantilla/` (o `data/ojeo/`) con este nombre:
   `grupo_vista_AAAA-MM-DD.csv`, donde la fecha es la **del juego**.
   - grupo de plantilla: `primer-equipo`, `filial` o `juvenil`.
   - en ojeo, el grupo es el nombre del foco, por ejemplo `laterales-izquierdos_2029-01-05.csv`.
   - Haz todas las vistas de un mismo equipo **el mismo día de juego**: así se juntan (información general + estadísticas + contratos…).
3. Ejecutas el comando del informe que quieras. Cada comando importa antes los CSV nuevos a la base de datos `fm.db`, así que el historial se va guardando solo.

## Comandos

| Comando | Qué hace |
|---|---|
| `python fm.py revisar` | Lista los archivos importados y los datos que faltan para cada informe. |
| `python fm.py contratos` | Contratos de 18 meses o menos con su fecha límite (1 de enero), cláusulas bajas en jugadores de 4★ o más, sueldos frente a los topes y masa salarial. |
| `python fm.py plantilla` | RENOVAR / VENDER YA / CEDER / SALE LIBRE / MANTENER con el motivo en una frase, más la cobertura de cada posición de la táctica. |
| `python fm.py fichajes` | Ranking 0-100 "modelo Castellón" por posición, con la lista de descartados y su motivo. |
| `python fm.py cantera` | Jugadores de 19 años o menos con potencial de 4★ o más, su evolución y dónde deben jugar. |
| `python fm.py partidos` | Bloques de 10 jornadas: xG, xPts, casa/fuera, rivales de arriba/abajo, mentalidad y alertas de faltas y tarjetas. |
| `python fm.py equipo` | Analítica del Centro de datos frente a la media de la liga: juego (xG) frente a resultados y métricas mejores o peores que la media. |
| `python fm.py disciplina` | Amarillas por jugador y quién está a 1 o 2 de la sanción. |
| `python fm.py evolucion` | Cambios de estrellas y valor entre capturas. Para un jugador: `python fm.py evolucion "Pau Calvo"`. |
| `python fm.py todo` | Genera todos los informes. |

## Partidos

Rellena `data/partidos/partidos.csv`, una fila por partido. Puedes abrirlo en Excel; el separador es `;`.

- **Resultado**: tus goles primero (`2-1`).
- **Jornada**: vacía en los partidos de copa.
- **Posición rival**: su puesto en la tabla ese día; sirve para comparar contra los de arriba y los de abajo.
- **Local/Visitante**: escribe `Local` o `Visitante`.

## Liga

En `data/liga/` se guardan la clasificación (`clasificacion_AAAA-MM-DD.csv`) y el calendario (`calendario_AAAA-MM-DD.csv`) sacados de las capturas del Portal. Si en `partidos.csv` dejas vacía la «Posición rival», se toma de la última clasificación. El informe de partidos también muestra los próximos rivales y en qué parte de la tabla están.

## Panel de analista

`python fm.py panel` exporta a `panel/` los CSV del panel de analista privado de claude.ai (partidos, plantilla, métricas del Centro de datos y clasificación). La página del panel está en `panel/index.html`. Cuando hay datos nuevos, Claude sube los CSV al panel.

## Configuración

Todo se ajusta en `config.yaml`: topes de sueldo, reserva de enero, presupuesto salarial, edad máxima para renovar, criterio del potencial (mínimo/media/máximo), posiciones necesarias con su prioridad, pesos de la puntuación de fichajes, umbrales de alerta, ciclo de amarillas, etc.

## Si falta un dato

La herramienta **no inventa nada**. Si una columna no está en las capturas (cláusula, nota media, minutos, amarillas, valoración de entrenamiento…), el informe lo avisa y ese apartado se activa solo cuando aparezca la columna.
