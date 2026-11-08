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

## 18/09/2028 · Tácticas > Centro de datos (análisis del segundo entrenador)

Capturas: `analitica_*_2028-09-18.webp` → `data/analitica/equipo_2028-09-18.csv` y `data/analitica/jugador_2028-09-18.csv`.

- Son valores por partido de la temporada (4 jornadas), comparados con la media de la 2ª Federación Gr. 5 (en el jugador, con la media de su rol).
- La métrica `% Pase` sale en las 3 capturas con el mismo valor (80,2 / 88,4); `Gol/Par`, `xG- Sp/90`, `Dis/Par`, `% disparos`, `Enc/Par`, `xGC/Par` y `% ent` se repiten en varias y coinciden.
- **Gráfico de pases (pases intentados por partido / % completados)**: no se leen los números del eje vertical (están cortados). Solo apunto lo que dice el FM: somos el equipo que menos pases da y de los menos precisos (esquina inferior izquierda).
- Sin confirmar qué mide `Imb` ni el sentido exacto de `1/3 final pas con/par`: no los valoro como mejor/peor.
- **Jornada 1** (dato del usuario): Numantia 2-0 Salamanca → en `partidos.csv` como `0-2`. Sin fecha ni campo: no los sé.
- **Jornada 1**: el usuario confirma que fue **fuera de casa**. La fecha sigue sin saberse.

## 18/09/2028 · Centro de datos (balón parado, juego aéreo y acciones defensivas)

- **Balón parado defensivo** (gráfico de dispersión): somos el escudo de arriba a la derecha. Valores **leídos a ojo** con las marcas de los ejes:
  - centros del rival a balón parado ≈ 11,8 por partido (media ≈ 6,3);
  - xA del rival a balón parado ≈ 0,16 por partido (media ≈ 0,06).
  - El FM dice: "Encajamos más xA a balón parado que la media" y "Recibimos más centros a balón parado que la media".
- **Óscar León, juego aéreo** (relativo a los delanteros de la división; leído a ojo):
  - ≈ 9,8 cabezazos intentados por 90' (media ≈ 4,3);
  - ≈ 13 % ganados (media ≈ 29 %).
  - En el gráfico hay un segundo jugador con foto, sin nombre: no lo transcribo.
- **Acciones defensivas**: 84 por partido (media 66). Por zonas, de nuestra área a la del rival: 42 %, 29 %, 14 %, 7 %, 4 % y 4 %. El FM dice que la mayoría son cerca de nuestra área.
