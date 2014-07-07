CREATE OR REPLACE FUNCTION recalculate_agregacion_edc_py_v1(campana_id int, cantidad_intentos int) RETURNS INT AS $$
    #
    # Return values
    #       0: RECALCULO OK
    #      -1: ERROR DE LOCK
    #
    from plpy import spiexceptions
    import collections
    import pprint

    DEBUG = False

    if DEBUG:
        def dump_result(result, query_name):
            plpy.info("> ----- RESULT FOR QUERY: {0}".format(query_name))
            if len(result) > 0:
                line = ",".join([
                    str(col_name) for col_name in result[0]
                ])
                plpy.info("> {0}".format(line))
            for row in result:
                line = ",".join([str(row[col_name]) for col_name in row])
                plpy.info("> {0}".format(line))
            plpy.info("> ----- ")
    else:
        def dump_result(result, query_name):
            pass

    plpy.notice("recalculate_agregacion_edc_py_v1(): INICIANDO...")

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Lock
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    sql_lock = """
    SELECT
        id
    FROM
        fts_web_agregaciondeeventodecontacto
    WHERE
        campana_id = $1 AND
        numero_intento = 1
    FOR UPDATE
        NOWAIT
    """
    plan_lock = plpy.prepare(sql_lock, ["int"])
    try:
        records_lock = plpy.execute(plan_lock, [campana_id])
    except spiexceptions.LockNotAvailable:
        plpy.warning("recalculate_agregacion_edc_py_v1(): No se pudo obtener lock "
            "para campana {0}".format(campana_id))
        return -1

    plpy.info("recalculate_agregacion_edc_py_v1(): LOCK obtenido - continuamos")

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # PREPARE: select para obtener nuevos datos
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    sql_nuevos_datos = """
    SELECT
        ev_agregados.dato
            as "numero_intento",

        MAX(ev_agregados.timestamp_ultimo_evento)
            as "timestamp_ultimo_evento",

        sum(CASE ev_agregados.evento WHEN  2 THEN ev_agregados.suma_de_eventos ELSE 0 END)
            as "cantidad_intentos",
        sum(CASE ev_agregados.evento WHEN 22 THEN ev_agregados.suma_de_eventos ELSE 0 END)
            as "cantidad_finalizados",

        sum(CASE ev_agregados.evento WHEN 50 THEN ev_agregados.suma_de_eventos ELSE 0 END)
            as "cantidad_opcion_0",
        sum(CASE ev_agregados.evento WHEN 51 THEN ev_agregados.suma_de_eventos ELSE 0 END)
            as "cantidad_opcion_1",
        sum(CASE ev_agregados.evento WHEN 52 THEN ev_agregados.suma_de_eventos ELSE 0 END)
            as "cantidad_opcion_2",
        sum(CASE ev_agregados.evento WHEN 53 THEN ev_agregados.suma_de_eventos ELSE 0 END)
            as "cantidad_opcion_3",
        sum(CASE ev_agregados.evento WHEN 54 THEN ev_agregados.suma_de_eventos ELSE 0 END)
            as "cantidad_opcion_4",
        sum(CASE ev_agregados.evento WHEN 55 THEN ev_agregados.suma_de_eventos ELSE 0 END)
            as "cantidad_opcion_5",
        sum(CASE ev_agregados.evento WHEN 56 THEN ev_agregados.suma_de_eventos ELSE 0 END)
            as "cantidad_opcion_6",
        sum(CASE ev_agregados.evento WHEN 57 THEN ev_agregados.suma_de_eventos ELSE 0 END)
            as "cantidad_opcion_7",
        sum(CASE ev_agregados.evento WHEN 58 THEN ev_agregados.suma_de_eventos ELSE 0 END)
            as "cantidad_opcion_8",
        sum(CASE ev_agregados.evento WHEN 59 THEN ev_agregados.suma_de_eventos ELSE 0 END)
            as "cantidad_opcion_9"
    FROM (
        SELECT
            dato,
            evento,
            count(*) as "suma_de_eventos",
            max(timestamp) as "timestamp_ultimo_evento"
        FROM fts_daemon_eventodecontacto
        WHERE
            campana_id = $1 AND
            dato = $2 AND
            (
                evento = 2 -- EVENTO_DAEMON_INICIA_INTENTO / intento de contacto
                OR evento = 22 -- EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO / contacto finalizado
                OR ( evento >= 50 AND evento <= 59) -- EVENTO_ASTERISK_OPCION_0 = 50
            )
        GROUP BY dato, evento

    ) AS ev_agregados
    GROUP BY ev_agregados.dato
    """

    plan_nuevos_datos = plpy.prepare(sql_nuevos_datos, ["int", "int"])

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # PREPARE: update de agregates
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    sql_update = """
    UPDATE fts_web_agregaciondeeventodecontacto
    SET
    (
        cantidad_intentos,
        cantidad_finalizados,
        cantidad_opcion_0,
        cantidad_opcion_1,
        cantidad_opcion_2,
        cantidad_opcion_3,
        cantidad_opcion_4,
        cantidad_opcion_5,
        cantidad_opcion_6,
        cantidad_opcion_7,
        cantidad_opcion_8,
        cantidad_opcion_9,
        timestamp_ultima_actualizacion,
        timestamp_ultimo_evento
    ) = (
        $1, -- cantidad_intentos
        $2, -- cantidad_finalizados
        $3, -- cantidad_opcion_0
        $4, -- cantidad_opcion_1
        $5, -- cantidad_opcion_2
        $6, -- cantidad_opcion_3
        $7, -- cantidad_opcion_4
        $8, -- cantidad_opcion_5
        $9, -- cantidad_opcion_6
        $10, -- cantidad_opcion_7
        $11, -- cantidad_opcion_8
        $12, -- cantidad_opcion_9
        NOW(), -- timestamp_ultima_actualizacion
        $13    -- timestamp_ultimo_evento
    )
    WHERE
        campana_id = $14 AND
        numero_intento = $15
    """

    plan_update = plpy.prepare(sql_update, [
    "int",
    "int",
    "int",
    "int",
    "int",
    "int",
    "int",
    "int",
    "int",
    "int",
    "int",
    "int",
    "timestamp with time zone",
    "int",
    "int"
    ])

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Buscamos datos para los 'numero_intento'
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    aedc_actualizados = 0

    for nro_intento in range(1, cantidad_intentos + 1):

        # Esta es una parte CLAVE y CRITICA del sistema. Al buscar los EDC,
        #  filtramos los que posean timestamp > al timestamp del ultimo evento
        #  que se tuvo en cuenta la ultima vez q'' se actualizo la AEDC.
        # Por lo tanto, para que esto siga funcionando, hay que actualizar AEDC
        #  con el timestamp del ultimo EDC tenido en cuenta.
        params_nuevos_datos = [
        campana_id,
        nro_intento,
        ]

        #
        # SELECT EDC
        #
        
        records_nuevos_datos = plpy.execute(plan_nuevos_datos, params_nuevos_datos)

        if len(records_nuevos_datos) != 1:
            plpy.notice("recalculate_agregacion_edc_py_v1(): NO se devolvieron datos para "
                "campana {0}, intento {1}".format(campana_id, nro_intento))
            continue

        dump_result(records_nuevos_datos, "Current aggregates")

        COLS = ["numero_intento", "cantidad_intentos", "cantidad_finalizados",
            "cantidad_opcion_0", "cantidad_opcion_1", "cantidad_opcion_2", "cantidad_opcion_3",
            "cantidad_opcion_4", "cantidad_opcion_5", "cantidad_opcion_6", "cantidad_opcion_7",
            "cantidad_opcion_8", "cantidad_opcion_9",
            "timestamp_ultimo_evento"]

        datos_de_edc = {}
        for col_name in COLS:
            datos_de_edc[col_name] = records_nuevos_datos[0][col_name]

        if DEBUG:
            plpy.info("recalculate_agregacion_edc_py_v1(): datos_de_edc[{0}]: {1}".format(
                nro_intento, pprint.pformat(dict(datos_de_edc))))

        #
        # UPDATE AEDC
        #

        plpy.notice("recalculate_agregacion_edc_py_v1(): UPDATE AEDC - campana: {0} - nro_intento: {1}".format(
            campana_id, nro_intento))

        res_update = plpy.execute(plan_update, [
            int(datos_de_edc["cantidad_intentos"]),
            int(datos_de_edc["cantidad_finalizados"]),
            int(datos_de_edc["cantidad_opcion_0"]),
            int(datos_de_edc["cantidad_opcion_1"]),
            int(datos_de_edc["cantidad_opcion_2"]),
            int(datos_de_edc["cantidad_opcion_3"]),
            int(datos_de_edc["cantidad_opcion_4"]),
            int(datos_de_edc["cantidad_opcion_5"]),
            int(datos_de_edc["cantidad_opcion_6"]),
            int(datos_de_edc["cantidad_opcion_7"]),
            int(datos_de_edc["cantidad_opcion_8"]),
            int(datos_de_edc["cantidad_opcion_9"]),
            datos_de_edc["timestamp_ultimo_evento"],
            campana_id,
            nro_intento,
        ])

        # TODO: chequear resultado de UPDATE

        # fin de proceso de 1 intento

    return 0

$$ LANGUAGE plpythonu;
