# Créditos de las imágenes

## `laboratorio/` — Laboratorio 1, Robótica Industrial 2025-II

| Archivo | Descripción |
|---|---|
| `irb140_herramienta_caja.jpg` | IRB 140 del LabSIR con el portamarcador y la caja-pastel sobre la banda |
| `herramienta_cad.jpg` | Modelo CAD del portamarcador (Autodesk Inventor) |
| `herramienta_impresa.jpg` | Portamarcador impreso en PLA con el marcador |
| `caja_pastel.jpg` | Caja de 15 × 15 × 15 cm con tapa de acrílico |
| `robotstudio_estacion.jpg` | Estación de RobotStudio con robot, herramienta y caja |
| `robotstudio_trayectorias.jpg` | Trayectorias de los nombres sobre la caja en RobotStudio |
| `plano_planta.png` | Plano de planta de la celda en RobotStudio |

Origen: [Nicolas-Eule/Laboratorio_Robotica_1](https://github.com/Nicolas-Eule/Laboratorio_Robotica_1) (`assets/img`). Autores: Jorge Nicolás Garzón Acevedo, Johan Camilo Patiño Mogollón y Gabriel Eduardo Bojacá Munar. Las imágenes se redimensionaron y se convirtieron a JPG; el contenido no se modificó.

El programa de `rapid/lab01_decoracion/` proviene del mismo repositorio (`robotstudio/Load_FlexPendant` e `io/mapeo_IO.md`).

## `figuras/` — figuras propias

Diagramas elaborados para esta guía:

- **IRB 140 y RAPID:** ejes del IRB 140, marcos de referencia, zonas, tipos de movimiento, `Offs`/`RelTool` y trayectorias de ejemplo.
- **Laboratorio:** trayectoria del Laboratorio 1.
- **SCADA:** red del laboratorio y arquitectura SCADA.

Origen de los datos:

- `trayectorias_ejemplo.svg` usa los mismos parámetros de las rutinas RAPID del README.
- `trayectoria_laboratorio.svg` se calculó a partir de los `robtarget`, las instrucciones `MoveL` y los `wobjdata` de `rapid/lab01_decoracion/Module1.mod`.
- Las cotas del robot corresponden al modelo cinemático nominal del IRB 140, y los límites articulares al modelo de RobotStudio.
- Las direcciones IP de `red_laboratorio.svg` se tomaron de videos de prácticas del LabSIR y deben verificarse.

## `abb_librws/` — arquitectura RWS / EGM

`rws_egm_arquitectura.png` proviene de [ros-industrial/abb_librws](https://github.com/ros-industrial/abb_librws) (`docs/images/rws_sketch.png`), incluido en [labsir-un/abb_un_driver](https://github.com/labsir-un/abb_un_driver). © 2015 ABB Schweiz AG, licencia BSD-3-Clause; el texto completo está en [`abb_librws/LICENSE`](abb_librws/LICENSE).

## Imágenes de producto de ABB (enlazadas, no incluidas)

Las fotos del IRB 140 de la sección 1 del README se cargan directamente desde `cdn.productimages.abb.com`, el servidor de imágenes del sitio de producto de ABB Robotics. Son © ABB y no se redistribuyen en este repositorio. Si ABB cambia esas direcciones, las imágenes dejarán de mostrarse.

## Videos (miniaturas de YouTube enlazadas)

- **Sección 18:** simulación y ejecución del Laboratorio 1, Robótica Industrial 2025-II.
- **Sección 27:** prácticas de SCADA y Comunicaciones Industriales del LabSIR:
  - 2023-1: Andrés Holguín Restrepo, Sara Jiménez y Nicolás López Bermeo.
  - 2024-2: canal de Eduardo Barrera.
  - 2019, Grupo 5: Camilo Ávila, Danilo Suárez y Sebastián Gómez.
