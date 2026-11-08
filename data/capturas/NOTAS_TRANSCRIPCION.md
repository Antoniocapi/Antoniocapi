# Notas de transcripción de capturas

## 18/09/2028 · Información general (primer equipo, filial y juvenil)

Capturas: `primer-equipo_…`, `filial_…` y `juvenil_…_2028-09-18.webp` → CSV en `data/plantilla/`.

Conversiones aplicadas:
- **Dinero**: "m €" = miles. `52m € p/a` → `52000`. El valor de traspaso es un rango: `14m € - 65m €` → `14000-65000`.
- **Estrellas**: media estrella = `.5`. En el **potencial**, las estrellas **blancas** (rango incierto del ojeo) se guardan como rango: 3 doradas + 1 blanca → `3-4`; 3 doradas + media dorada + media blanca + media blanca → `3.5-4.5`.
- **Celdas vacías**: "-", "Sin datos", "N/D" y "No disponible" se dejan vacías.

Avisos (celdas cortadas en la captura; transcrito solo lo que se ve):
- Aimar Vicandi · Posición: `ME (DI), MP (DI...`
- Ivan Murgia · Posición: `DF (C), MC, ME...`
- Raúl Ruiz · Posición: `DF/CR/ME/MP...`
- Manuel · Posición: `DF (DC), MC, ...`
- Mario Segura (`19,25m € p...`) e Isaac Varela (`18,25m € p...`) · Sueldo: cortado el "p/a", pero el importe se lee entero.

Otros:
- Filial: 4 jugadores en gris sin datos (Willian Obama, Carlos Flores, Matías Aguirre, Eric). Solo tienen posición, edad y país.
- Joaquín Tello aparece en el primer equipo (marca "B") y en el filial.
- Columna Inf: Seg = le siguen otros clubes, B = con minutos en el B, Juv = juvenil (confirmado). "Les" y "Trn" se dejan tal cual.
- El nombre de David Hamansenya y Xavi Miràngels sale en **azul** (= cedidos a nuestro club, confirmado); el de Jorge María, Andrei Roateș y Pablo Arbós sale en **rosa** ("Cedido en otro club").

## 18/09/2028 · Portal (vista general)

Captura: `portal_vista-general_2028-09-18.webp`.

- **Clasificación** → `data/liga/clasificacion_2028-09-18.csv`. El FM no muestra la columna de empates; sale de Jug − G − P.
- **Calendario** → `data/liga/calendario_2028-09-18.csv`. El resultado se copia tal cual sale en el FM (goles del local primero). Nombres cortados que he completado con la clasificación: "R.C. Alcobe..." = R.C. Alcobendas y "Fuenlabra..." = Fuenlabrada. La última fila (26/11 Las Rozas, F) sale medio cortada, pero se lee.
- **Partidos** → `data/partidos/partidos.csv`, con nuestros goles primero:
  - Coria 1-2 Salamanca (punto verde) → `2-1`.
  - Unionistas 1-1 → `1-1`.
  - Guijuelo 0-0 → `0-0`.
  - La jornada (2, 3 y 4) la deduzco: la clasificación dice 4 jugados y estos son los 3 últimos.
  - **Falta la jornada 1**: no sale en la captura. Por la clasificación, la perdimos por 2 goles de diferencia.
  - **xG y estadísticas: vacíos** (no salen en el Portal).
- **Presupuestos** → `config.yaml`. Aquí "M" = millones: 1,82M € = 1.820.000 €.
  - Fichajes: disponible 14.000 €, gastado 39.150 €.
  - Sueldos: gasto 1.820.000 € al año, disponible 195.000 € al año.
