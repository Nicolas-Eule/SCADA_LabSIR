# Programación RAPID para el ABB IRB140 — Guía introductoria

Repositorio de apoyo para el curso **Comunicaciones Industriales SCADA** — Laboratorio de Robótica, Universidad Nacional de Colombia, Sede Bogotá.

Este documento reúne, de forma introductoria, las instrucciones, funciones y tipos de datos de **RAPID** (el lenguaje de programación de los controladores ABB) que se pueden usar con el manipulador **IRB140** del laboratorio: cómo moverlo articulación por articulación, cómo construir trayectorias cartesianas, cómo usar variables y contadores para generar movimientos, cómo monitorear su estado y cómo comunicarlo con un sistema SCADA.

> **Alcance.** Los ejemplos están escritos para un controlador **IRC5 con RobotWare 6.x**. Antes de ejecutar cualquier programa en el robot real, revise la sección [0. Antes de empezar](#0-antes-de-empezar) y valide todo en **RobotStudio** con un controlador virtual.

---

## Tabla de contenido

0. [Antes de empezar](#0-antes-de-empezar)
1. [El manipulador IRB140](#1-el-manipulador-irb140)
2. [Estructura de un programa RAPID](#2-estructura-de-un-programa-rapid)
3. [Tipos de datos y declaración de variables](#3-tipos-de-datos-y-declaración-de-variables)
4. [Sistemas de coordenadas, herramientas y objetos de trabajo](#4-sistemas-de-coordenadas-herramientas-y-objetos-de-trabajo)
5. [Instrucciones de movimiento](#5-instrucciones-de-movimiento)
6. [Movimiento articular: control de los ángulos de cada eje](#6-movimiento-articular-control-de-los-ángulos-de-cada-eje)
7. [Funciones de posición y transformación](#7-funciones-de-posición-y-transformación)
8. [Construcción de trayectorias (ejemplos)](#8-construcción-de-trayectorias-ejemplos)
9. [Control de flujo](#9-control-de-flujo)
10. [Variables, contadores, arreglos y matemáticas](#10-variables-contadores-arreglos-y-matemáticas)
11. [Entradas y salidas (E/S)](#11-entradas-y-salidas-es)
12. [Interacción con el FlexPendant](#12-interacción-con-el-flexpendant)
13. [Interrupciones y manejo de errores](#13-interrupciones-y-manejo-de-errores)
14. [Monitoreo y seguimiento del robot](#14-monitoreo-y-seguimiento-del-robot)
15. [Comunicación con sistemas SCADA](#15-comunicación-con-sistemas-scada)
16. [Flujo de trabajo en el laboratorio](#16-flujo-de-trabajo-en-el-laboratorio)
17. [Errores comunes y buenas prácticas](#17-errores-comunes-y-buenas-prácticas)
18. [Referencias](#18-referencias)

---

## 0. Antes de empezar

Varios elementos dependen de la configuración específica del controlador del laboratorio. Verifíquelos antes de usar los ejemplos:

| Elemento | Dónde se verifica | Por qué importa |
|---|---|---|
| Versión de RobotWare | FlexPendant → *Información del sistema* | Robot Web Services solo existe desde RobotWare 6. |
| Opciones de software instaladas | FlexPendant → *Información del sistema → Opciones de sistema* | Sockets (*PC Interface*), multitarea (*Multitasking*) y buses de campo son opciones de pago. |
| Nombres de las señales de E/S | FlexPendant → *Entradas y salidas* / RobotStudio → *Configuración → I/O System* | En esta guía se usan nombres genéricos (`DI_01`, `DO_01`); sustitúyalos por los reales. |
| Herramienta montada (`tooldata`) | Medición del TCP en el laboratorio | Un TCP o una masa incorrectos producen trayectorias erróneas y mal desempeño dinámico. |
| Límites articulares configurados | RobotStudio → *Configuración → Motion → Arm* | Pueden ser más restrictivos que los límites mecánicos. |
| Zonas de seguridad de la celda | Responsable del laboratorio | Mesas, accesorios y otros equipos dentro del volumen de trabajo. |

**Regla de oro:** todo programa nuevo se ejecuta primero en RobotStudio, luego en el robot real en **modo manual** a velocidad reducida, y solo después en modo automático.

---

## 1. El manipulador IRB140

Robot industrial articulado de **6 ejes**, de carga ligera.

| Característica | Valor |
|---|---|
| Ejes | 6 (rotacionales) |
| Carga útil | 6 kg (versiones antiguas: 5 kg) |
| Alcance (al centro del eje 5) | 810 mm |
| Repetibilidad | ± 0,03 mm |
| Montaje | Piso, pared o invertido |
| Controlador | IRC5 (versiones anteriores: S4Cplus) |

### Límites y velocidades articulares

| Eje | Movimiento | Límite inferior | Límite superior | Velocidad máx. (IRB140) |
|---|---|---|---|---|
| 1 | Rotación de la base | −180° | +180° | 200 °/s |
| 2 | Brazo inferior | −90° | +110° | 200 °/s |
| 3 | Brazo superior | −230° | +50° | 260 °/s |
| 4 | Rotación de muñeca | −200° | +200° | 360 °/s |
| 5 | Flexión de muñeca | −120° | +120° | 360 °/s |
| 6 | Rotación de brida | −400° | +400° | 450 °/s |

> Límites tomados del modelo del IRB140 que usa RobotStudio. La hoja de datos de ABB indica un recorrido total de 230° para el eje 5 y define los ejes 4 y 6 como de rotación ilimitada (con 400° por defecto en el eje 4). **Los límites vigentes son los que estén configurados en el controlador** (ver sección 0).

**Posición de calibración / *home* típica:** `[0, 0, 0, 0, 30, 0]` grados (eje 5 a 30° para alejar la muñeca de la singularidad).

---

## 2. Estructura de un programa RAPID

Un programa RAPID se organiza en **tareas** (normalmente una sola: `T_ROB1`), cada una con **módulos**:

- **Módulos de programa** (`.mod`): contienen el código de la aplicación. Se cargan y descargan con el programa.
- **Módulos de sistema** (`.sys`): datos y rutinas permanentes del sistema (por ejemplo, `user.sys`, `BASE.sys`).

Dentro de un módulo existen tres tipos de rutinas:

| Rutina | Palabra clave | Uso |
|---|---|---|
| Procedimiento | `PROC ... ENDPROC` | Ejecuta acciones; no retorna valor. |
| Función | `FUNC <tipo> ... ENDFUNC` | Retorna un valor (`RETURN`). |
| Rutina de interrupción | `TRAP ... ENDTRAP` | Se ejecuta al dispararse una interrupción. |

El punto de entrada es el procedimiento `main`.

```rapid
MODULE Modulo_Ejemplo
    ! Comentarios con signo de exclamación

    ! ---- Datos ----
    CONST jointtarget jHome := [[0,0,0,0,30,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    VAR num contador := 0;

    ! ---- Rutina principal ----
    PROC main()
        Inicializar;
        MoveAbsJ jHome, v200, fine, tool0;
        TPWrite "Programa terminado. Ciclos: " \Num:=contador;
    ENDPROC

    ! ---- Procedimiento auxiliar ----
    PROC Inicializar()
        contador := 0;
        TPErase;
    ENDPROC

    ! ---- Función con parámetros ----
    FUNC num Cuadrado(num x)
        RETURN x * x;
    ENDFUNC
ENDMODULE
```

**Parámetros de rutinas:** se pasan por valor por defecto; `INOUT` permite modificar el argumento, `PERS`/`VAR` exigen el tipo de almacenamiento, y los parámetros opcionales se escriben con `\` (por ejemplo `PROC Mover(robtarget p \num vel)` y se consulta su presencia con `Present(vel)`).

---

## 3. Tipos de datos y declaración de variables

### 3.1 Tipos de almacenamiento

| Declaración | Comportamiento | Uso típico |
|---|---|---|
| `CONST` | Valor fijo, no se puede modificar en ejecución. | Puntos fijos, parámetros. |
| `VAR` | Se reinicia al valor inicial cuando se carga el programa o se mueve el puntero a `main`. | Contadores, variables de trabajo. |
| `PERS` | Persistente: el valor actual se guarda en el código y sobrevive a reinicios del programa. Es visible desde otras tareas y desde el exterior. | Datos de herramienta, comunicación con SCADA. |

### 3.2 Tipos básicos

| Tipo | Descripción | Ejemplo |
|---|---|---|
| `num` | Número real (o entero) | `VAR num i := 0;` |
| `dnum` | Número de doble precisión | `VAR dnum t := 0;` |
| `bool` | Lógico | `VAR bool listo := FALSE;` |
| `string` | Texto (máx. 80 caracteres) | `VAR string msg := "Hola";` |
| `byte` | Entero 0–255 | `VAR byte b := 10;` |

### 3.3 Tipos de movimiento y geometría

| Tipo | Contenido | Estructura |
|---|---|---|
| `pos` | Posición cartesiana [mm] | `[x, y, z]` |
| `orient` | Orientación en cuaternión | `[q1, q2, q3, q4]` |
| `pose` | Marco de referencia | `[pos, orient]` |
| `confdata` | Configuración del brazo (cuadrantes) | `[cf1, cf4, cf6, cfx]` |
| `extjoint` | Ejes externos (`9E9` = sin eje) | `[e1, …, e6]` |
| `robtarget` | Punto cartesiano del TCP | `[pos, orient, confdata, extjoint]` |
| `robjoint` | Ángulos de los 6 ejes [°] | `[rax_1, …, rax_6]` |
| `jointtarget` | Posición articular | `[robjoint, extjoint]` |
| `speeddata` | Velocidad | `[v_tcp, v_ori, v_leax, v_reax]` |
| `zonedata` | Zona de aproximación | `fine`, `z0`, `z1`, `z5`, `z10`, … |
| `tooldata` | Herramienta (TCP + carga) | `[robhold, tframe, tload]` |
| `wobjdata` | Objeto de trabajo | `[robhold, ufprog, ufmec, uframe, oframe]` |
| `loaddata` | Carga útil | `[masa, cog, aom, ix, iy, iz]` |

Acceso a componentes con punto: `p10.trans.x`, `p10.rot`, `j1.robax.rax_3`.

### 3.4 Datos predefinidos útiles

- **Velocidades** (`speeddata`): `v5`, `v10`, `v20`, `v50`, `v100`, `v150`, `v200`, `v300`, `v400`, `v500`, `v600`, `v800`, `v1000`, `v1500`, `v2000`, `v2500`, `v3000`, `v4000`, `v5000`, `v6000`, `v7000`, `vmax` (mm/s del TCP).
- **Zonas** (`zonedata`): `fine` (parada exacta), `z0`, `z1`, `z5`, `z10`, `z15`, `z20`, `z30`, `z40`, `z50`, `z60`, `z80`, `z100`, `z150`, `z200` (radio en mm).
- **Herramienta y objeto por defecto:** `tool0` (TCP en el centro de la brida) y `wobj0` (coincide con el sistema de la base).

### 3.5 Declaración de un `robtarget`

```rapid
!                         pos [mm]        orient (cuaternión)   confdata     ejes externos
CONST robtarget pA := [[500, 0, 400], [0, 0, 1, 0], [0, 0, 0, 0], [9E9,9E9,9E9,9E9,9E9,9E9]];
```

El cuaternión `[0, 0, 1, 0]` corresponde a una rotación de 180° alrededor de Y: el eje Z de la herramienta apunta hacia abajo. **Se recomienda enseñar (*teach*) los puntos con el FlexPendant** en lugar de escribir el `confdata` a mano, y luego derivar el resto con `Offs` o `RelTool`.

---

## 4. Sistemas de coordenadas, herramientas y objetos de trabajo

### 4.1 Sistemas de referencia

| Sistema | Descripción |
|---|---|
| **World** | Referencia global de la celda. En una instalación de un solo robot suele coincidir con **Base**. |
| **Base** | Origen en la base del robot. |
| **Work object (`wobjdata`)** | Marco ligado a la pieza o a la mesa. Los `robtarget` se expresan respecto a él. |
| **Tool (`tooldata`)** | Marco ligado a la herramienta; su origen es el **TCP**. |

Programar los puntos dentro de un `wobjdata` permite **reubicar toda una trayectoria** cambiando solo el marco del objeto de trabajo.

### 4.2 Definición de una herramienta

```rapid
!                       robhold  [ TCP [mm]  , orientación ]   [ masa[kg], cog[mm], aom, Ix, Iy, Iz ]
PERS tooldata tMarcador := [TRUE, [[0, 0, 150], [1, 0, 0, 0]], [0.3, [0, 0, 60], [1, 0, 0, 0], 0, 0, 0]];
```

- `robhold = TRUE`: la herramienta la sostiene el robot.
- La **masa debe ser mayor que 0**.
- El TCP se puede medir con el método de 4 puntos en el FlexPendant (*Movimiento → Herramienta → Definir*).

### 4.3 Definición de un objeto de trabajo

```rapid
!                        robhold ufprog ufmec  uframe (marco del usuario)          oframe (marco del objeto)
PERS wobjdata wMesa := [FALSE, TRUE, "", [[400, -200, 100], [1, 0, 0, 0]], [[0, 0, 0], [1, 0, 0, 0]]];
```

El `uframe` se mide con el método de 3 puntos (origen, punto sobre X, punto sobre Y) en el FlexPendant.

---

## 5. Instrucciones de movimiento

### 5.1 Resumen

| Instrucción | Interpolación | Destino | Uso |
|---|---|---|---|
| `MoveAbsJ` | Articular | `jointtarget` | Ir a ángulos absolutos (home, posiciones seguras). |
| `MoveJ` | Articular | `robtarget` | Desplazamientos rápidos donde la trayectoria del TCP no importa. |
| `MoveL` | Lineal | `robtarget` | TCP en línea recta (dibujo, inserción, soldadura). |
| `MoveC` | Circular | 2 × `robtarget` | Arco por un punto intermedio hasta un punto final. |
| `MoveJDO` / `MoveLDO` / `MoveCDO` | J / L / C | `robtarget` | Movimiento + activación de una salida digital en el punto. |
| `MoveJSync` / `MoveLSync` / `MoveCSync` | J / L / C | `robtarget` | Movimiento + llamada a un procedimiento en el punto. |
| `SearchL` / `SearchC` | L / C | `robtarget` | Movimiento que se detiene o registra la posición al cambiar una señal. |
| `TriggL` / `TriggJ` / `TriggC` | L / J / C | `robtarget` | Eventos (E/S) a una distancia o tiempo definidos sobre la trayectoria. |

### 5.2 Sintaxis general

```rapid
MoveL ToPoint [\ID] , Speed [\V] | [\T] , Zone [\Z] [\Inpos] , Tool [\WObj] [\Corr];
```

| Argumento | Descripción |
|---|---|
| `ToPoint` | Punto de destino (`robtarget`). |
| `Speed` | `speeddata` (`v100`) o personalizado. |
| `\V:=` | Sobrescribe la velocidad del TCP (mm/s). |
| `\T:=` | Define el tiempo total del movimiento (s). |
| `Zone` | `fine` = parada exacta; `zN` = paso suave con radio N mm. |
| `Tool` | `tooldata` activa. |
| `\WObj:=` | Objeto de trabajo (por defecto `wobj0`). |
| `\Conc` | Ejecuta las instrucciones siguientes mientras el robot se mueve. |

### 5.3 Ejemplos

```rapid
MoveAbsJ jHome, v200, fine, tool0;                       ! Ángulos absolutos
MoveJ pA, v500, z50, tMarcador \WObj:=wMesa;             ! Articular hacia pA
MoveL Offs(pA, 0, 0, -50), v50, fine, tMarcador \WObj:=wMesa;  ! Baja 50 mm en línea recta
MoveL pB, v100 \V:=75, z1, tMarcador \WObj:=wMesa;       ! Velocidad TCP = 75 mm/s
MoveL pC, v100 \T:=3, fine, tMarcador \WObj:=wMesa;      ! Llega en 3 s
MoveC pMedio, pFin, v100, z10, tMarcador \WObj:=wMesa;   ! Arco por pMedio hasta pFin
MoveLDO pD, v100, fine, tMarcador, DO_01, 1;             ! Activa DO_01 al llegar a pD
```

### 5.4 Ajustes globales del movimiento

| Instrucción | Efecto |
|---|---|
| `VelSet 50, 500;` | Escala todas las velocidades programadas al 50 % y limita el TCP a 500 mm/s. |
| `AccSet 50, 100;` | Reduce la aceleración al 50 % (rampa al 100 %). Suaviza movimientos. |
| `ConfJ \Off;` / `ConfL \Off;` | Desactiva el control de configuración del brazo (usar con cuidado). |
| `SingArea \Wrist;` | Permite al controlador variar la orientación para atravesar singularidades de muñeca. |
| `SingArea \Off;` | Comportamiento por defecto. |
| `WaitRob \InPos;` | Espera a que el robot se detenga en posición. |
| `StopMove;` / `StartMove;` | Detiene / reanuda el movimiento (útil en rutinas TRAP). |

---

## 6. Movimiento articular: control de los ángulos de cada eje

### 6.1 Definir y alcanzar ángulos

```rapid
VAR jointtarget jObjetivo := [[0, 0, 0, 0, 30, 0], [9E9,9E9,9E9,9E9,9E9,9E9]];

PROC IrAAngulos()
    jObjetivo.robax.rax_1 := 45;      ! Eje 1 a 45°
    jObjetivo.robax.rax_2 := 10;      ! Eje 2 a 10°
    jObjetivo.robax.rax_3 := -20;     ! Eje 3 a -20°
    MoveAbsJ jObjetivo, v200, fine, tool0;
ENDPROC
```

### 6.2 Leer la posición articular actual

```rapid
VAR jointtarget jActual;

jActual := CJointT();
TPWrite "Eje 1 [deg]: " \Num:=jActual.robax.rax_1;
TPWrite "Eje 5 [deg]: " \Num:=jActual.robax.rax_5;
```

### 6.3 Barrido de una articulación con contador

Mueve cada eje de forma independiente alrededor del *home*, sin salir de un margen seguro.

```rapid
PROC BarridoEje(num eje, num amplitud, num paso)
    VAR jointtarget j;
    VAR num ang;

    j := jHome;
    FOR k FROM 0 TO Trunc(2 * amplitud / paso) DO
        ang := -amplitud + k * paso;
        TEST eje
        CASE 1: j.robax.rax_1 := jHome.robax.rax_1 + ang;
        CASE 2: j.robax.rax_2 := jHome.robax.rax_2 + ang;
        CASE 3: j.robax.rax_3 := jHome.robax.rax_3 + ang;
        CASE 4: j.robax.rax_4 := jHome.robax.rax_4 + ang;
        CASE 5: j.robax.rax_5 := jHome.robax.rax_5 + ang;
        CASE 6: j.robax.rax_6 := jHome.robax.rax_6 + ang;
        ENDTEST
        MoveAbsJ j, v100, z5, tool0;
    ENDFOR
    MoveAbsJ jHome, v100, fine, tool0;
ENDPROC

PROC main()
    MoveAbsJ jHome, v200, fine, tool0;
    FOR e FROM 1 TO 6 DO
        BarridoEje e, 20, 5;       ! ±20° en pasos de 5°
    ENDFOR
ENDPROC
```

### 6.4 Validar ángulos antes de mover

```rapid
FUNC bool DentroDeLimites(jointtarget j)
    ! Límites de referencia (ajustar a los configurados en el controlador)
    IF Abs(j.robax.rax_1) > 180 RETURN FALSE;
    IF j.robax.rax_2 < -90 OR j.robax.rax_2 > 110 RETURN FALSE;
    IF j.robax.rax_3 < -230 OR j.robax.rax_3 > 50 RETURN FALSE;
    IF Abs(j.robax.rax_4) > 200 RETURN FALSE;
    IF Abs(j.robax.rax_5) > 120 RETURN FALSE;
    IF Abs(j.robax.rax_6) > 400 RETURN FALSE;
    RETURN TRUE;
ENDFUNC
```

### 6.5 Conversión entre espacio articular y cartesiano

| Función | Descripción |
|---|---|
| `CalcJointT(robtarget, tool \WObj)` | Cinemática inversa: ángulos para alcanzar un `robtarget`. |
| `CalcRobT(jointtarget, tool \WObj)` | Cinemática directa: `robtarget` a partir de ángulos. |

```rapid
VAR jointtarget jCalc;
VAR robtarget pCalc;

jCalc := CalcJointT(pA, tMarcador \WObj:=wMesa);
pCalc := CalcRobT(jCalc, tMarcador \WObj:=wMesa);
```

---

## 7. Funciones de posición y transformación

| Función / instrucción | Descripción | Ejemplo |
|---|---|---|
| `Offs(p, dx, dy, dz)` | Desplaza un punto en el marco del objeto de trabajo. | `Offs(pA, 100, 0, 0)` |
| `RelTool(p, dx, dy, dz \Rx \Ry \Rz)` | Desplaza/rota en el marco de la herramienta. | `RelTool(pA, 0, 0, 20 \Rz:=45)` |
| `CRobT(\Tool \WObj)` | Posición cartesiana actual (`robtarget`). | `pAct := CRobT(\Tool:=tMarcador \WObj:=wMesa);` |
| `CPos(\Tool \WObj)` | Posición actual (`pos`) sin orientación. | `posAct := CPos();` |
| `CJointT()` | Ángulos articulares actuales. | `jAct := CJointT();` |
| `OrientZYX(z, y, x)` | Construye un cuaternión desde ángulos de Euler ZYX [°]. | `pA.rot := OrientZYX(0, 180, 0);` |
| `EulerZYX(\X|\Y|\Z, orient)` | Extrae un ángulo de Euler de un cuaternión. | `rz := EulerZYX(\Z, pA.rot);` |
| `NOrient(orient)` | Normaliza un cuaternión. | `q := NOrient(q);` |
| `PoseMult(p1, p2)` | Composición de marcos. | `T := PoseMult(T1, T2);` |
| `PoseInv(p)` | Inversa de un marco. | `Ti := PoseInv(T);` |
| `PoseVect(p, pos)` | Transforma un vector por un marco. | `v2 := PoseVect(T, v1);` |
| `Distance(p1, p2)` | Distancia entre dos `pos` [mm]. | `d := Distance(pA.trans, pB.trans);` |
| `PDispSet pose` / `PDispOn` / `PDispOff` | Desplazamiento de programa: traslada/rota todos los puntos siguientes. | Ver ejemplo 8.6 |

---

## 8. Construcción de trayectorias (ejemplos)

> En todos los ejemplos, `pCentro` es un punto enseñado sobre la superficie de trabajo con el eje Z de la herramienta hacia abajo. Las dimensiones son ilustrativas: compruebe el alcance en RobotStudio.

```rapid
PERS robtarget pCentro := [[0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 0], [9E9,9E9,9E9,9E9,9E9,9E9]];
CONST num zSeg := 50;   ! Altura de aproximación [mm]
```

### 8.1 Cuadrado con `Offs`

```rapid
PROC Cuadrado(num lado)
    MoveJ Offs(pCentro, 0, 0, zSeg), v300, z10, tMarcador \WObj:=wMesa;
    MoveL pCentro, v50, fine, tMarcador \WObj:=wMesa;
    MoveL Offs(pCentro, lado, 0, 0),    v100, z1, tMarcador \WObj:=wMesa;
    MoveL Offs(pCentro, lado, lado, 0), v100, z1, tMarcador \WObj:=wMesa;
    MoveL Offs(pCentro, 0, lado, 0),    v100, z1, tMarcador \WObj:=wMesa;
    MoveL pCentro,                      v100, fine, tMarcador \WObj:=wMesa;
    MoveL Offs(pCentro, 0, 0, zSeg),    v100, z10, tMarcador \WObj:=wMesa;
ENDPROC
```

### 8.2 Círculo completo con `MoveC`

`MoveC` traza como máximo un arco; un círculo completo requiere dos (o más) instrucciones.

```rapid
PROC Circulo(num r)
    MoveJ Offs(pCentro, r, 0, zSeg), v300, z10, tMarcador \WObj:=wMesa;
    MoveL Offs(pCentro, r, 0, 0), v50, fine, tMarcador \WObj:=wMesa;
    MoveC Offs(pCentro, 0, r, 0),  Offs(pCentro, -r, 0, 0), v100, z1, tMarcador \WObj:=wMesa;
    MoveC Offs(pCentro, 0, -r, 0), Offs(pCentro,  r, 0, 0), v100, fine, tMarcador \WObj:=wMesa;
    MoveL Offs(pCentro, r, 0, zSeg), v100, z10, tMarcador \WObj:=wMesa;
ENDPROC
```

### 8.3 Trayectorias paramétricas con contadores (`FOR` + `Sin`/`Cos`)

Las funciones trigonométricas de RAPID trabajan en **grados**.

```rapid
! Polígono regular de n lados (n grande ≈ círculo)
PROC Poligono(num r, num n)
    VAR num ang;
    MoveJ Offs(pCentro, r, 0, zSeg), v300, z10, tMarcador \WObj:=wMesa;
    FOR i FROM 0 TO n DO
        ang := i * 360 / n;
        MoveL Offs(pCentro, r * Cos(ang), r * Sin(ang), 0), v100, z1, tMarcador \WObj:=wMesa;
    ENDFOR
    MoveL Offs(pCentro, r, 0, zSeg), v100, z10, tMarcador \WObj:=wMesa;
ENDPROC

! Espiral de Arquímedes
PROC Espiral(num vueltas, num paso)
    VAR num ang;
    VAR num r;
    MoveJ Offs(pCentro, 0, 0, zSeg), v300, z10, tMarcador \WObj:=wMesa;
    MoveL pCentro, v50, fine, tMarcador \WObj:=wMesa;
    FOR i FROM 0 TO vueltas * 36 DO
        ang := i * 10;                     ! 10° por iteración
        r := paso * ang / 360;             ! El radio crece 'paso' mm por vuelta
        MoveL Offs(pCentro, r * Cos(ang), r * Sin(ang), 0), v80, z1, tMarcador \WObj:=wMesa;
    ENDFOR
    MoveL Offs(CRobT(\Tool:=tMarcador \WObj:=wMesa), 0, 0, zSeg), v100, fine, tMarcador \WObj:=wMesa;
ENDPROC

! Hélice (variación en Z)
PROC Helice(num r, num vueltas, num avanceZ)
    VAR num ang;
    FOR i FROM 0 TO vueltas * 36 DO
        ang := i * 10;
        MoveL Offs(pCentro, r * Cos(ang), r * Sin(ang), zSeg + avanceZ * ang / 360), v100, z1, tMarcador \WObj:=wMesa;
    ENDFOR
ENDPROC
```

### 8.4 Trayectoria definida por un arreglo de puntos

```rapid
CONST num nPts := 5;
CONST pos ruta{nPts} := [[0,0,0], [80,0,0], [80,60,0], [40,90,0], [0,60,0]];

PROC SeguirRuta()
    MoveJ Offs(pCentro, ruta{1}.x, ruta{1}.y, zSeg), v300, z10, tMarcador \WObj:=wMesa;
    FOR i FROM 1 TO Dim(ruta, 1) DO
        MoveL Offs(pCentro, ruta{i}.x, ruta{i}.y, ruta{i}.z), v100, z1, tMarcador \WObj:=wMesa;
    ENDFOR
    MoveL Offs(pCentro, ruta{1}.x, ruta{1}.y, 0), v100, fine, tMarcador \WObj:=wMesa;   ! Cierra la figura
    MoveL Offs(pCentro, ruta{1}.x, ruta{1}.y, zSeg), v100, z10, tMarcador \WObj:=wMesa;
ENDPROC
```

### 8.5 Paletizado con contadores de filas y columnas

```rapid
PROC Paletizar(num filas, num cols, num dx, num dy)
    VAR num pieza := 0;
    FOR f FROM 0 TO filas - 1 DO
        FOR c FROM 0 TO cols - 1 DO
            Incr pieza;
            MoveJ Offs(pCentro, c * dx, f * dy, zSeg), v500, z20, tMarcador \WObj:=wMesa;
            MoveL Offs(pCentro, c * dx, f * dy, 0), v100, fine, tMarcador \WObj:=wMesa;
            ! Aquí: SetDO / Reset de la pinza
            WaitTime 0.3;
            MoveL Offs(pCentro, c * dx, f * dy, zSeg), v200, z20, tMarcador \WObj:=wMesa;
            TPWrite "Pieza: " \Num:=pieza;
        ENDFOR
    ENDFOR
ENDPROC
```

### 8.6 Reutilizar una figura en otra posición (`PDispSet`) o en otro objeto de trabajo

```rapid
PROC FiguraDesplazada()
    VAR pose desp := [[150, 0, 0], [1, 0, 0, 0]];   ! Trasladar 150 mm en X
    PDispSet desp;
    Cuadrado 50;
    PDispOff;
ENDPROC
```

Alternativa recomendada: definir un segundo `wobjdata` (por ejemplo un plano inclinado) y ejecutar la misma rutina con `\WObj:=wPlanoInclinado`.

### 8.7 Variación de orientación sobre un punto (`RelTool`)

```rapid
PROC Inclinaciones()
    FOR k FROM -2 TO 2 DO
        MoveL RelTool(pCentro, 0, 0, -zSeg \Rx:=k * 10), v50, fine, tMarcador \WObj:=wMesa;
    ENDFOR
    FOR k FROM 0 TO 8 DO
        MoveL RelTool(pCentro, 0, 0, -zSeg \Rz:=k * 45), v50, z1, tMarcador \WObj:=wMesa;
    ENDFOR
ENDPROC
```

---

## 9. Control de flujo

| Estructura | Sintaxis |
|---|---|
| Condicional | `IF cond THEN ... ELSEIF cond THEN ... ELSE ... ENDIF` |
| Condicional compacto | `IF cond instrucción;` |
| Bucle con contador | `FOR i FROM 1 TO 10 [STEP 2] DO ... ENDFOR` |
| Bucle condicional | `WHILE cond DO ... ENDWHILE` |
| Selección | `TEST var CASE 1: ... CASE 2, 3: ... DEFAULT: ... ENDTEST` |
| Salto | `GOTO etiqueta;` … `etiqueta:` |
| Retorno | `RETURN;` / `RETURN valor;` |
| Pausas | `WaitTime 1.5;` · `WaitUntil cond \MaxTime:=5;` |
| Detener | `Stop;` (pausa, se puede reanudar) · `EXIT;` (termina el programa) · `Break;` |

> La variable de un `FOR` se declara implícitamente y solo existe dentro del bucle.

**Menú de trayectorias seleccionable:**

```rapid
PROC main()
    VAR num opcion;
    WHILE TRUE DO
        TPReadFK opcion, "Seleccione trayectoria", "Cuadrado", "Circulo", "Espiral", "Home", "Salir";
        TEST opcion
        CASE 1: Cuadrado 60;
        CASE 2: Circulo 40;
        CASE 3: Espiral 3, 10;
        CASE 4: MoveAbsJ jHome, v200, fine, tool0;
        CASE 5: EXIT;
        ENDTEST
    ENDWHILE
ENDPROC
```

---

## 10. Variables, contadores, arreglos y matemáticas

### 10.1 Contadores

| Instrucción | Efecto |
|---|---|
| `Incr reg1;` | `reg1 := reg1 + 1` |
| `Decr reg1;` | `reg1 := reg1 - 1` |
| `Add reg1, 5;` | `reg1 := reg1 + 5` |
| `Clear reg1;` | `reg1 := 0` |

`reg1` … `reg5` son variables `num` predefinidas en el módulo de sistema `user.sys`.

### 10.2 Arreglos

```rapid
VAR num angulos{6};                     ! Arreglo de 6 elementos (índice desde 1)
VAR num matriz{3, 4};                   ! Matriz 3x4
VAR robtarget puntos{10};

angulos{1} := 45;
n := Dim(angulos, 1);                   ! Tamaño en la dimensión 1
```

### 10.3 Funciones matemáticas

| Función | Descripción |
|---|---|
| `Abs(x)`, `Sqrt(x)`, `Pow(b, e)`, `Exp(x)`, `Ln(x)` | Básicas |
| `Sin`, `Cos`, `Tan` | Trigonométricas (**grados**) |
| `ASin`, `ACos`, `ATan`, `ATan2(y, x)` | Inversas (resultado en grados) |
| `Round(x \Dec:=n)`, `Trunc(x \Dec:=n)` | Redondeo y truncamiento |
| `Max(a, b)`, `Min(a, b)` | Máximo y mínimo |
| `DOT(v1, v2)`, `CrossProd(v1, v2)`, `VectMagn(v)` | Operaciones vectoriales sobre `pos` |
| `a DIV b`, `a MOD b` | División entera y residuo |

### 10.4 Cadenas de texto

| Función | Descripción |
|---|---|
| `NumToStr(x, dec)` | Número → texto con `dec` decimales |
| `StrToVal(str, var)` | Texto → valor (retorna `bool`) |
| `ValToStr(dato)` | Cualquier dato → texto |
| `StrLen(str)`, `StrPart(str, ini, len)`, `StrFind(...)` | Manipulación |
| `+` | Concatenación: `"Eje: " + NumToStr(a, 2)` |

---

## 11. Entradas y salidas (E/S)

Las señales se definen en la configuración del sistema de E/S (`EIO.cfg`). Tipos: `signaldi`, `signaldo`, `signalai`, `signalao`, `signalgi`, `signalgo`.

| Instrucción / función | Descripción |
|---|---|
| `SetDO DO_01, 1;` | Escribe una salida digital. |
| `Set DO_01;` / `Reset DO_01;` | Pone a 1 / a 0. |
| `PulseDO \PLength:=0.5, DO_01;` | Pulso de 0,5 s. |
| `SetAO AO_01, 2.5;` | Salida analógica. |
| `SetGO GO_01, 7;` | Salida de grupo (entero sobre varios bits). |
| `DInput(DI_01)` / `DOutput(DO_01)` | Leer el valor de una señal. También se puede usar directamente: `IF DI_01 = 1 THEN`. |
| `AInput(AI_01)`, `GInput(GI_01)` | Lectura analógica / de grupo. |
| `WaitDI DI_01, 1 \MaxTime:=10;` | Espera a que una entrada tome un valor. |
| `WaitDO DO_01, 1;` | Espera sobre una salida. |

**Seleccionar trayectoria desde un PLC** (por ejemplo, mediante una salida de grupo del PLC conectada a `GI_Trayectoria`):

```rapid
PROC main()
    WHILE TRUE DO
        WaitDI DI_Start, 1;
        SetDO DO_Ocupado, 1;
        TEST GInput(GI_Trayectoria)
        CASE 1: Cuadrado 60;
        CASE 2: Circulo 40;
        DEFAULT: TPWrite "Codigo no valido";
        ENDTEST
        SetDO DO_Ocupado, 0;
        PulseDO \PLength:=0.5, DO_Terminado;
        WaitDI DI_Start, 0;
    ENDWHILE
ENDPROC
```

> Sustituya `DI_Start`, `GI_Trayectoria`, `DO_Ocupado` y `DO_Terminado` por las señales reales del laboratorio.

---

## 12. Interacción con el FlexPendant

| Instrucción | Descripción |
|---|---|
| `TPErase;` | Limpia la pantalla. |
| `TPWrite "Texto" [\Num:=] [\Bool:=] [\Pos:=] [\Orient:=];` | Escribe un mensaje con un dato. |
| `TPReadNum var, "Pregunta";` | Solicita un número al operador. |
| `TPReadFK var, "Texto", "F1", "F2", "F3", "F4", "F5";` | Menú de 5 teclas de función (`stEmpty` para vacías). Retorna 1–5. |
| `UIMsgBox`, `UINumEntry`, `UIListView` | Cuadros de diálogo más elaborados. |
| `ErrWrite "Titulo", "Detalle";` | Registra un mensaje en el registro de eventos. |

```rapid
PROC ParametrosOperador()
    VAR num lado;
    TPReadNum lado, "Lado del cuadrado [mm] (10-100):";
    IF lado < 10 OR lado > 100 THEN
        TPWrite "Valor fuera de rango";
        RETURN;
    ENDIF
    Cuadrado lado;
ENDPROC
```

---

## 13. Interrupciones y manejo de errores

### 13.1 Interrupciones (`TRAP`)

| Instrucción | Descripción |
|---|---|
| `CONNECT intnum WITH rutinaTrap;` | Asocia una interrupción a una rutina. |
| `ISignalDI DI_01, 1, intnum;` | Interrupción por flanco de una entrada digital. |
| `ITimer 1, intnum;` | Interrupción periódica cada 1 s (`\Single` = una sola vez). |
| `ISleep` / `IWatch` | Desactiva / reactiva temporalmente. |
| `IDelete intnum;` | Elimina la interrupción. |

```rapid
VAR intnum iParo;

PROC main()
    IDelete iParo;
    CONNECT iParo WITH trParo;
    ISignalDI DI_Pausa, 1, iParo;
    ! ... programa ...
ENDPROC

TRAP trParo
    StopMove;
    TPWrite "Pausa solicitada";
    WaitDI DI_Pausa, 0;
    StartMove;
ENDTRAP
```

### 13.2 Manejo de errores

Cada rutina puede tener un bloque `ERROR` que se ejecuta cuando ocurre un error recuperable. El código del error está en `ERRNO`.

```rapid
PROC LeerValor()
    VAR num x;
    x := 10 / reg1;
ERROR
    IF ERRNO = ERR_DIVZERO THEN
        reg1 := 1;
        RETRY;          ! Reintenta la instrucción que falló
    ENDIF
ENDPROC
```

| Instrucción | Acción |
|---|---|
| `RETRY` | Reintenta la instrucción que causó el error. |
| `TRYNEXT` | Continúa con la siguiente instrucción. |
| `RETURN` | Sale de la rutina. |
| `RAISE` | Propaga el error a la rutina llamadora. |

---

## 14. Monitoreo y seguimiento del robot

### 14.1 Mostrar ángulos y posición durante un recorrido

```rapid
PROC Reportar()
    VAR jointtarget j;
    VAR robtarget p;
    j := CJointT();
    p := CRobT(\Tool:=tMarcador \WObj:=wMesa);
    TPWrite "J1..J3: " + NumToStr(j.robax.rax_1, 1) + " / " + NumToStr(j.robax.rax_2, 1) + " / " + NumToStr(j.robax.rax_3, 1);
    TPWrite "J4..J6: " + NumToStr(j.robax.rax_4, 1) + " / " + NumToStr(j.robax.rax_5, 1) + " / " + NumToStr(j.robax.rax_6, 1);
    TPWrite "TCP [mm]: " \Pos:=p.trans;
ENDPROC
```

> Use `fine` (o `WaitRob \InPos`) antes de leer `CJointT`/`CRobT` si necesita el valor en el punto exacto; con zonas de aproximación, el controlador ejecuta instrucciones por adelantado.

### 14.2 Registro en archivo (*data logging*)

```rapid
VAR iodev log;
VAR clock reloj;

PROC IniciarLog()
    Open "HOME:" \File:="log_ejes.csv", log \Write;
    Write log, "t;J1;J2;J3;J4;J5;J6";
    ClkReset reloj;
    ClkStart reloj;
ENDPROC

PROC RegistrarMuestra()
    VAR jointtarget j;
    j := CJointT();
    Write log, NumToStr(ClkRead(reloj), 3) + ";" + NumToStr(j.robax.rax_1, 2) + ";" + NumToStr(j.robax.rax_2, 2) + ";"
             + NumToStr(j.robax.rax_3, 2) + ";" + NumToStr(j.robax.rax_4, 2) + ";" + NumToStr(j.robax.rax_5, 2) + ";"
             + NumToStr(j.robax.rax_6, 2);
ENDPROC

PROC CerrarLog()
    ClkStop reloj;
    Close log;
ENDPROC
```

El archivo queda en la carpeta `HOME` del controlador y se puede descargar con RobotStudio o por FTP.

### 14.3 Muestreo periódico con interrupción de tiempo

```rapid
VAR intnum iMuestreo;

PROC main()
    IniciarLog;
    CONNECT iMuestreo WITH trMuestreo;
    ITimer 0.2, iMuestreo;          ! Muestra cada 200 ms
    Espiral 3, 10;
    IDelete iMuestreo;
    CerrarLog;
ENDPROC

TRAP trMuestreo
    RegistrarMuestra;
ENDTRAP
```

### 14.4 Variables persistentes como interfaz de estado

Publicar el estado del programa en variables `PERS` permite leerlo desde fuera del controlador (sección 15):

```rapid
PERS num  nCiclos := 0;
PERS num  nPaso := 0;
PERS bool bEnMovimiento := FALSE;
PERS jointtarget jUltima := [[0,0,0,0,30,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
```

### 14.5 Tiempos de ciclo

```rapid
VAR clock cCiclo;
VAR num tCiclo;

ClkReset cCiclo;
ClkStart cCiclo;
Cuadrado 60;
ClkStop cCiclo;
tCiclo := ClkRead(cCiclo);
TPWrite "Tiempo de ciclo [s]: " \Num:=tCiclo;
```

---

## 15. Comunicación con sistemas SCADA

El robot puede integrarse a un SCADA por varias vías. **Cada una depende de las opciones instaladas en el controlador** (sección 0).

| Vía | Requisito | Qué permite | Herramientas del lado SCADA |
|---|---|---|---|
| **E/S digitales cableadas** | Tarjeta de E/S en el controlador | Arranque/paro, códigos de trayectoria, estados. | PLC (p. ej. Siemens S7) → SCADA |
| **Bus de campo** (PROFINET, EtherNet/IP, DeviceNet) | Opción de bus de campo en RobotWare | Intercambio de señales y grupos con un PLC. | PLC → SCADA |
| **Socket Messaging (TCP/IP)** | Opción *PC Interface* | Enviar y recibir cadenas o datos desde RAPID. | Python, Node-RED, LabVIEW |
| **Robot Web Services (RWS)** | RobotWare 6.x | API REST (HTTP) para leer/escribir variables RAPID, E/S, posición, estado. | Node-RED, Python, Ignition (REST) |
| **OPC (DA/UA)** | Servidor OPC de ABB instalado en un PC | Exposición de variables del robot como *tags* OPC. | Ignition, KEPServerEX, cualquier cliente OPC |
| **PC SDK** | Licencia/opción *PC Interface* | Aplicaciones .NET a la medida. | C# / VB.NET |

### 15.1 Servidor TCP en RAPID (Socket Messaging)

```rapid
VAR socketdev servidor;
VAR socketdev cliente;
VAR string recibido;
VAR jointtarget jSock;

PROC ServidorSocket()
    SocketCreate servidor;
    SocketBind servidor, "192.168.125.1", 1025;     ! IP del controlador (ajustar)
    SocketListen servidor;
    SocketAccept servidor, cliente \Time:=WAIT_MAX;

    WHILE TRUE DO
        SocketReceive cliente \Str:=recibido \Time:=WAIT_MAX;
        TEST recibido
        CASE "CUADRADO": Cuadrado 60;
        CASE "CIRCULO":  Circulo 40;
        CASE "HOME":     MoveAbsJ jHome, v200, fine, tool0;
        CASE "JOINTS":   ! Responder con los ángulos actuales
            jSock := CJointT();
            SocketSend cliente \Str:=ValToStr(jSock.robax);
        DEFAULT:
            SocketSend cliente \Str:="ERR";
        ENDTEST
        IF recibido <> "JOINTS" SocketSend cliente \Str:="OK";
    ENDWHILE
ERROR
    IF ERRNO = ERR_SOCK_CLOSED THEN
        SocketClose cliente;
        SocketClose servidor;
        RETURN;
    ENDIF
ENDPROC
```

> `192.168.125.1` es la dirección del puerto de servicio del IRC5. Para la red del laboratorio, use la IP del puerto WAN configurado.

### 15.2 Lectura con Robot Web Services (RobotWare 6)

Ejemplos de recursos REST (autenticación *digest*; el usuario por defecto es `Default User`, verifique la configuración del laboratorio):

| Dato | Petición |
|---|---|
| Ángulos articulares | `GET http://<ip>/rw/motionsystem/mechunits/ROB_1/jointtarget?json=1` |
| Posición cartesiana | `GET http://<ip>/rw/motionsystem/mechunits/ROB_1/robtarget?json=1` |
| Variable RAPID | `GET http://<ip>/rw/rapid/symbol/data/RAPID/T_ROB1/<Modulo>/nCiclos?json=1` |
| Estado de ejecución | `GET http://<ip>/rw/rapid/execution?json=1` |
| Señal de E/S | `GET http://<ip>/rw/iosystem/signals/<nombre_señal>?json=1` |

Con esto, un flujo de **Node-RED** (nodo *http request* periódico) o un script de Python puede alimentar un tablero SCADA con los ángulos de cada eje, el contador de ciclos y el estado del programa en tiempo real.

---

## 16. Flujo de trabajo en el laboratorio

1. **Simular en RobotStudio**: crear una estación con el IRB140 y un controlador virtual con la misma versión de RobotWare que el real.
2. **Escribir y verificar el módulo** (`RAPID → Comprobar programa`).
3. **Enseñar puntos de referencia** en el robot real (centro de la mesa, objeto de trabajo, herramienta).
4. **Cargar el módulo** al controlador (RobotStudio *Online* o memoria USB).
5. **Ejecutar en modo manual**: velocidad reducida (el controlador limita el TCP a 250 mm/s), paso a paso, con el dispositivo de habilitación.
6. **Ejecutar en modo automático** solo con la celda despejada y la autorización del responsable.
7. **Respaldar**: guardar el módulo y los datos (`tooldata`, `wobjdata`) en este repositorio.

**Estructura sugerida del repositorio:**

```
.
├── README.md
├── rapid/
│   ├── 01_movimientos_basicos.mod
│   ├── 02_articulaciones.mod
│   ├── 03_trayectorias.mod
│   ├── 04_es_plc.mod
│   ├── 05_monitoreo.mod
│   └── 06_socket_scada.mod
├── robotstudio/          # Estación (.rspag) y respaldos del controlador
├── scada/                # Flujos de Node-RED, scripts de Python, proyecto SCADA
└── docs/                 # Imágenes, diagramas de la celda, guías de práctica
```

---

## 17. Errores comunes y buenas prácticas

| Problema | Causa probable | Solución |
|---|---|---|
| *Position outside reach* | Punto fuera del volumen de trabajo. | Verificar con `CalcJointT` o en RobotStudio. |
| *Joint out of range* | Una articulación excede su límite. | Cambiar la orientación o el `confdata`; validar con la función de la sección 6.4. |
| Error de configuración (*axis configuration*) | El `confdata` no coincide con el camino real. | Reenseñar el punto; como último recurso `ConfL \Off`. |
| Singularidad de muñeca | Ejes 4 y 6 alineados (eje 5 ≈ 0°). | Evitar orientaciones con eje 5 cercano a 0°; `SingArea \Wrist`. |
| Lectura de posición "adelantada" | Ejecución anticipada con zonas `zN`. | Usar `fine` o `WaitRob \InPos` antes de leer. |
| Trayectoria desplazada | `tooldata` o `wobjdata` incorrectos. | Redefinir el TCP y el objeto de trabajo. |

**Buenas prácticas**

- Siempre especificar `tool` y `\WObj` explícitamente en cada movimiento.
- Usar `fine` en puntos donde se lee una señal, se actúa una herramienta o se toma una medida.
- Usar una altura de aproximación (`zSeg`) antes de bajar a la superficie.
- Empezar con velocidades bajas (`v50`–`v100`) y `VelSet` reducido en las primeras pruebas.
- Nombrar puntos y variables de forma descriptiva (`pCentroMesa`, `nCiclos`, `jHome`).
- Comentar cada rutina: qué hace, unidades y marco de referencia.

---

## 18. Referencias

- ABB. *Technical reference manual — RAPID Instructions, Functions and Data types* (RobotWare 6).
- ABB. *Technical reference manual — RAPID overview* (RobotWare 6).
- ABB. *Operating manual — IRC5 with FlexPendant*.
- ABB. *Application manual — Controller software IRC5* (Socket Messaging, multitarea y demás opciones).
- ABB. *Product specification — IRB 140*.
- ABB. *IRB 140 — Data sheet*: <https://library.e.abb.com/public/0ab091987347463cb06a3cc653d8ddb8/IRB_140_20211001.pdf>
- ABB RobotStudio Developer Center. *Building IRB140 Model* (límites articulares del modelo): <https://developercenter.robotstudio.com/api/robotstudio/articles/How-To/RobotMechanism/BuildthemodeloftheIRB140.html>
- ABB Developer Center. *Robot Web Services — RobotWare 6*: <https://developercenter.robotstudio.com/>

---

*Universidad Nacional de Colombia — Sede Bogotá · Curso Comunicaciones Industriales SCADA · Laboratorio de Robótica*
