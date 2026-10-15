MODULE ModSCADA
    !***********************************************************
    ! Interfaz SCADA para el Laboratorio 1 (decoración de torta)
    ! IRB 140 · IRC5 · RobotWare 6
    !
    ! Las variables PERS de este módulo son las que se agregan al
    ! servidor OPC UA (ABB IoT Gateway) y luego a Ignition, Node-RED
    ! o al puente MQTT (scada/opcua_mqtt_bridge.py).
    !
    ! Depende de rapid/lab01_decoracion/Module1.mod (Marcador,
    ! SINGBREAK, CHANGETOOL, Homming, ANICOLAS ... DKYMA,
    ! señales DI_01, DI_02, DO_02 y Conveyor_FWD).
    !***********************************************************

    ! ---------- RAPID -> SCADA (el SCADA solo lee) ----------
    PERS num scJ1:=0;
    PERS num scJ2:=0;
    PERS num scJ3:=0;
    PERS num scJ4:=0;
    PERS num scJ5:=0;
    PERS num scJ6:=0;
    PERS num scX:=0;               ! TCP del marcador en la base [mm]
    PERS num scY:=0;
    PERS num scZ:=0;
    PERS num scEstado:=0;          ! 0 espera · 1 decorando · 2 mantenimiento · 3 home · 9 orden inválida
    PERS num scRutina:=0;          ! 1 NICOLAS · 2 CAMILO · 3 GABRIEL · 4 KYMA
    PERS num scCiclos:=0;          ! tortas decoradas

    ! ---------- SCADA -> RAPID (el SCADA escribe) ----------
    PERS num scCmd:=0;             ! 0 nada · 1 decorar · 2 mantenimiento · 3 home · 4 reiniciar contador
    PERS num scRepeticiones:=1;

    VAR intnum iPublicar;

    !-----------------------------------------------------------
    ! Llamar una vez al inicio de main
    !-----------------------------------------------------------
    PROC IniciarSCADA()
        scEstado:=0;
        scRutina:=0;
        scCmd:=0;
        IDelete iPublicar;
        CONNECT iPublicar WITH trPublicar;
        ITimer 0.2,iPublicar;      ! publica ángulos y TCP cada 200 ms, también durante los movimientos
    ENDPROC

    !-----------------------------------------------------------
    ! Llamar en cada vuelta del WHILE de main
    !-----------------------------------------------------------
    PROC AtenderSCADA()
        VAR num orden;
        orden:=scCmd;
        IF orden=0 RETURN;
        scCmd:=0;                  ! acuse: el SCADA ve que la orden fue tomada
        TEST orden
        CASE 1:
            IF scRepeticiones<1 scRepeticiones:=1;
            FOR k FROM 1 TO scRepeticiones DO
                Decorar;
            ENDFOR
        CASE 2:
            Mantenimiento;
        CASE 3:
            scEstado:=3;
            Homming;
            scEstado:=0;
        CASE 4:
            scCiclos:=0;
        DEFAULT:
            scEstado:=9;
        ENDTEST
    ENDPROC

    !-----------------------------------------------------------
    ! Secuencia del laboratorio, con estado publicado
    !-----------------------------------------------------------
    PROC Decorar()
        scEstado:=1;
        TPWrite "ENCIENDE BANDA TRANSPORTADORA";
        Set Conveyor_FWD;
        WaitTime 3;
        Reset Conveyor_FWD;
        TPWrite "INICIANDO DECORADO";
        Set DO_02;
        MoveAbsJ SINGBREAK,v500,z1,Marcador;
        scRutina:=1;
        ANICOLAS;
        scRutina:=2;
        BCAMILO;
        scRutina:=3;
        CGABRIEL;
        scRutina:=4;
        DKYMA;
        scRutina:=0;
        Homming;
        Incr scCiclos;
        TPWrite "DECORADO FINALIZADO";
        WaitTime 3;
        Set Conveyor_FWD;
        WaitTime 5;
        Reset Conveyor_FWD;
        scEstado:=0;
    ENDPROC

    PROC Mantenimiento()
        ! El SCADA puede llevar el robot a la pose de cambio de herramienta,
        ! pero reanudar exige los dos botones físicos del panel (operador presente).
        scEstado:=2;
        Homming;
        MoveAbsJ CHANGETOOL,v500,z5,Marcador;
        Reset DO_02;
        TPWrite "PRESIONE LOS DOS BOTONES PARA CONTINUAR";
        WaitDI DI_01,1;
        WaitDI DI_02,1;
        WaitTime 5;
        MoveAbsJ HOME0,v500,fine,Marcador;
        scEstado:=0;
    ENDPROC

    !-----------------------------------------------------------
    ! Publicación periódica (se ejecuta aunque el robot se mueva)
    !-----------------------------------------------------------
    TRAP trPublicar
        VAR jointtarget j;
        VAR robtarget p;
        j:=CJointT();
        p:=CRobT(\Tool:=Marcador\WObj:=wobj0);
        scJ1:=Round(j.robax.rax_1\Dec:=2);
        scJ2:=Round(j.robax.rax_2\Dec:=2);
        scJ3:=Round(j.robax.rax_3\Dec:=2);
        scJ4:=Round(j.robax.rax_4\Dec:=2);
        scJ5:=Round(j.robax.rax_5\Dec:=2);
        scJ6:=Round(j.robax.rax_6\Dec:=2);
        scX:=Round(p.trans.x\Dec:=1);
        scY:=Round(p.trans.y\Dec:=1);
        scZ:=Round(p.trans.z\Dec:=1);
    ENDTRAP

    !-----------------------------------------------------------
    ! main de referencia: reemplaza el main de Module1.mod
    ! (cambie el nombre a "main" y comente el original)
    !-----------------------------------------------------------
    PROC mainSCADA()
        TPErase;
        TPWrite "INICIO PROGRAMA (con SCADA)";
        Reset Conveyor_FWD;
        Reset DO_02;
        IniciarSCADA;
        WHILE TRUE DO
            AtenderSCADA;
            IF DI_01=1 AND DI_02=0 THEN
                Decorar;
            ELSEIF DI_01=0 AND DI_02=1 THEN
                Mantenimiento;
            ELSEIF DI_01=1 AND DI_02=1 THEN
                TPWrite "NO DEBE PRESIONAR AMBAS ENTRADAS AL TIEMPO";
            ENDIF
            WaitTime 0.2;
        ENDWHILE
    ENDPROC
ENDMODULE
