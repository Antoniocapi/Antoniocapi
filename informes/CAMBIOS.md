# Qué se ha hecho (lo último, arriba)

## 09/11 · Fichaje: Ekain Orobengoa (DL)
- Libre, 24 años, 3★/4★, delantero centro y extremo izquierdo. 4º del ranking (80/100).
- En `fichados` de config.yaml: sale como «Fichado» en el panel. Siguiente prioridad: lateral izquierdo.

## 09/11 · Renovaciones cerradas salvo Calvo
- Renovados: León, Eceizabarrena, Balan y Jordi Martínez (en `renovados` de config.yaml).
- **Calvo pide 120.000 €**: sueldo justo ≈73.000 €. Propuesta: contraoferta de 70.000-80.000 € con primas; si no acepta, venderlo en enero.

## 09/11 · Portal del 23/12/2028
- **Clasificación**: 6º con 29 puntos, a 1 del playoff. 19 de 24 puntos en las jornadas 10-17 y 3 victorias seguidas.
- **Renovados**: León (3 años) y Eceizabarrena (2 años). Ya no salen como «renovar»; falta la captura de sus nuevos contratos.
- **Presupuesto**: 116.000 € al año para sueldos y 14.000 € para traspasos. En el mercado de invierno la reserva de enero ya se puede gastar (`usar_reserva: true`): el margen para fichar es de 116.000 €. Ranking recalculado.
- **Panel**: clasificación y calendario nuevos (próximo: C.D. Coria, 07/01) y cuenta atrás al 23/12.

## 09/11 · Panel rediseñado: más visual, menos tablas
- **Inicio**: cuenta atrás hasta el 1 de enero, 4 cifras clave y un **tablero de decisiones** (Renovar ya · Proteger cláusula · Vender o sacar · Fichar) con fichas de jugador.
- **Plantilla**: fichas por línea (porteros, defensas, medios y ataque), con una barra de calidad a potencial, la nota y un color por acción. Botón para cambiar de equipo.
- **Contratos**: semáforo por columnas y gráfico de cláusula frente a valor de mercado.
- **Mercado**: tarjetas de candidatos con un anillo de puntuación.
- **Cantera**: mapa calidad/potencial y fichas agrupadas por dónde deben jugar.
- **Fuera la pestaña Táctica** (ahora la lleva el segundo entrenador). Todas las tablas siguen disponibles, plegadas en «Ver tablas».

## 09/11 · 17/12/2028: plantillas al día y plan del mercado de invierno
- **Transcrito**: estadísticas del primer equipo y del Salamanca B, y la vista general del B y del juvenil (estrellas nuevas).
- **Herramienta**: ahora junta la vista más reciente de cada tipo (las estadísticas del 17/12 con los contratos del 18/09) y rellena los datos de quien sube de categoría (Ruvira).
- **Reglas corregidas**: la nota baja ya no manda vender a canteranos; quien rinde muy por encima de sus estrellas (Cojo, 7,09) ya no sale como «sale libre».
- **Nuevo informe**: `2028-12-17_mercado-invierno.md`, el plan del director deportivo: renovaciones antes del 1/1, cláusulas, salidas, fichajes y cantera.
- **Tareas**: rehechas para el mercado.
- **Ojeo de delanteros** (20 jugadores): ranking en `2028-12-17_fichajes.md` y en la nueva pestaña **Mercado** del panel. Primero: **Genís Clua** (19, 3,5/4,5-5★, sin contrato).
- **Fichajes**: quitado el tope fijo de 60.000 €; solo se descarta lo que no cabe en el margen salarial o en el presupuesto de traspasos.
- `config.yaml`: posiciones necesarias = DL (C) alta, DF (I) alta, POR baja.

## 09/11 · Jornada 9: Fuenlabrada 0-0 Salamanca
- **Transcrito**: estadísticas y once inicial con nota (pantalla Resultado).
- **Partido**: punto con algo de suerte (0,79 de xG frente a 1,47, 0 ocasiones claras). Cuarta portería a cero de la temporada y solo 3 faltas. León volvió (6,2) sin ocasiones.
- **Temporada**: 10 puntos en 9 jornadas con 11,3 puntos esperados. 5 goles con 9,64 de xG; 2 partidos seguidos sin marcar.
- **Próximo**: la jornada 10 cierra el primer bloque; con la clasificación completa y las estadísticas de la plantilla hago la revisión de bloque.

## 09/11 · Jornada 8: Salamanca 0-2 Zamora
- **Transcrito**: estadísticas, jugadores en el campo al final con su nota, goles y clasificación parcial (seguimos 10º con 9 puntos).
- **Partido**: nos superaron (0,65 de xG frente a 2,10, 32 % de posesión, 10 córners en contra). Goles suyos en el 68' y el 79'.
- **Patrón**: contra los de arriba (Numantia y Zamora), 0,98 de xG a favor y 4,47 en contra. Contra el resto somos mejores.
- **Tarea urgente nueva**: plan específico para rivales de arriba (próximo: U. Adarve, 1º, el 12/11).

## 09/11 · Jornada 7: Valladolid B 2-1 Salamanca
- **Transcrito**: estadísticas, jugadores en el campo al final con su nota, goles y parte de la clasificación (seguimos 10º con 9 puntos).
- **Partido**: derrota injusta por xG (1,84 frente a 1,65). 17 tiros, 65 pases progresivos y 3 ocasiones claras frente a 0, pero gol suyo en el 5'. Desde el banquillo: gol de Valdaliso (87'), asistencia de Tello y debut de Ruvira (16 años, 6,8).
- **Temporada**: 9 puntos con 9,96 puntos esperados (−0,96). El problema claro es la puntería: 5 goles con 8,20 de xG.
- **Tareas**: nueva «Más finalización en los entrenamientos». «Subir a Ruvira», hecha. Valdaliso ya no se cede (añadido a `no_ceder` en config.yaml).
- **Panel**: actualizado. La comprobación automática no ha llegado a ejecutarse (el panel no estaba abierto); se hará al abrirlo.

## 09/11 · Corrección: en la J5 y la J6 las flechas marcan a los que ENTRARON
- Como Bilbao y Hamansenya marcaron en el 29' y luego los cambiaste por cansancio, las capturas del 90' muestran a quien estaba en el campo al final. Las flechas son los que entraron desde el banquillo. Lo había leído al revés.
- **Corregido**: alineaciones (titular o suplente), análisis de la J5 y la J6 y notas de transcripción. Bilbao y Hamansenya, titulares en la J6 (sin nota en la captura).
- El informe de partidos separa ahora **partidos jugados** y **titularidades**.

## 09/11 · Jornada 6: Salamanca 1-0 Mirandés B · y León internacional
- **Transcrito**: estadísticas, once con notas, gol (29', Bilbao, asistencia de Hamansenya), calendario y parte de la clasificación (10º con 9 puntos).
- **Partido**: el mejor de la temporada. 2,29 de xG frente a 0,33, 3 ocasiones claras frente a 0 y tercera portería a cero seguida. Cojo 7,6, Murúa 7,4 y Luis Paulo 7,3.
- **Hito**: el xG total es positivo por primera vez (6,36 frente a 6,23). Sin la J1, 6,03 frente a 3,86.
- **Problema nuevo**: la puntería, con 4 goles y 6,36 de xG. Y León es internacional (República Dominicana): faltará en cada parón.
- **Cambios en el plan**: sin León, Escribano de 9 (mejor que Benítes). El **delantero centro pasa a prioridad alta en enero**, por delante del lateral izquierdo.
- **Panel**: comprobación correcta.

## 09/11 · Confirmación: flechas = cambios
- Anotado en las notas de transcripción: en la J5 salieron Benítes, Valdaliso, Edu González, Kadochnikov y Osei. Falta saber quién entró.

## 09/11 · Jornada 5: Salamanca 0-0 R.C. Alcobendas
- **Transcrito**: estadísticas, once con notas y resultado; calendario y parte de la clasificación (solo se ven los puestos 9-15, quedamos 12º con 6 puntos).
- **Partido**: el más completo con balón. 53 % de posesión, 84 % de pase, 10 tiros frente a 8, xG 0,78 frente a 0,35, solo 7 faltas y 5 córners en contra. Faltó el gol: jugó Benítes (17 años) de 9, con León y Escribano fuera del once.
- **Temporada**: 6 puntos con 5,85 puntos esperados; los resultados ya reflejan el juego. En las 4 últimas jornadas, más xG que el rival (3,74 frente a 3,53).
- **Tareas**: hechas «Miràngels fuera» y «Luis Paulo de central» (7,1, el mejor de campo). León sigue sin ser titular.
- **Panel**: comprobación correcta.

## 09/11 · Centro de datos: goles, pase, físico y juego aéreo
- **Transcrito**: análisis de goles, pase de Jiménez y de Alsúa, físico de los defensas y juego aéreo de los delanteros. Los valores de los gráficos son aproximados, leídos a ojo.
- **Hallazgos** (bloque 8 de la pestaña Análisis):
  - Jiménez completa ≈44 % de sus pases (media ≈83 %): jugamos en largo y lo perdemos. → Saques de puerta cortos y portero en corto.
  - Alsúa toca poco el balón (≈47 pases por 90', media ≈60) y con menos acierto (≈86 %, media ≈90 %).
  - Cojo es el defensa más intenso de la liga (≈11 esprints por 90', media ≈4,7).
  - Escribano gana ≈41 % de los balones aéreos y León el 13 %. → Escribano a la lista de rematadores en los córners a favor.
  - Análisis de goles histórico: no encajamos entre el 76' y el 90' y marcamos el 26 % de nuestros goles del 76' en adelante.
- **Pendiente de confirmar**: el análisis de goles suma 74 a favor y 53 en contra, así que no es de esta temporada. ¿Qué periodo cubre?

## 09/11 · Plantilla por equipos, sueldo justo e informe de analista
- **Plantilla dividida**: en el panel, tres tablas (Primer equipo, Salamanca B y Juvenil) con todos los jugadores. Tello sale en los dos equipos en los que está inscrito. El filial se llama ahora "Salamanca B" en todos los informes.
- **Sueldo justo (sin topes fijos)**: modelo estadístico nuevo. Con la misma masa salarial de cada equipo, calcula lo que le correspondería a cada jugador por lo que aporta (calidad, nota ajustada por minutos, participación y margen de mejora). Si mejora, su sueldo justo sube.
  - Cobran de más: Vicandi (+159 %), Bilbao (+167 %), Kadochnikov (+78 %) y Ucín (+75 %).
  - Cobran de menos: León (−49 %), Escribano (−46 %), Jiménez (−43 %) y Calvo (−41 %). Al renovarlos, subirles el sueldo.
  - Está en el informe de contratos, en la pestaña Plantilla (gráfico de sueldo real frente a sueldo justo) y en Contratos (tabla de sueldos que no cuadran).
- **Informe de analista** (pestaña nueva "Análisis" e `informes/2028-09-18_analisis.md`): 25 puntos en 8 bloques sobre las jornadas 1-4, con la lista de capturas que necesito para profundizar.
- **Rectificación**: retiro lo de subir la línea defensiva. Contra el Guijuelo, con el bloque más bajo, concedimos solo 0,66 de xG. El problema son las faltas y el balón parado.
- **Comprobación del panel**: correcta.

## 09/11 · Estadísticas, defensa aérea y Luis Paulo al once
- **Transcrito**: estadísticas del primer equipo (minutos, amarillas, media, goles, asistencias) y la lista de "Defensas aéreos" de los córners en contra.
- **Hallazgo**: los 4 mejores por arriba (Luis Paulo, Lucas Santos, Kadochnikov y Ucín) no son titulares, y los centrales titulares son débiles por arriba (Mulas, salto 9; Murúa, fuerza 5).
- **Cambio**: **Luis Paulo de central titular** por Mulas, y Lucas Santos convocado. Es la tarea urgente nº 6 del panel.
- **Disciplina**: 8 jugadores con 1 amarilla; nadie cerca de la sanción.
- **Cesiones**: ahora se calculan con los minutos reales. Siguen Marc Castro y Valdaliso.
- **Panel**: la tabla de Plantilla muestra los minutos y las amarillas.
- **Pendiente**: capturas de Entrenamiento → Valoraciones y de Balón parado → Faltas → Defensa.

## 09/11 · Panel con pestañas
- Panel dividido en Inicio, Partidos, Táctica, Plantilla, Contratos, Cantera y Liga, con la lista "Qué hacer ahora" y botones para ir a cada pestaña.
- Córners en contra: nadie cubre el segundo palo. C2 pasa a «Marcar segundo palo».
