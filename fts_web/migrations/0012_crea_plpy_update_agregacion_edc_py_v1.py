# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        pass

#        sql_OLD = """
#
#CREATE OR REPLACE FUNCTION update_agregacion_edc_py_v1(campana_id int) RETURNS INT AS $$
#    #
#    # Return values
#    #       0: NO SE ACTUALIZO NADA
#    #  n >= 1: SE ACTUALIZARON 'n' AEDC
#    #      -1: ERROR DE LOCK
#    #
#    from plpy import spiexceptions
#    import collections
#    import pprint
#
#    DEBUG = False
#
#    if DEBUG:
#        def dump_result(result, query_name):
#            plpy.info("> ----- RESULT FOR QUERY: {0}".format(query_name))
#            if len(result) > 0:
#                line = ",".join([
#                    str(col_name) for col_name in result[0]
#                ])
#                plpy.info("> {0}".format(line))
#            for row in result:
#                line = ",".join([str(row[col_name]) for col_name in row])
#                plpy.info("> {0}".format(line))
#            plpy.info("> ----- ")
#    else:
#        def dump_result(result, query_name):
#            pass
#
#    plpy.notice("update_agregacion_edc_py(): INICIANDO...")
#
#    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#    # Lock
#    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#    sql_lock = \"\"\"
#    SELECT
#        id
#    FROM
#        fts_web_agregaciondeeventodecontacto
#    WHERE
#        campana_id = $1 AND
#        numero_intento = 1
#    FOR UPDATE
#        NOWAIT
#    \"\"\"
#    plan_lock = plpy.prepare(sql_lock, ["int"])
#    try:
#        records_lock = plpy.execute(plan_lock, [campana_id])
#    except spiexceptions.LockNotAvailable:
#        plpy.warning("update_agregacion_edc_py(): No se pudo obtener lock "
#            "para campana {0}".format(campana_id))
#        return -1
#
#    plpy.info("update_agregacion_edc_py(): LOCK obtenido - continuamos")
#
#    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#    # fts_web_agregaciondeeventodecontacto
#    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#    sql_aedc = \"\"\"
#    SELECT
#        id,
#        numero_intento,
#        cantidad_intentos,
#        cantidad_finalizados,
#        cantidad_opcion_0,
#        cantidad_opcion_1,
#        cantidad_opcion_2,
#        cantidad_opcion_3,
#        cantidad_opcion_4,
#        cantidad_opcion_5,
#        cantidad_opcion_6,
#        cantidad_opcion_7,
#        cantidad_opcion_8,
#        cantidad_opcion_9,
#        timestamp_ultima_actualizacion,
#        timestamp_ultimo_evento,
#        tipo_agregacion
#    FROM
#        fts_web_agregaciondeeventodecontacto
#    WHERE
#        campana_id = $1
#    ORDER BY
#        numero_intento
#    \"\"\"
#    plan_aedc = plpy.prepare(sql_aedc, ["int"])
#    records_aedc = plpy.execute(plan_aedc, [campana_id])
#
#    dump_result(records_aedc, "Current aggregates")
#
#    if DEBUG:
#        plpy.info("update_agregacion_edc_py(): AEDC: {0} records".format(len(records_aedc)))
#
#    # ----- Guardamos resultado en dicts
#
#    COLS = ["id", "numero_intento", "cantidad_intentos", "cantidad_finalizados",
#        "cantidad_opcion_0", "cantidad_opcion_1", "cantidad_opcion_2", "cantidad_opcion_3",
#        "cantidad_opcion_4", "cantidad_opcion_5", "cantidad_opcion_6", "cantidad_opcion_7",
#        "cantidad_opcion_8", "cantidad_opcion_9", "timestamp_ultima_actualizacion",
#        "timestamp_ultimo_evento", "tipo_agregacion"]
#
#    aedc_x_nro_intento = collections.defaultdict(lambda: dict())
#    for row in records_aedc:
#        numero_intento = row["numero_intento"]
#        dict_intento = aedc_x_nro_intento[numero_intento]
#        for col_name in COLS:
#            dict_intento[col_name] = row[col_name]
#
#    if DEBUG:
#        plpy.info("update_agregacion_edc_py(): aedc_x_nro_intento: {0}".format(
#            pprint.pformat(dict(aedc_x_nro_intento))))
#
#    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#    # PREPARE: select para obtener nuevos datos
#    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#    
#    sql_nuevos_datos = \"\"\"
#    SELECT
#        ev_agregados.dato
#            as "numero_intento",
#
#        MAX(ev_agregados.timestamp_ultimo_evento)
#            as "timestamp_ultimo_evento",
#
#        sum(CASE ev_agregados.evento WHEN  2 THEN ev_agregados.suma_de_eventos ELSE 0 END)
#            as "cantidad_intentos",
#        sum(CASE ev_agregados.evento WHEN 22 THEN ev_agregados.suma_de_eventos ELSE 0 END)
#            as "cantidad_finalizados",
#
#        sum(CASE ev_agregados.evento WHEN 50 THEN ev_agregados.suma_de_eventos ELSE 0 END)
#            as "cantidad_opcion_0",
#        sum(CASE ev_agregados.evento WHEN 51 THEN ev_agregados.suma_de_eventos ELSE 0 END)
#            as "cantidad_opcion_1",
#        sum(CASE ev_agregados.evento WHEN 52 THEN ev_agregados.suma_de_eventos ELSE 0 END)
#            as "cantidad_opcion_2",
#        sum(CASE ev_agregados.evento WHEN 53 THEN ev_agregados.suma_de_eventos ELSE 0 END)
#            as "cantidad_opcion_3",
#        sum(CASE ev_agregados.evento WHEN 54 THEN ev_agregados.suma_de_eventos ELSE 0 END)
#            as "cantidad_opcion_4",
#        sum(CASE ev_agregados.evento WHEN 55 THEN ev_agregados.suma_de_eventos ELSE 0 END)
#            as "cantidad_opcion_5",
#        sum(CASE ev_agregados.evento WHEN 56 THEN ev_agregados.suma_de_eventos ELSE 0 END)
#            as "cantidad_opcion_6",
#        sum(CASE ev_agregados.evento WHEN 57 THEN ev_agregados.suma_de_eventos ELSE 0 END)
#            as "cantidad_opcion_7",
#        sum(CASE ev_agregados.evento WHEN 58 THEN ev_agregados.suma_de_eventos ELSE 0 END)
#            as "cantidad_opcion_8",
#        sum(CASE ev_agregados.evento WHEN 59 THEN ev_agregados.suma_de_eventos ELSE 0 END)
#            as "cantidad_opcion_9"
#    FROM (
#        SELECT
#            dato,
#            evento,
#            count(*) as "suma_de_eventos",
#            max(timestamp) as "timestamp_ultimo_evento"
#        FROM fts_daemon_eventodecontacto
#        WHERE
#            campana_id = $1 AND
#            dato = $2 AND
#            timestamp > $3 AND
#            timestamp < NOW() - interval '2 second' AND
#            (
#                evento = 2 -- EVENTO_DAEMON_INICIA_INTENTO / intento de contacto
#                OR evento = 22 -- EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO / contacto finalizado
#                OR ( evento >= 50 AND evento <= 59) -- EVENTO_ASTERISK_OPCION_0 = 50
#            )
#        GROUP BY dato, evento
#
#    ) AS ev_agregados
#    GROUP BY ev_agregados.dato
#    \"\"\"
#
#    plan_nuevos_datos = plpy.prepare(sql_nuevos_datos, ["int", "int", "timestamp with time zone"])
#
#    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#    # PREPARE: update de agregates
#    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#    sql_update = \"\"\"
#    UPDATE fts_web_agregaciondeeventodecontacto
#    SET
#    (
#        cantidad_intentos,
#        cantidad_finalizados,
#        cantidad_opcion_0,
#        cantidad_opcion_1,
#        cantidad_opcion_2,
#        cantidad_opcion_3,
#        cantidad_opcion_4,
#        cantidad_opcion_5,
#        cantidad_opcion_6,
#        cantidad_opcion_7,
#        cantidad_opcion_8,
#        cantidad_opcion_9,
#        timestamp_ultima_actualizacion,
#        timestamp_ultimo_evento
#    ) = (
#        cantidad_intentos    + $1, -- cantidad_intentos
#        cantidad_finalizados + $2, -- cantidad_finalizados
#        cantidad_opcion_0 +  $3, -- cantidad_opcion_0
#        cantidad_opcion_1 +  $4, -- cantidad_opcion_1
#        cantidad_opcion_2 +  $5, -- cantidad_opcion_2
#        cantidad_opcion_3 +  $6, -- cantidad_opcion_3
#        cantidad_opcion_4 +  $7, -- cantidad_opcion_4
#        cantidad_opcion_5 +  $8, -- cantidad_opcion_5
#        cantidad_opcion_6 +  $9, -- cantidad_opcion_6
#        cantidad_opcion_7 + $10, -- cantidad_opcion_7
#        cantidad_opcion_8 + $11, -- cantidad_opcion_8
#        cantidad_opcion_9 + $12, -- cantidad_opcion_9
#        NOW(), -- timestamp_ultima_actualizacion
#        $13    -- timestamp_ultimo_evento
#    )
#    WHERE
#        campana_id = $14 AND
#        numero_intento = $15
#    \"\"\"
#
#    plan_update = plpy.prepare(sql_update, [
#    "int",
#    "int",
#    "int",
#    "int",
#    "int",
#    "int",
#    "int",
#    "int",
#    "int",
#    "int",
#    "int",
#    "int",
#    "timestamp with time zone",
#    "int",
#    "int"
#    ])
#
#    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#    # Buscamos datos para los 'numero_intento'
#    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#    aedc_actualizados = 0
#
#    for nro_intento, aedc in aedc_x_nro_intento.iteritems():
#
#        # Esta es una parte CLAVE y CRITICA del sistema. Al buscar los EDC,
#        #  filtramos los que posean timestamp > al timestamp del ultimo evento
#        #  que se tuvo en cuenta la ultima vez q' se actualizo la AEDC.
#        # Por lo tanto, para que esto siga funcionando, hay que actualizar AEDC
#        #  con el timestamp del ultimo EDC tenido en cuenta.
#        params_nuevos_datos = [
#        campana_id,
#        nro_intento,
#        aedc['timestamp_ultimo_evento']
#        ]
#
#        #
#        # SELECT EDC
#        #
#        
#        records_nuevos_datos = plpy.execute(plan_nuevos_datos, params_nuevos_datos)
#
#        if len(records_nuevos_datos) != 1:
#            plpy.notice("update_agregacion_edc_py(): NO se devolvieron datos para "
#                "campana {0}, intento {1}".format(campana_id, nro_intento))
#            continue
#
#        dump_result(records_nuevos_datos, "Current aggregates")
#
#        COLS = ["numero_intento", "cantidad_intentos", "cantidad_finalizados",
#            "cantidad_opcion_0", "cantidad_opcion_1", "cantidad_opcion_2", "cantidad_opcion_3",
#            "cantidad_opcion_4", "cantidad_opcion_5", "cantidad_opcion_6", "cantidad_opcion_7",
#            "cantidad_opcion_8", "cantidad_opcion_9",
#            "timestamp_ultimo_evento"]
#
#        # 'nuevos_datos_por_numero_intento' YA NO SE USA
#        datos_de_edc = {}
#        for col_name in COLS:
#            datos_de_edc[col_name] = records_nuevos_datos[0][col_name]
#
#        if DEBUG:
#            plpy.info("update_agregacion_edc_py(): datos_de_edc[{0}]: {1}".format(
#                nro_intento, pprint.pformat(dict(datos_de_edc))))
#
#        #
#        # UPDATE AEDC
#        #
#
#        suma_eventos = sum([
#            int(datos_de_edc["cantidad_intentos"]),
#            int(datos_de_edc["cantidad_finalizados"]),
#            int(datos_de_edc["cantidad_opcion_0"]),
#            int(datos_de_edc["cantidad_opcion_1"]),
#            int(datos_de_edc["cantidad_opcion_2"]),
#            int(datos_de_edc["cantidad_opcion_3"]),
#            int(datos_de_edc["cantidad_opcion_4"]),
#            int(datos_de_edc["cantidad_opcion_5"]),
#            int(datos_de_edc["cantidad_opcion_6"]),
#            int(datos_de_edc["cantidad_opcion_7"]),
#            int(datos_de_edc["cantidad_opcion_8"]),
#            int(datos_de_edc["cantidad_opcion_9"]),
#        ])
#
#        if suma_eventos == 0:
#            # evitamos 1 update!
#            plpy.notice("update_agregacion_edc_py(): *NO* se hara UPDATE AEDC porque no hay "
#                "nuevos eventos - campana: {0} - intento: {1}".format(
#                    campana_id, nro_intento))
#            continue
#
#        plpy.notice("update_agregacion_edc_py(): UPDATE AEDC - campana: {0} - nro_intento: {1}".format(
#            campana_id, nro_intento))
#
#        aedc_actualizados += 1
#
#        res_update = plpy.execute(plan_update, [
#            int(datos_de_edc["cantidad_intentos"]),
#            int(datos_de_edc["cantidad_finalizados"]),
#            int(datos_de_edc["cantidad_opcion_0"]),
#            int(datos_de_edc["cantidad_opcion_1"]),
#            int(datos_de_edc["cantidad_opcion_2"]),
#            int(datos_de_edc["cantidad_opcion_3"]),
#            int(datos_de_edc["cantidad_opcion_4"]),
#            int(datos_de_edc["cantidad_opcion_5"]),
#            int(datos_de_edc["cantidad_opcion_6"]),
#            int(datos_de_edc["cantidad_opcion_7"]),
#            int(datos_de_edc["cantidad_opcion_8"]),
#            int(datos_de_edc["cantidad_opcion_9"]),
#            datos_de_edc["timestamp_ultimo_evento"],
#            campana_id,
#            nro_intento,
#        ])
#
#        # TODO: chequear resultado de UPDATE
#
#        # fin de proceso de 1 intento
#
#    return aedc_actualizados
#
#$$ LANGUAGE plpythonu;
#
#        """

    def backwards(self, orm):
        pass
#        sql = """DROP FUNCTION IF EXISTS update_agregacion_edc_py_v1(integer)"""
#        db.execute(sql)

    models = {
        u'fts_web.actuacion': {
            'Meta': {'object_name': 'Actuacion'},
            'campana': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'actuaciones'", 'to': u"orm['fts_web.Campana']"}),
            'dia_semanal': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'hora_desde': ('django.db.models.fields.TimeField', [], {}),
            'hora_hasta': ('django.db.models.fields.TimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'fts_web.agentegrupoatencion': {
            'Meta': {'object_name': 'AgenteGrupoAtencion'},
            'grupo_atencion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'agentes'", 'to': u"orm['fts_web.GrupoAtencion']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numero_interno': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        u'fts_web.agregaciondeeventodecontacto': {
            'Meta': {'object_name': 'AgregacionDeEventoDeContacto'},
            'campana_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'cantidad_finalizados': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_intentos': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_0': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_1': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_2': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_3': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_4': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_5': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_6': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_7': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_8': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cantidad_opcion_9': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numero_intento': ('django.db.models.fields.IntegerField', [], {}),
            'timestamp_ultima_actualizacion': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'timestamp_ultimo_evento': ('django.db.models.fields.DateTimeField', [], {}),
            'tipo_agregacion': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        u'fts_web.basedatoscontacto': {
            'Meta': {'object_name': 'BaseDatosContacto'},
            'archivo_importacion': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'cantidad_contactos': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'columna_datos': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'columnas': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'fecha_alta': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'nombre_archivo_importacion': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'sin_definir': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'fts_web.calificacion': {
            'Meta': {'ordering': "[u'nombre']", 'object_name': 'Calificacion'},
            'campana': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'calificaciones'", 'to': u"orm['fts_web.Campana']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'fts_web.campana': {
            'Meta': {'object_name': 'Campana'},
            'audio_asterisk': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'audio_original': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'bd_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'campanas'", 'to': u"orm['fts_web.BaseDatosContacto']"}),
            'cantidad_canales': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'cantidad_intentos': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'estado': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'fecha_fin': ('django.db.models.fields.DateField', [], {}),
            'fecha_inicio': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'segundos_ring': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'fts_web.contacto': {
            'Meta': {'object_name': 'Contacto'},
            'bd_contacto': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'contactos'", 'to': u"orm['fts_web.BaseDatosContacto']"}),
            'datos': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'telefono': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'fts_web.grupoatencion': {
            'Meta': {'object_name': 'GrupoAtencion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'ring_strategy': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'timeout': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'fts_web.opcion': {
            'Meta': {'unique_together': "((u'digito', u'campana'), (u'accion', u'campana', u'grupo_atencion'), (u'accion', u'campana', u'calificacion'))", 'object_name': 'Opcion'},
            'accion': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'calificacion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['fts_web.Calificacion']", 'null': 'True', 'blank': 'True'}),
            'campana': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'opciones'", 'to': u"orm['fts_web.Campana']"}),
            'digito': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'grupo_atencion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['fts_web.GrupoAtencion']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['fts_web']