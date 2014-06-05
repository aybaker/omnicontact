CREATE OR REPLACE FUNCTION update_agregacion_edc_py_v1(campana_id int) RETURNS TIMESTAMP WITH TIME ZONE AS $$
    from plpy import spiexceptions
    import collections
    import pprint

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

    plpy.notice("update_agregacion_edc_py(): INICIANDO...")

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
        plpy.warning("update_agregacion_edc_py(): No se pudo obtener lock "
            "para campana {0}".format(campana_id))
        return None

    plpy.info("update_agregacion_edc_py(): LOCK obtenido - continuamos")

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # fts_web_agregaciondeeventodecontacto
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    sql_aedc = """
    SELECT
        id,
        numero_intento,
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
        timestamp_ultimo_evento,
        tipo_agregacion
    FROM
        fts_web_agregaciondeeventodecontacto
    WHERE
        campana_id = $1
    ORDER BY
        numero_intento
    """
    plan_aedc = plpy.prepare(sql_aedc, ["int"])
    records_aedc = plpy.execute(plan_aedc, [campana_id])

    dump_result(records_aedc, "Current aggregates")

    plpy.info("update_agregacion_edc_py(): AEDC: {0} records".format(len(records_aedc)))

    # ----- Guardamos resultado en dicts

    COLS = ["id", "numero_intento", "cantidad_intentos", "cantidad_finalizados",
        "cantidad_opcion_0", "cantidad_opcion_1", "cantidad_opcion_2", "cantidad_opcion_3",
        "cantidad_opcion_4", "cantidad_opcion_5", "cantidad_opcion_6", "cantidad_opcion_7",
        "cantidad_opcion_8", "cantidad_opcion_9", "timestamp_ultima_actualizacion",
        "timestamp_ultimo_evento", "tipo_agregacion"]

    agregacion_por_numero_intento = collections.defaultdict(lambda: dict())
    for row in records_aedc:
        numero_intento = row["numero_intento"]
        dict_intento = agregacion_por_numero_intento[numero_intento]
        for col_name in COLS:
            dict_intento[col_name] = row[col_name]

    plpy.info("update_agregacion_edc_py(): agregacion_por_numero_intento: {0}".format(
        pprint.pformat(dict(agregacion_por_numero_intento))))


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Buscamos datos de EDC
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
            (
                evento = 2 -- EVENTO_DAEMON_INICIA_INTENTO / intento de contacto
                OR evento = 22 -- EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO / contacto finalizado
                OR ( evento >= 50 AND evento <= 59) -- EVENTO_ASTERISK_OPCION_0 = 50
            )
        GROUP BY dato, evento

    ) AS ev_agregados
    GROUP BY ev_agregados.dato
    """

    plan_nuevos_datos = plpy.prepare(sql_nuevos_datos, ["int"])
    records_nuevos_datos = plpy.execute(plan_nuevos_datos, [campana_id])

    dump_result(records_nuevos_datos, "Current aggregates")

    COLS = ["numero_intento", "cantidad_intentos", "cantidad_finalizados",
        "cantidad_opcion_0", "cantidad_opcion_1", "cantidad_opcion_2", "cantidad_opcion_3",
        "cantidad_opcion_4", "cantidad_opcion_5", "cantidad_opcion_6", "cantidad_opcion_7",
        "cantidad_opcion_8", "cantidad_opcion_9",
        "timestamp_ultimo_evento"]

    nuevos_datos_por_numero_intento = collections.defaultdict(lambda: dict())
    for row in records_nuevos_datos:
        numero_intento = row["numero_intento"]
        dict_intento = nuevos_datos_por_numero_intento[numero_intento]
        for col_name in COLS:
            dict_intento[col_name] = row[col_name]

    plpy.info("update_agregacion_edc_py(): nuevos_datos_por_numero_intento: {0}".format(
        pprint.pformat(dict(nuevos_datos_por_numero_intento))))

    #
    # Creamos UPDATE
    #

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
        $13 -- timestamp_ultimo_evento
    )
    WHERE
        campana_id = $14 AND
        numero_intento = $15
    """

    try:
        pass
    except:
        plpy.warning("ERROR")
        return None

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

    for intento, dict_datos in nuevos_datos_por_numero_intento.iteritems():
        plpy.info("update_agregacion_edc_py(): Se UPDATEara campana {0} intento {1}".format(
            campana_id, intento))
        res_update = plpy.execute(plan_update, [
            int(dict_datos["cantidad_intentos"]),
            int(dict_datos["cantidad_finalizados"]),
            int(dict_datos["cantidad_opcion_0"]),
            int(dict_datos["cantidad_opcion_1"]),
            int(dict_datos["cantidad_opcion_2"]),
            int(dict_datos["cantidad_opcion_3"]),
            int(dict_datos["cantidad_opcion_4"]),
            int(dict_datos["cantidad_opcion_5"]),
            int(dict_datos["cantidad_opcion_6"]),
            int(dict_datos["cantidad_opcion_7"]),
            int(dict_datos["cantidad_opcion_8"]),
            int(dict_datos["cantidad_opcion_9"]),
            dict_datos["timestamp_ultimo_evento"],
            campana_id,
            intento,
        ])

    try:
        max_timestamp = max(row["timestamp_ultimo_evento"] for row in records_aedc)
        plpy.info("update_agregacion_edc_py(): RETURN: {0}".format(str(max_timestamp)))
        return max_timestamp
    except:
        plpy.warning("update_agregacion_edc_py(): ERROR")
        return None

$$ LANGUAGE plpythonu;
