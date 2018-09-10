# -*- coding: utf-8 -*-

"""
Modelos de la aplicación
"""

from __future__ import unicode_literals

import datetime
import logging
import os
import json

from django.conf import settings
from django.core.exceptions import ValidationError, SuspiciousOperation
from django.db import models, transaction, connection
from django.db.models import Sum
from django.utils.timezone import now
from fts_daemon.audio_conversor import ConversorDeAudioService
from fts_web.errors import (FtsRecicladoCampanaError,
                            FTSOptimisticLockingError)
from fts_web.utiles import upload_to, log_timing, ValidadorDeNombreDeCampoExtra


logger = logging.getLogger(__name__)


#==============================================================================
# Derivación Externa
#==============================================================================

class DerivacionExternaManager(models.Manager):
    """Manager para DerivacionExterna"""

    def get_queryset(self):
        return super(DerivacionExternaManager, self).\
            get_queryset().exclude(borrado=True)


class DerivacionExterna(models.Model):
    """
    Representa una Derivación Externa.
    """
    objects_default = models.Manager()
    # Por defecto django utiliza el primer manager instanciado. Se aplica al
    # admin de django, y no aplica las customizaciones del resto de los
    # managers que se creen.

    objects = DerivacionExternaManager()

    TIPO_DERIVACION_DIAL = 1
    """Derivacion a atraves de dial."""

    TIPO_DERIVACION_GOTO = 2
    """Derivacion a atraves de goto."""

    TIPO_DERIVACION_CHOICES = (
        (TIPO_DERIVACION_DIAL, 'DIAL'),
        (TIPO_DERIVACION_GOTO, 'GOTO'),
    )
    tipo_derivacion = models.PositiveIntegerField(
        choices=TIPO_DERIVACION_CHOICES,
        default=TIPO_DERIVACION_DIAL,
    )

    nombre = models.CharField(
        max_length=128,
    )
    dial_string = models.CharField(
        max_length=256,
    )
    borrado = models.BooleanField(
        default=False,
        editable=False,
    )

    def __unicode__(self):
        if self.borrado:
            return '(ELiminado) {0}'.format(self.nombre)
        return self.nombre

    def puede_borrarse(self):
        """Metodo que realiza los chequeos necesarios del modelo, y
        devuelve booleano indincando si se puede o no borrar.

        :returns: bool - True si la DerivacionExterna puede borrarse.
        """
        if Opcion.objects.filter(derivacion_externa=self).exclude(
            campana__estado=Campana.ESTADO_BORRADA).exclude(
            campana__estado=Campana.ESTADO_EN_DEFINICION).count():
            return False
        return True

    def borrar(self, *args, **kwargs):
        logger.info("Seteando derivacion externa %s como BORRADA", self.id)
        assert self.puede_borrarse()

        self.borrado = True
        self.save()


#==============================================================================
# Grupos de Atención
#==============================================================================

class GrupoAtencionManager(models.Manager):
    """Manager para GrupoAtencion"""

    def get_queryset(self):
        return super(GrupoAtencionManager, self).\
            get_queryset().exclude(borrado=True)

    def obtener_todos_para_generar_config(self):
        """Devuelve g.a. que deben ser tenidas en cuenta
        al generar el configuracoin de queues.
        """
        return self.all()


class GrupoAtencion(models.Model):
    """
    Representa un Grupo de Atencion, o sea, un conjunto de agentes
    a donde se puede derivar una llamada.

    Se sobreescribe el método `delete()` para implementar
    un borrado lógico.
    """

    objects_default = models.Manager()
    # Por defecto django utiliza el primer manager instanciado. Se aplica al
    # admin de django, y no aplica las customizaciones del resto de los
    # managers que se creen.

    objects = GrupoAtencionManager()

    RINGALL, RRMEMORY = range(0, 2)
    RING_STRATEGY_CHOICES = (
        (RINGALL, 'RINGALL'),
        (RRMEMORY, 'RRMEMORY'),
    )

    RING_STRATEGY_PARA_ASTERISK = dict([
        (RINGALL, 'ringall'),
        (RRMEMORY, 'rrmemory'),
    ])
    """Texto a usar en configuracion de Asterisk"""

    nombre = models.CharField(
        max_length=128,
    )
    timeout = models.PositiveIntegerField()
    ring_strategy = models.PositiveIntegerField(
        choices=RING_STRATEGY_CHOICES,
        default=RINGALL,
    )
    borrado = models.BooleanField(
        default=False,
        editable=False,
    )

    def __unicode__(self):
        if self.borrado:
            return '(ELiminado) {0}'.format(self.nombre)
        return self.nombre

    def puede_borrarse(self):
        """Metodo que realiza los chequeos necesarios del modelo, y
        devuelve booleano indincando si se puede o no borrar.

        :returns: bool - True si la GrupoAtencion puede borrarse.
        """
        if Opcion.objects.filter(grupo_atencion=self).exclude(
            campana__estado=Campana.ESTADO_BORRADA).exclude(
            campana__estado=Campana.ESTADO_EN_DEFINICION).count():
            return False
        return True

    def borrar(self, *args, **kwargs):
        logger.info("Seteando grupo atencion %s como BORRADA", self.id)
        assert self.puede_borrarse()

        self.borrado = True
        self.save()

    def get_cantidad_agentes(self):
        return self.agentes.all().count()

    def get_nombre_para_asterisk(self):
        """Devuelve un texto para ser usado en Asterisk,
        para identificar este grupo de atencion.
        """
        assert self.id
        return 'fts_grupo_atencion_{0}'.format(self.id)

    def get_ring_strategy_para_asterisk(self):
        """Devuelve un texto para ser usado en Asterisk,
        para identificar la ring_strategy seleccionada.
        """
        return GrupoAtencion.RING_STRATEGY_PARA_ASTERISK[self.ring_strategy]


class AgenteGrupoAtencion(models.Model):
    numero_interno = models.CharField(
        max_length=32,
    )
    grupo_atencion = models.ForeignKey(
        'GrupoAtencion',
        related_name='agentes'
    )
    #    active = models.BooleanField(
    #        default=True,
    #        editable=False,
    #    )

    def __unicode__(self):
        return '{0} >> {1}'.format(
            self.grupo_atencion, self.numero_interno)
        #    if self.active:
        #        return '{0} >> {1}'.format(
        #            self.grupo_atencion, self.numero_interno)
        #    return '(ELiminado) {0} >> {1}'.format(
        #            self.grupo_atencion, self.numero_interno)

    #    def delete(self, *args, **kwargs):
    #        if self.active:
    #            self.active = False
    #            self.save()


#==============================================================================
# Base Datos Contactos
#==============================================================================

class BaseDatosContactoManager(models.Manager):
    """Manager para BaseDatosContacto"""

    def obtener_definidas(self):
        """
        Este método filtra lo objetos BaseDatosContacto que
        esté definidos.
        """
        return self.filter(estado=BaseDatosContacto.ESTADO_DEFINIDA)

    def obtener_en_definicion_para_editar(self, base_datos_contacto_id):
        """Devuelve la base datos pasada por ID, siempre que pueda ser editada.
        En caso de no encontarse, lanza SuspiciousOperation
        """
        try:
            return self.filter(
                estado=BaseDatosContacto.ESTADO_EN_DEFINICION).get(
                pk=base_datos_contacto_id)
        except BaseDatosContacto.DoesNotExist:
            raise(SuspiciousOperation("No se encontro base datos en "
                                      "estado ESTADO_EN_DEFINICION"))

    def obtener_definida_para_depurar(self, base_datos_contacto_id):
        """Devuelve la base datos pasada por ID, siempre que pueda ser
        depurada.
        En caso de no encontarse, lanza SuspiciousOperation
        """
        try:
            return self.filter(
                estado=BaseDatosContacto.ESTADO_DEFINIDA).get(
                pk=base_datos_contacto_id)
        except BaseDatosContacto.DoesNotExist:
            raise(SuspiciousOperation("No se encontro base datos en "
                                      "estado ESTADO_EN_DEFINICION"))


upload_to_archivos_importacion = upload_to("archivos_importacion", 95)


class MetadataBaseDatosContactoDTO(object):
    """Encapsula acceso a metadatos de BaseDatosContacto"""

    def __init__(self):
        self._metadata = {}

    # -----

    @property
    def cantidad_de_columnas(self):
        try:
            return self._metadata['cant_col']
        except KeyError:
            raise(ValueError("La cantidad de columnas no ha sido seteada"))

    @cantidad_de_columnas.setter
    def cantidad_de_columnas(self, cant):
        assert isinstance(cant, int), ("'cantidad_de_columnas' "
        "debe ser int. Se encontro: {0}".format(type(cant)))

        assert cant > 0, ("'cantidad_de_columnas' "
                          "debe ser > 0. Se especifico {0}".format(cant))

        self._metadata['cant_col'] = cant

    # -----

    @property
    def columna_con_telefono(self):
        try:
            return self._metadata['col_telefono']
        except KeyError:
            raise(ValueError("No se ha seteado 'columna_con_telefono'"))

    @columna_con_telefono.setter
    def columna_con_telefono(self, columna):
        columna = int(columna)
        assert columna < self.cantidad_de_columnas, ("No se puede setear "
            "'columna_con_telefono' = {0} porque  la BD solo "
            "posee {1} columnas"
            "".format(columna, self.cantidad_de_columnas))
        self._metadata['col_telefono'] = columna

    # -----

    @property
    def columnas_con_fecha(self):
        try:
            return self._metadata['cols_fecha']
        except KeyError:
            return []

    @columnas_con_fecha.setter
    def columnas_con_fecha(self, columnas):
        """
        Parametros:
        - columnas: Lista de enteros que indican las columnas con fechas.
        """
        assert isinstance(columnas, (list, tuple)), ("'columnas_con_fecha' "
            "recibe listas o tuplas. Se recibio: {0}".format(type(columnas)))
        for col in columnas:
            assert isinstance(col, int), ("Los elementos de "
            "'columnas_con_fecha' deben ser int. Se encontro: {0}".format(
                type(col)))
            assert col < self.cantidad_de_columnas, ("No se puede setear "
                "'columnas_con_fecha' = {0} porque  la BD solo "
                "posee {1} columnas"
                "".format(col, self.cantidad_de_columnas))

        self._metadata['cols_fecha'] = columnas

    # -----

    @property
    def columnas_con_hora(self):
        try:
            return self._metadata['cols_hora']
        except KeyError:
            return []

    @columnas_con_hora.setter
    def columnas_con_hora(self, columnas):
        """
        Parametros:
        - columnas: Lista de enteros que indican las columnas con horas.
        """
        assert isinstance(columnas, (list, tuple)), ("'columnas_con_hora' "
            "recibe listas o tuplas. Se recibio: {0}".format(type(columnas)))
        for col in columnas:
            assert isinstance(col, int), ("Los elementos de "
            "'columnas_con_hora' deben ser int. Se encontro: {0}".format(
                type(col)))
            assert col < self.cantidad_de_columnas, ("No se puede setear "
                "'columnas_con_hora' = {0} porque  la BD solo "
                "posee {1} columnas"
                "".format(col, self.cantidad_de_columnas))

        self._metadata['cols_hora'] = columnas

    # -----

    @property
    def nombres_de_columnas(self):
        try:
            return self._metadata['nombres_de_columnas']
        except KeyError:
            return []

    @nombres_de_columnas.setter
    def nombres_de_columnas(self, columnas):
        """
        Parametros:
        - columnas: Lista de strings con nombres de las
                    columnas.
        """
        assert isinstance(columnas, (list, tuple)), ("'nombres_de_columnas' "
            "recibe listas o tuplas. Se recibio: {0}".format(type(columnas)))
        assert len(columnas) == self.cantidad_de_columnas, ("Se intentaron "
            "setear {0} nombres de columnas, pero la BD posee {1} columnas"
            "".format(len(columnas), self.cantidad_de_columnas))

        self._metadata['nombres_de_columnas'] = columnas

    @property
    def primer_fila_es_encabezado(self):
        try:
            return self._metadata['prim_fila_enc']
        except KeyError:
            raise(ValueError("No se ha seteado si primer "
                             "fila es encabezado"))

    @primer_fila_es_encabezado.setter
    def primer_fila_es_encabezado(self, es_encabezado):
        assert isinstance(es_encabezado, bool)

        self._metadata['prim_fila_enc'] = es_encabezado

    def obtener_telefono_de_dato_de_contacto(self, datos_json):
        """Devuelve el numero telefonico del contacto.

        :param datos: atribuito 'datos' del contacto, o sea, valores de
                      las columnas codificadas con json
        """
        col_telefono = self._metadata['col_telefono']
        try:
            datos = json.loads(datos_json)
        except:
            logger.exception("Excepcion detectada al desserializar "
                             "datos extras. Datos extras: '{0}'"
                             "".format(datos_json))
            raise

        assert len(datos) == self.cantidad_de_columnas

        telefono = datos[col_telefono]
        return telefono

    def obtener_telefono_y_datos_extras(self, datos_json):
        """Devuelve tupla con (1) el numero telefonico del contacto,
        y (2) un dict con los datos extras del contacto

        :param datos: atribuito 'datos' del contacto, o sea, valores de
                      las columnas codificadas con json
        """
        # Decodificamos JSON
        try:
            datos = json.loads(datos_json)
        except:
            logger.exception("Excepcion detectada al desserializar "
                             "datos extras. Datos extras: '{0}'"
                             "".format(datos_json))
            raise

        assert len(datos) == self.cantidad_de_columnas

        # Obtenemos telefono
        telefono = datos[self.columna_con_telefono]

        # Obtenemos datos extra
        datos_extra = dict(zip(self.nombres_de_columnas,
                               datos))

        return telefono, datos_extra

    def validar_metadatos(self):
        """Valida que los datos de metadatos estan completos"""
        assert self.cantidad_de_columnas > 0, "cantidad_de_columnas es <= 0"
        assert self.columna_con_telefono >= 0, "columna_con_telefono < 0"
        assert self.columna_con_telefono < self.cantidad_de_columnas, \
            "columna_con_telefono >= cantidad_de_columnas"

        for index_columna in self.columnas_con_fecha:
            assert index_columna >= 0, "columnas_con_fecha: index_columna < 0"
            assert index_columna < self.cantidad_de_columnas, (""
                "columnas_con_fecha: "
                "index_columna >= cantidad_de_columnas")

        for index_columna in self.columnas_con_hora:
            assert index_columna >= 0, "columnas_con_hora: index_columna < 0"
            assert index_columna < self.cantidad_de_columnas, (""
                "columnas_con_hora: "
                "index_columna >= cantidad_de_columnas")

        assert len(self.nombres_de_columnas) == self.cantidad_de_columnas, \
            "len(nombres_de_columnas) != cantidad_de_columnas"

        validador = ValidadorDeNombreDeCampoExtra()
        for nombre_columna in self.nombres_de_columnas:
            assert validador.validar_nombre_de_columna(nombre_columna), \
                "El nombre del campo extra / columna no es valido"

        assert self.primer_fila_es_encabezado in (True, False), \
            "primer_fila_es_encabezado no es un booleano valido"

    def dato_extra_es_hora(self, nombre_de_columna):
        """
        Devuelve True si el dato extra correspondiente a la columna
        con nombre `nombre_de_columna` ha sido seteada con el
        tipo de dato `hora`.

        Este metodo no realiza ningun tipo de sanitizacion del nombre
        de columna recibido por parametro! Se supone que el nombre
        de columna es valido y existe.

        :raises ValueError: si la columna no existe
        """
        index = self.nombres_de_columnas.index(nombre_de_columna)
        return index in self.columnas_con_hora

    def dato_extra_es_fecha(self, nombre_de_columna):
        """
        Devuelve True si el dato extra correspondiente a la columna
        con nombre `nombre_de_columna` ha sido seteada con el
        tipo de dato `fecha`.

        Este metodo no realiza ningun tipo de sanitizacion del nombre
        de columna recibido por parametro! Se supone que el nombre
        de columna es valido y existe.

        :raises ValueError: si la columna no existe
        """
        index = self.nombres_de_columnas.index(nombre_de_columna)
        return index in self.columnas_con_fecha

    def dato_extra_es_telefono(self, nombre_de_columna):
        """
        Devuelve True si el dato extra correspondiente a la columna
        con numero telefonico.

        Este metodo no realiza ningun tipo de sanitizacion del nombre
        de columna recibido por parametro! Se supone que el nombre
        de columna es valido y existe.

        :raises ValueError: si la columna no existe
        """
        index = self.nombres_de_columnas.index(nombre_de_columna)
        return index == self.columna_con_telefono

    def dato_extra_es_generico(self, nombre_de_columna):
        """
        Devuelve True si el dato extra correspondiente a la columna
        con nombre `nombre_de_columna` es de tipo generico, o sea
        debe ser tratado como texto (ej: no es el nro de telefono,
        ni hora ni fecha)

        Este metodo no realiza ningun tipo de sanitizacion del nombre
        de columna recibido por parametro! Se supone que el nombre
        de columna es valido y existe.

        :raises ValueError: si la columna no existe
        """
        index = self.nombres_de_columnas.index(nombre_de_columna)
        return not (
                    index in self.columnas_con_hora
                    or
                    index in self.columnas_con_fecha
                    or
                    index == self.columna_con_telefono
                    )


class MetadataBaseDatosContacto(MetadataBaseDatosContactoDTO):
    """Encapsula acceso a metadatos de BaseDatosContacto"""

    def __init__(self, bd):
        super(MetadataBaseDatosContacto, self).__init__()
        self.bd = bd
        if bd.metadata is not None and bd.metadata != '':
            try:
                self._metadata = json.loads(bd.metadata)
            except:
                logger.exception("Excepcion detectada al desserializar "
                                 "metadata de la bd {0}".format(bd.id))
                raise

    # -----

    def save(self):
        """Guardar los metadatos en la instancia de BaseDatosContacto"""
        # Primero validamos
        self.validar_metadatos()

        # Ahora guardamos
        try:
            self.bd.metadata = json.dumps(self._metadata)
        except:
            logger.exception("Excepcion detectada al serializar "
                             "metadata de la bd {0}".format(self.bd.id))
            raise


class BaseDatosContacto(models.Model):
    objects = BaseDatosContactoManager()

    DATO_EXTRA_GENERICO = 'GENERICO'
    DATO_EXTRA_FECHA = 'FECHA'
    DATO_EXTRA_HORA = 'HORA'

    DATOS_EXTRAS = (
        (DATO_EXTRA_GENERICO, 'Dato Genérico'),
        (DATO_EXTRA_FECHA, 'Fecha'),
        (DATO_EXTRA_HORA, 'Hora'),
    )

    ESTADO_EN_DEFINICION = 0
    ESTADO_DEFINIDA = 1
    ESTADO_EN_DEPURACION = 2
    ESTADO_DEPURADA = 3
    ESTADOS = (
        (ESTADO_EN_DEFINICION, 'En Definición'),
        (ESTADO_DEFINIDA, 'Definida'),
        (ESTADO_EN_DEPURACION, 'En Depuracion'),
        (ESTADO_DEPURADA, 'Depurada')
    )

    nombre = models.CharField(
        max_length=128,
    )
    fecha_alta = models.DateTimeField(
        auto_now_add=True,
    )
    archivo_importacion = models.FileField(
        upload_to=upload_to_archivos_importacion,
        max_length=256,
    )
    nombre_archivo_importacion = models.CharField(
        max_length=256,
    )
    metadata = models.TextField(null=True, blank=True)
    sin_definir = models.BooleanField(
        default=True,
    )
    cantidad_contactos = models.PositiveIntegerField(
        default=0
    )
    estado = models.PositiveIntegerField(
        choices=ESTADOS,
        default=ESTADO_EN_DEFINICION,
    )

    def __unicode__(self):
        return "{0}: ({1} contactos)".format(self.nombre,
                                             self.cantidad_contactos)

    def get_metadata(self):
        return MetadataBaseDatosContacto(self)

    def genera_contactos(self, lista_datos_contacto):
        """
        Este metodo se encarga de realizar la generación de contactos
        a partir de una lista de tuplas de teléfonos.
        Parametros:
        - lista_datos_contacto: lista de tuplas con lo datos del contacto.
        """

        for datos_contacto in lista_datos_contacto:
            Contacto.objects.create(
                datos=datos_contacto[0],
                bd_contacto=self,
            )
        self.cantidad_contactos = len(lista_datos_contacto)

    def define(self):
        """
        Este método se encara de llevar a cabo la definición del
        objeto BaseDatosContacto. Establece el atributo sin_definir
        en False haciedo que quede disponible el objeto.
        """
        assert self.estado == BaseDatosContacto.ESTADO_EN_DEFINICION
        logger.info("Seteando base datos contacto %s como definida", self.id)
        self.sin_definir = False

        self.estado = self.ESTADO_DEFINIDA
        self.save()

    def get_cantidad_contactos(self):
        """
        Devuelve la cantidad de contactos de la BaseDatosContacto.
        """

        return self.cantidad_contactos

    def verifica_en_uso(self):
        """
        Este método se encarga de verificar si la base de datos esta siendo
        usada por alguna campaña que este activa o pausada.
        Devuelve  booleano.
        """
        estados_campanas = [campana.estado for campana in self.campanas.all()]
        if any(estado == Campana.ESTADO_ACTIVA for estado in estados_campanas):
            return True
        return False

    def verifica_depurada(self):
        """
        Este método se encarga de verificar si la base de datos esta siendo
        depurada o si ya fue depurada.
        Devuelve booleano.
        """
        if self.estado in (self.ESTADO_EN_DEPURACION, self.ESTADO_DEPURADA):
            return True
        return False

    def elimina_contactos(self):
        """
        Este método se encarga de eliminar todos los contactos de la
        BaseDatoContacto actual.
        El estado de la base de datos tiene que ser ESTADO_EN_DEFINICION o
        ESTADO_EN_DEPURACION, no se deberían eliminar los contactos con la
        misma en otro estado.
        """
        assert self.estado in (self.ESTADO_EN_DEFINICION,
                               self.ESTADO_EN_DEPURACION)
        self.contactos.all().delete()

    def procesa_depuracion(self):
        """
        Este método se encarga de llevar el proceso de depuración de
        BaseDatoContacto invocando a los métodos que realizan las distintas
        acciones.
        """

        if self.estado != BaseDatosContacto.ESTADO_DEFINIDA:
            raise(SuspiciousOperation("La BD {0} NO se puede depurar porque "
                                      "no esta en estado ESTADO_DEFINIDA. "
                                      "Estado: {1}".format(self.pk,
                                                           self.estado)))

        # 1) Cambio de estado BaseDatoContacto (ESTADO_EN_DEPURACION).
        logger.info("Iniciando el proceso de depurado de BaseDatoContacto:"
                    "Seteando base datos contacto %s como"
                    "ESTADO_EN_DEPURACION.", self.id)

        self.estado = self.ESTADO_EN_DEPURACION
        self.save()

        # 2) Llamada a método que hace el COPY / dump.
        Contacto.objects.realiza_dump_contactos(self)

        # 3) Llama el método que hace el borrado de los contactos.
        self.elimina_contactos()

        # 4) Cambio de estado BaseDatoContacto (ESTADO_DEPURADA).
        logger.info("Finalizando el proceso de depurado de "
                    "BaseDatoContacto: Seteando base datos contacto %s "
                    "como ESTADO_DEPURADA.", self.id)
        self.estado = self.ESTADO_DEPURADA
        self.save()

    def copia_para_reciclar(self):
        """
        Este método se encarga de duplicar la base de datos de contactos
        actual.
        NO realiza la copia de los contactos de la misma.
        """
        copia = BaseDatosContacto.objects.create(
            nombre='{0} (reciclada)'.format(self.nombre),
            archivo_importacion=self.archivo_importacion,
            nombre_archivo_importacion=self.nombre_archivo_importacion,
            metadata=self.metadata,
        )
        return copia


class ContactoManager(models.Manager):
    """Manager para Contacto"""

    def realiza_dump_contactos(self, bd_contacto):
        """
        Este método realiza el dump de los contactos de la base de datos a un
        archivo.
        """

        nombre_archivo_contactos = 'contacto_{0}'.format(bd_contacto.pk)
        copy_to = os.path.join(settings.FTS_BASE_DATO_CONTACTO_DUMP_PATH,
                               nombre_archivo_contactos)

        cursor = connection.cursor()
        sql = """COPY (SELECT * FROM fts_web_contacto WHERE
            bd_contacto_id = %s) TO %s;
        """

        params = [bd_contacto.id, copy_to]
        with log_timing(logger,
                        "ContactoManager.realiza_dump_contactos() tardo "
                        "%s seg"):
            cursor.execute(sql, params)


class ContactoPendiente(object):
    """Guarda informacion de un contacto pendiente de ser contactado"""

    def __init__(self, id_contacto, cantidad_intentos_realizados):
        self._id_contacto = id_contacto
        self._cantidad_intentos_realizados = cantidad_intentos_realizados

    @property
    def cantidad_intentos_realizados(self):
        return self._cantidad_intentos_realizados

    @property
    def id_contacto(self):
        return self._id_contacto


class Contacto(models.Model):
    objects = ContactoManager()

    datos = models.TextField()
    bd_contacto = models.ForeignKey(
        'BaseDatosContacto',
        related_name='contactos'
    )

    def obtener_telefono_y_datos_extras(self, metadata):
        """Devuelve lista con (telefono, datos_extras) utilizando
        la informacion de metadata pasada por parametro.

        Recibimos `metadata` por parametro por una cuestion de
        performance.
        """
        telefono, extras = metadata.obtener_telefono_y_datos_extras(self.datos)
        return (telefono, extras)

    def __unicode__(self):
        return '{0} >> {1}'.format(
            self.bd_contacto, self.datos)


#==============================================================================
# Campaña
#==============================================================================

class TemplateManager(models.Manager):
    """Manager para Campanas-->Template"""

    def obtener_activos(self):
        """Devuelve campañas-->templates en estado activas.
        """
        return self.filter(es_template=True,
                           estado=Campana.ESTADO_TEMPLATE_ACTIVO)

    def crea_campana_de_template(self, template):
        """
        Este método se encarga de crear una campana a partir del template
        proporcionado.
        """
        assert template.estado == Campana.ESTADO_TEMPLATE_ACTIVO
        assert template.es_template

        campana = Campana.objects.replicar_campana(template)
        return campana

    def obtener_en_definicion_para_editar(self, campana_id):
        """Devuelve la campaña pasada por ID, siempre que dicha
        campaña pueda ser editar (editada en el proceso de
        definirla, o sea, en el proceso de "creacion" de la
        campaña).

        En caso de no encontarse, lanza SuspiciousOperation
        """
        try:
            return self.filter(
                estado=Campana.ESTADO_TEMPLATE_EN_DEFINICION).get(
                pk=campana_id)
        except Campana.DoesNotExist:
            raise(SuspiciousOperation("No se encontro campana/template %s en "
                                      "estado ESTADO_TEMPLATE_EN_DEFINICION"))

    def obtener_activo_para_eliminar_crear_ver(self, campana_id):
        """Devuelve la campaña pasada por ID, siempre que dicha
        campaña pueda ser eliminada.

        En caso de no encontarse, lanza SuspiciousOperation
        """
        try:
            return self.filter(
                estado=Campana.ESTADO_TEMPLATE_ACTIVO).get(pk=campana_id)
        except Campana.DoesNotExist:
            raise(SuspiciousOperation("No se encontro campana/template %s en "
                                      "estado ESTADO_TEMPLATE_ACTIVO"))


class AbstractCampana(models.Model):
    """
    Modelo abstracto para las campana de audio y de sms.
    """

    nombre = models.CharField(max_length=128)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    bd_contacto = models.ForeignKey(
        'BaseDatosContacto',
        null=True, blank=True,
        related_name="%(class)ss"
    )

    class Meta:
        abstract = True

    def obtener_actuaciones_validas(self):
        """
        Este método devuelve un lista con las actuaciones válidas de una
        campaña. Teniendo como válidas aquellas que se van a ser procesadas
        teniendo en cuenta las fechas y horas que se le setearon.

        En caso de que las fecha_iniio y fecha_fin sean nulas, como ser en un
        template, devuelve una lista vacia.
        """
        hoy_ahora = datetime.datetime.today()
        hoy = hoy_ahora.date()
        ahora = hoy_ahora.time()

        lista_actuaciones = [actuacion.dia_semanal for actuacion in
                             self.actuaciones.all()]
        lista_actuaciones_validas = []

        dias_totales = (self.fecha_fin - self.fecha_inicio).days + 1
        for numero_dia in range(dias_totales):
            dia_actual = (self.fecha_inicio + datetime.timedelta(
                days=numero_dia))
            dia_semanal_actual = dia_actual.weekday()

            if dia_semanal_actual in lista_actuaciones:
                actuaciones_diaria = self.actuaciones.filter(
                    dia_semanal=dia_semanal_actual)
                for actuacion in actuaciones_diaria:
                    actuacion_valida = True
                    if dia_actual == hoy and ahora > actuacion.hora_hasta:
                        actuacion_valida = False

                    if actuacion_valida:
                        lista_actuaciones_validas.append(actuacion)
        return lista_actuaciones_validas

    def obtener_actuacion_actual(self):
        """
        Este método devuelve la actuación correspondiente al
        momento de hacer la llamada al método.
        Si no hay ninguna devuelve None.
        """
        hoy_ahora = datetime.datetime.today()
        assert hoy_ahora.tzinfo is None
        dia_semanal = hoy_ahora.weekday()
        hora_actual = hoy_ahora.time()

        # FIXME: PERFORMANCE: ver si el resultado de 'filter()' se cachea,
        # sino, usar algo que se cachee, ya que este metodo es ejecutado
        # muchas veces desde el daemon
        actuaciones_hoy = self.actuaciones.filter(dia_semanal=dia_semanal)
        if not actuaciones_hoy:
            return None

        for actuacion in actuaciones_hoy:
            if actuacion.hora_desde <= hora_actual <= actuacion.hora_hasta:
                return actuacion
        return None

    def verifica_fecha(self, hoy_ahora):
        """
        Este método se encarga de verificar si la fecha pasada como
        parametro en hoy_ahora es válida para la campaña actual.
        Devuelve True o False.
        """
        assert isinstance(hoy_ahora, datetime.datetime)

        fecha_actual = hoy_ahora.date()

        if self.fecha_inicio <= fecha_actual <= self.fecha_fin:
            return True
        return False

    def valida_actuaciones(self):
        """
        Este método verifica que la actuaciones de una campana, sean válidas.
        Corrobora que al menos uno de los días semanales del rango de fechas
        de la campana concuerde con algún dia de la actuación que tenga la
        campana al momento de ser consultado este método.
        Si la campaña tiene un solo día de ejecución o si tiene un solo día
        de actuación, y los días semanales coinciden y es hoy, valida que
        hora actual sea menor que la hora_hasta de la actuación.
        """
        valida = False
        hoy_ahora = datetime.datetime.today()
        hoy = hoy_ahora.date()
        ahora = hoy_ahora.time()

        fecha_inicio = self.fecha_inicio
        fecha_fin = self.fecha_fin

        lista_actuaciones = [actuacion.dia_semanal for actuacion in
                             self.actuaciones.all()]

        dias_totales = (self.fecha_fin - self.fecha_inicio).days + 1
        for numero_dia in range(dias_totales):
            dia_actual = (self.fecha_inicio + datetime.timedelta(
                days=numero_dia))
            dia_semanal_actual = dia_actual.weekday()

            if dia_semanal_actual in lista_actuaciones:
                valida = True
                actuaciones_diaria = self.actuaciones.filter(
                    dia_semanal=dia_semanal_actual)
                for actuacion in actuaciones_diaria:
                    if dia_actual == hoy and ahora > actuacion.hora_hasta:
                        valida = False
        return valida


class BaseCampanaYCampanaSmsManager(models.Manager):

    def obtener_en_definicion_para_editar(self, campana_id):
        """Devuelve la campaña pasada por ID, siempre que dicha
        campaña pueda ser editar (editada en el proceso de
        definirla, o sea, en el proceso de "creacion" de la
        campaña).

        En caso de no encontarse, lanza SuspiciousOperation
        """
        try:
            return self.filter(
                estado=self.model.ESTADO_EN_DEFINICION).get(
                pk=campana_id)
        except self.model.DoesNotExist:
            raise(SuspiciousOperation("No se encontro campana %s en "
                                      "estado ESTADO_EN_DEFINICION"))


class CampanaManager(BaseCampanaYCampanaSmsManager):
    """Manager para Campanas"""

    def get_queryset(self):
        return super(CampanaManager, self).get_queryset().\
            filter(es_template=False).\
            exclude(estado=Campana.ESTADO_BORRADA)

    def obtener_activas(self):
        """Devuelve campañas en estado activas.
        Puede suceder que este metodo devuelva campañas en estado activas,
        pero que en realidad deberian estar en estado FINALIZADAS porque,
        por ejemplo, la fecha actual es posterior a "fecha de fin", todavía
        no se actualizó el estado de dichas campañas en la BD.
        """
        return self.filter(estado=Campana.ESTADO_ACTIVA)

    def obtener_pausadas(self):
        """
        Devuelve campañas en estado pausadas.
        """
        return self.filter(estado=Campana.ESTADO_PAUSADA)

    def obtener_finalizadas(self):
        """Devuelve queryset para filtrar campañas en estado finalizadas."""
        return self.filter(estado=Campana.ESTADO_FINALIZADA)

    def obtener_depuradas(self):
        """Devuelve queryset para filtrar campañas en estado depuradas."""
        return self.filter(estado=Campana.ESTADO_DEPURADA)

    def obtener_activa_para_detalle_estado(self, campana_id):
        """Devuelve la campaña pasada por ID, siempre que dicha
        campaña este activa, procesándose, para ver su estado.

        En caso de no encontarse, lanza SuspiciousOperation.
        """
        try:
            return self.filter(estado=Campana.ESTADO_ACTIVA).get(
                pk=campana_id)
        except Campana.DoesNotExist:
            raise(SuspiciousOperation("No se encontro campana %s en "
                                      "estado ESTADO_ACTIVA"))

    def obtener_depurada_para_eliminar(self, campana_id):
        """Devuelve la campaña pasada por ID, siempre que dicha
        campaña pueda ser eliminada.

        En caso de no encontarse, lanza SuspiciousOperation
        """
        try:
            return self.filter(
                estado=Campana.ESTADO_DEPURADA).get(pk=campana_id)
        except Campana.DoesNotExist:
            raise(SuspiciousOperation("No se encontro campana en "
                                      "estado ESTADO_FINALIZADA"))

    def obtener_depurada_para_reciclar(self, campana_id):
        """Devuelve la campaña pasada por ID, siempre que dicha
        campaña pueda ser reciclada. Debe haber estar depuarada.

        En caso de no encontarse, lanza SuspiciousOperation
        """
        try:
            return self.filter(estado=Campana.ESTADO_DEPURADA).get(
                pk=campana_id)
        except Campana.DoesNotExist:
            raise(SuspiciousOperation("No se encontro campana en "
                                      "estado ESTADO_DEPURADA"))

    def obtener_para_detalle(self, campana_id):
        """Devuelve la campaña pasada por ID, siempre que a dicha
        campaña se le pueda ver el detalle, debe estar en estado activa,
        pausada, finalifada o depurada.

        En caso de no encontarse, lanza SuspiciousOperation
        """
        try:
            ESTADOS_VER_DETALLE = [Campana.ESTADO_ACTIVA,
                                   Campana.ESTADO_PAUSADA,
                                   Campana.ESTADO_FINALIZADA,
                                   Campana.ESTADO_DEPURADA]
            return self.filter(estado__in=ESTADOS_VER_DETALLE).get(
                pk=campana_id)
        except Campana.DoesNotExist:
            raise(SuspiciousOperation("No se encontro campana en "
                                      "estado ESTADO_ACTIVA, ESTADO_PAUSADA, "
                                      "ESTADO_FINALIZADA o ESTADO_DEPURADA"))

    def obtener_todas_para_generar_dialplan(self):
        """Devuelve campañas que deben ser tenidas en cuenta
        al generar el dialplan.
        """
        # TODO: renombrar a `obtener_todas_para_generar_config()`
        return self.filter(estado__in=[Campana.ESTADO_ACTIVA,
            Campana.ESTADO_PAUSADA, Campana.ESTADO_FINALIZADA])

    def obtener_ejecucion(self):
        """
        Devuelve las campanas que tengan actuación en el
        momento de realizar la consulta.
        """
        #Fecha y Hora local.
        hoy_ahora = datetime.datetime.today()
        dia_semanal = hoy_ahora.weekday()
        fecha_actual = hoy_ahora.date()
        hora_actual = hoy_ahora.time()

        campanas_hoy = self.obtener_activas().filter(
            fecha_inicio__lte=fecha_actual,
            fecha_fin__gte=fecha_actual)

        campanas_ejecucion = campanas_hoy.filter(
            actuaciones__dia_semanal=dia_semanal,
            actuaciones__hora_desde__lte=hora_actual,
            actuaciones__hora_hasta__gte=hora_actual)

        return campanas_ejecucion

    def verifica_estado_activa(self, campana_id):
        """Devuelve booleano indicando si el estado de la campaña
        es 'ACTIVA'
        :param campana_id: Id de la campaña
        :type pk: int
        :returns: bool -- si la campaña esta activa o no
        """
        return self.filter(pk=campana_id,
            estado=Campana.ESTADO_ACTIVA).exists()

    def obtener_vencidas_para_finalizar(self):
        """GENERADOR, devuelve las campañas que deberían ser finalizadas.
        SOLO verifica estado, fechas, actuaciones, etc., tomando
        los datos de la BD, pero NO tiene en cuenta si la
        campana posee llamadas en curso, etc.
        """
        # Aca necesitamos *localtime*. Usamos `now_ref` como fecha de
        # referencia para todos los calculos

        # FIXME: aunque necesitamos utilizar la hora local, esto hace
        # muy complicado crear un algoritmo respetable que funcione en
        # escenarios de cambios horarios!
        # El problema es que las actuaciones son basadas en hora (sin TZ),
        # por lo tanto, tecnicamente, si justo despues de las 23:59:59.999
        # se pasa a las 23:00:00.000 del mismo día, entonces algunas
        # Actuaciones podrían ser validas 2 veces!

        now_ref = datetime.datetime.now()

        # ¿Por que `ESTADO_PAUSADA`? Porque ya está vencida!
        # Otra alternativa sería dejarla pausada, y al des-pausarla
        # verificar si ya está vencida, y si está vencida, la
        # finalizamos...
        estados = [Campana.ESTADO_ACTIVA, Campana.ESTADO_PAUSADA]

        #
        # Primero finalizamos viejas, de ayer o anteriores
        #

        queryset = self.filter(
            fecha_fin__lt=now_ref.date(),
            estado__in=estados
        )

        # A las viejas, las finalizamos de una
        for campana in queryset:
            logger.info("obtener_vencidas_para_finalizar(): incluyendo "
                "campana %s xq su 'fecha_fin' es anterior a la fecha actual",
                campana.id)
            yield campana

        #
        # Si hay alguna q' finalice hoy, hay q' revisar las actuaciones
        #

        queryset = self.filter(
            fecha_fin=now_ref.date(),
            estado__in=estados
        )

        # # select_related() en 'reverse relationship'
        # # - era NO-OP en Django < 1.8
        # # - genera error en Django >= 1.8
        # queryset = queryset.select_related('actuaciones')

        for campana in queryset:
            actuaciones_para_hoy = [actuacion
                for actuacion in campana.actuaciones.all()
                if actuacion.dia_concuerda(now_ref.date())]

            # Si no tiene actuaciones para hoy, la finalizamos!
            if not actuaciones_para_hoy:
                logger.info("obtener_vencidas_para_finalizar(): incluyendo "
                    "campana %s xq su 'fecha_fin' es hoy, pero no posee "
                    "Actuacion para hoy", campana.id)
                yield campana
                continue

            # Si todas las actuaciones para hoy, tienen una
            # hora_fin menor a la actual, entonces podemos
            # finalizar la campaña
            son_anteriores = [act.es_anterior_a(now_ref.time())
                for act in actuaciones_para_hoy]
            if all(son_anteriores):
                # Todas las Actuaciones para hoy, poseen una
                # hora_desde / hora_hasta ANTERIOR a la actual
                # por lo tanto, podemos finalizar la campaña
                logger.info("obtener_vencidas_para_finalizar(): incluyendo "
                    "campana %s xq su 'fecha_fin' es hoy, posee Actuacion "
                    "pero todas son anteriores a hora actual", campana.id)
                yield campana
                continue

            # FIXME: falta devolver campañas que terminan en fechas
            # futuras, pero NO poseen actuaciones para dichas fechas

    def reciclar_campana(self, campana_id, bd_contacto):
        """
        Este método replica la campana pasada por parámetro con fin de
        reciclar la misma.
        """
        try:
            campana = self.get(pk=campana_id)
            assert campana.estado == Campana.ESTADO_DEPURADA

        except Campana.DoesNotExist:
            logger.warn("No se pudo recuperar la Campana: %s", campana_id)
            raise FtsRecicladoCampanaError("No se pudo recuperar la Campaña.")
        else:
            campana_reciclada = self.replicar_campana(campana)
            campana_reciclada.nombre = '{0} (reciclada)'.format(
                campana_reciclada.nombre)
            campana_reciclada.bd_contacto = bd_contacto
            campana_reciclada.save()

        return campana_reciclada

    def replicar_campana(self, campana):
        """
        Este método se encarga de replicar una campana existente, creando una
        campana nueva de iguales características.
        """
        assert isinstance(campana, Campana)

        # Replica Campana.
        campana_replicada = self.create(
            nombre=campana.nombre,
            cantidad_canales=campana.cantidad_canales,
            cantidad_intentos=campana.cantidad_intentos,
            segundos_ring=campana.segundos_ring,
            fecha_inicio=campana.fecha_inicio,
            fecha_fin=campana.fecha_fin,
            duracion_de_audio=campana.duracion_de_audio,
            bd_contacto=campana.bd_contacto,
        )

        # Replica Opciones y Calificaciones.
        opciones = campana.opciones.all()
        for opcion in opciones:
            calificacion_replicada = None
            if opcion.calificacion:
                calificacion_replicada = Calificacion.objects.create(
                    nombre=opcion.calificacion.nombre,
                    campana=campana_replicada,
                )

            Opcion.objects.create(
                digito=opcion.digito,
                accion=opcion.accion,
                grupo_atencion=opcion.grupo_atencion,
                derivacion_externa=opcion.derivacion_externa,
                calificacion=calificacion_replicada,
                campana=campana_replicada,
            )

        # Replica Actuaciones.
        actuaciones = campana.actuaciones.all()
        for actuacion in actuaciones:
            Actuacion.objects.create(
                dia_semanal=actuacion.dia_semanal,
                hora_desde=actuacion.hora_desde,
                hora_hasta=actuacion.hora_hasta,
                campana=campana_replicada,
            )

        audios_de_campana = campana.audios_de_campana.all()
        for audio_de_campana in audios_de_campana:
            AudioDeCampana.objects.create(
                orden=audio_de_campana.orden,
                audio_descripcion=audio_de_campana.audio_descripcion,
                audio_original=audio_de_campana.audio_original,
                audio_asterisk=audio_de_campana.audio_asterisk,
                tts=audio_de_campana.tts,
                tts_mensaje=audio_de_campana.tts_mensaje,
                archivo_de_audio=audio_de_campana.archivo_de_audio,
                campana=campana_replicada
            )

        return campana_replicada

upload_to_audios_asterisk = upload_to("audios_asterisk", 95)
upload_to_audios_originales = upload_to("audios_reproduccion", 95)


class Campana(AbstractCampana):
    """Una campaña del call center"""

    objects_default = models.Manager()
    # Por defecto django utiliza el primer manager instanciado. Se aplica al
    # admin de django, y no aplica las customizaciones del resto de los
    # managers que se creen.

    objects = CampanaManager()
    objects_template = TemplateManager()

    TIPO_RECICLADO_TOTAL = 1
    TIPO_RECICLADO_PENDIENTES = 2

    TIPO_RECICLADO_OCUPADOS = 3
    TIPO_RECICLADO_NO_CONTESTADOS = 4
    TIPO_RECICLADO_NUMERO_ERRONEO = 5
    TIPO_RECICLADO_LLAMADA_ERRONEA = 6

    TIPO_RECICLADO_UNICO = (
        (TIPO_RECICLADO_TOTAL, 'TOTAL'),
        (TIPO_RECICLADO_PENDIENTES, 'PENDIENTES'),
    )

    TIPO_RECICLADO_CONJUNTO = (
        (TIPO_RECICLADO_OCUPADOS, 'OCUPADOS'),
        (TIPO_RECICLADO_NO_CONTESTADOS, 'NO CONTESTO'),
        (TIPO_RECICLADO_NUMERO_ERRONEO, 'NUMERO ERRONEO'),
        (TIPO_RECICLADO_LLAMADA_ERRONEA, 'LLAMADA ERRONEA'),
    )

    # FIXME: El atributo estado podría ir en la clase base,
    # pero las constantes que definen las choices no se
    # sobreescriben. Revisar.
    ESTADO_EN_DEFINICION = 1
    """La campaña esta siendo definida en el wizard"""

    ESTADO_ACTIVA = 2
    """La campaña esta activa, o sea, EN_CURSO o PROGRAMADA
    A nivel de modelos, solo queremos registrar si está ACTIVA, y no nos
    importa si esta EN_CURSO (o sea, si en este momento el daemon está
    generando llamadas asociadas a la campaña) o PROGRAMADA (si todavia no
    estamos en el rango de dias y horas en los que se deben generar
    las llamadas)
    """

    ESTADO_PAUSADA = 3
    """La capaña fue pausada"""

    ESTADO_FINALIZADA = 4
    """La campaña fue finalizada, automatica o manualmente.
    Para mas inforacion, ver `finalizar()`"""

    ESTADO_DEPURADA = 5
    """La campaña ya fue depurada"""

    ESTADO_BORRADA = 6
    """La campaña ya fue borrada"""

    ESTADO_TEMPLATE_EN_DEFINICION = 7
    """La campaña se creo como template y esta en proceso de definición."""

    ESTADO_TEMPLATE_ACTIVO = 8
    """La campaña se creo como template y esta activa, en condición de usarse
    como tal."""

    ESTADO_TEMPLATE_BORRADO = 9
    """La campaña se creo como template y esta borrada, ya no puede usarse
    como tal."""

    ESTADOS = (
        (ESTADO_EN_DEFINICION, '(en definicion)'),
        (ESTADO_ACTIVA, 'Activa'),
        (ESTADO_PAUSADA, 'Pausada'),
        (ESTADO_FINALIZADA, 'Finalizada'),
        (ESTADO_DEPURADA, 'Depurada'),
        (ESTADO_BORRADA, 'Borrada'),

        (ESTADO_TEMPLATE_EN_DEFINICION, '(Template en definicion)'),
        (ESTADO_TEMPLATE_ACTIVO, 'Template Activo'),
        (ESTADO_TEMPLATE_BORRADO, 'Template Borrado'),
    )

    ACCION_NINGUNA = 0
    ACCION_DETECTAR_CONTESTADOR = 1
    ACCION_DETECTAR_EVITAR_CONTESTADOR = 2
    ACCIONES_CONTESTADOR = (
        (ACCION_NINGUNA, 'No hacer nada'),
        (ACCION_DETECTAR_CONTESTADOR, 'Detectar contestador'),
        (ACCION_DETECTAR_EVITAR_CONTESTADOR, 'Detectar y evitar contestador'),
    )

    estado = models.PositiveIntegerField(
        choices=ESTADOS,
        default=ESTADO_EN_DEFINICION,
    )
    cantidad_canales = models.PositiveIntegerField()
    cantidad_intentos = models.PositiveIntegerField()
    segundos_ring = models.PositiveIntegerField()
    duracion_de_audio = models.TimeField(null=True, blank=True)
    estadisticas = models.TextField(null=True, blank=True)
    es_template = models.BooleanField(default=False)
    accion_contestador = models.PositiveIntegerField(
        choices=ACCIONES_CONTESTADOR,
        default=ACCION_NINGUNA,
    )

    def obtener_id_archivo_audio(self):
        """
        Este método se encarga de llamar a la función que obtiene el ID de
        ArchivoDeAudio en caso que el audio de la campana haya sido
        seleccionado de uno pre cargado en archivos de audio.
        En caso que no se haya sleccionado un audio pre cargado en
        ArchivoDeAudio y se haya subido un audio específico para la campana
        devolvera None.
        """
        conversor_audio = ConversorDeAudioService()
        return conversor_audio.obtener_id_archivo_de_audio_desde_path(
            self.audio_asterisk.name)

    def puede_finalizarse(self):
        """Metodo que realiza los chequeos necesarios del modelo, y
        devuelve booleano indincando si se puede o no finalizar.

        Actualmente solo chequea el estado de la campaña.

        :returns: bool - True si la campaña puede finalizarse
        """
        return self.estado in (Campana.ESTADO_ACTIVA, Campana.ESTADO_PAUSADA)

    def puede_depurarse(self):
        """Metodo que realiza los chequeos necesarios del modelo, y
        devuelve booleano indincando si se puede o no depurar.

        Actualmente solo chequea el estado de la campaña.

        :returns: bool - True si la campaña puede depurarse
        """
        return self.estado == Campana.ESTADO_FINALIZADA

    def puede_borrarse(self):
        """Metodo que realiza los chequeos necesarios del modelo, y
        devuelve booleano indincando si se puede o no borrar.

        Actualmente solo chequea el estado de la campaña.

        :returns: bool - True si la campaña puede borrarse.
        """
        return self.estado == Campana.ESTADO_DEPURADA

    def activar_template(self):
        """
        Setea la Campaña -- Template como ESTADO_TEMPLATE_ACTIVO
        """
        logger.info("Seteando campana-->template %s como ACTIVO", self.id)
        assert self.estado == Campana.ESTADO_TEMPLATE_EN_DEFINICION
        self.estado = Campana.ESTADO_TEMPLATE_ACTIVO
        self.save()

    def borrar_template(self):
        """
        Setea la campaña como BORRADA
        """
        logger.info("Seteando campana-->template %s como BORRADA", self.id)
        assert self.estado == Campana.ESTADO_TEMPLATE_ACTIVO

        self.estado = Campana.ESTADO_BORRADA
        self.save()

    def activar(self):
        """
        Setea la campaña como ACTIVA
        Genera los IntentoDeContacto asociados a esta campaña.
        Genera tantas instancias para AgregacionDeEventoDeContacto como
        cantidad_intentos tenga esta campaña.
        """
        logger.info("Seteando campana %s como ACTIVA", self.id)
        assert self.estado == Campana.ESTADO_EN_DEFINICION
        self.estado = Campana.ESTADO_ACTIVA
        self.save()

        # FIXME: este proceso puede ser costoso, deberia ser asincrono
        # TODO: log timing
        from fts_daemon.models import EventoDeContacto
        EventoDeContacto.objects_gestion_llamadas.programar_campana(
            self.id)

        timestamp_ultimo_evento = now()
        for numero_intento in range(1, self.cantidad_intentos + 1):
            AgregacionDeEventoDeContacto.objects.create(
                campana_id=self.pk, numero_intento=numero_intento,
                timestamp_ultimo_evento=timestamp_ultimo_evento)

    def borrar(self):
        """
        Setea la campaña como BORRADA
        """
        logger.info("Seteando campana %s como BORRADA", self.id)
        assert self.puede_borrarse()

        self.estado = Campana.ESTADO_BORRADA
        self.save()

    def finalizar(self):
        """
        Setea la campaña como finalizada.

        Obviamente, este metodo pasa la campaña al estado FINALIZADA,
        sin hacer ningun tipo de control 'externo' al modelo, como
        por ejemplo, si hay llamadas en curso para esta Campaña.

        Antes de implementar FTS-248 (cuando se introdujo ESTADO_DEPURADA),
        ESTADO_FINALIZADA implicaba que la campaña ya estaba depurada.
        Ahora (post FTS-248) ESTADO_FINALIZADA significa que la campaña está
        finalizada (o sea, ya no debe procesarse), pero todavia no está
        depurada.

        Actualmente, hay 3 procesos que pueden cambiar el estado de la
        Campaña a FINALIZADA, por eso se implemento el control de
        concurrencia:

        1) manualmente, desde la administracion web
        2) el daemon 'llamador', al detectar que ya no hay mas contactos
        3) el daemon 'finalizador', al detectar que ya no se generaran
           llamadas

        Mientras la campaña está en estado FINALIZADA, *NO* debe modificarse
        y debe utilizarse con cuidado, ya que mientras está finalizada,
        el daemon depurador realizará todos los procesos asincronos
        (generaré reportes, re-calculará agregacion de EDC, etc.)

        :raise FTSOptimisticLockingError: si otro thread/proceso ha actualizado
                                          la campaña en la BD
        """
        logger.info("Seteando campana %s como ESTADO_FINALIZADA", self.id)
        assert self.puede_finalizarse()

        update_count = Campana.objects.filter(
            id=self.id, estado=self.estado).update(
                estado=Campana.ESTADO_FINALIZADA)
        if update_count != 1:
            raise(FTSOptimisticLockingError("No se pudo cambiar el estado "
                                            "de la campana en BD"))
        self.estado = Campana.ESTADO_FINALIZADA
        # self.save()

    def depurar(self):
        """Setea la campaña como depurada"""
        # NO hace falta chequear por optimistick locking, ya que hay
        # 1 solo proceso que pasa del estado FINALIZADA a DEPURADA
        # (el depurador, ejceutado en Celery)
        assert self.puede_depurarse(), \
            "La campana no cumple los requisitos para poder depurarse"
        self.estado = Campana.ESTADO_DEPURADA
        self.save()

    def pausar(self):
        """Setea la campaña como ESTADO_PAUSADA"""
        logger.info("Seteando campana %s como ESTADO_PAUSADA", self.id)
        assert self.estado == Campana.ESTADO_ACTIVA
        self.estado = Campana.ESTADO_PAUSADA
        self.save()

    def despausar(self):
        """Setea la campaña como ESTADO_ACTIVA.
        """
        logger.info("Seteando campana %s como ESTADO_ACTIVA", self.id)
        assert self.estado == Campana.ESTADO_PAUSADA
        self.estado = Campana.ESTADO_ACTIVA
        self.save()

    def obtener_detalle_opciones_seleccionadas(self):
        """
        Este método se encarga de invocar al método de EDC que filtra los
        contactos por cada opción seleccionada. Devuelve un lista de
        listas por ejemplo:
        [
           [Opcion, [3513368309, 3513368308]],
           [9, [3513368309, 3513368308]]
        ].
        El primer elemento (en el ejemplo de arriba: 'Opcion', y '9')
        corresponde a la opción seleccionada. Para los casos en que
        se ha presionado un número que no corresponde a ninguna opción,
        en vez de una instancia de Opcion, se devuelve un entero,
        representando el número (del 0 al 9) presionado.
        """
        from fts_daemon.models import EventoDeContacto
        EDC = EventoDeContacto.objects_estadisticas

        opciones = Opcion.objects.filter(campana=self)

        lista_final = []
        for numero_opcion, contactos in EDC.obtener_contactos_por_opciones(self.pk):
            lista_item = []

            digito = EventoDeContacto.EVENTO_A_NUMERO_OPCION_MAP[
                numero_opcion]

            try:
                opcion = opciones.get(digito=digito)
                lista_item.append(opcion)
            except Opcion.DoesNotExist:
                lista_item.append(digito)

            lista_item.append([map(unicode, json.loads(contacto))
                               for contacto in contactos])

            lista_final.append(lista_item)
        return lista_final

    def recalcular_aedc_completamente(self):
        """Recalcula COMPLETAMENTE la agregacion. Este debe
        realizarse cuando estamos SEGUROS que ya no hay llamadas
        en curso. Tiene en cuenta TODOS los EDC.

        Antes de usar estes metodo, tener en cuenta los
        requerimientos de `_plpython_recalcular_aedc_completamente()`
        (ej: transacciones, etc.)
        """
        assert self.estado == Campana.ESTADO_FINALIZADA
        AgregacionDeEventoDeContacto.objects.\
            _plpython_recalcular_aedc_completamente(self)

    def valida_grupo_atencion(self):
        """
        Este método valida, en el caso que para la campana se haya
        selccionado un grupo de atención, que no este borrado.
        """
        for opcion in self.opciones.all():
            if (opcion.grupo_atencion and
                opcion.grupo_atencion.borrado is True):
                return False
        return True

    def valida_derivacion_externa(self):
        """
        Este método valida, en el caso que para la campana se haya
        selccionado una derivacion externa, que no este borrada.
        """
        for opcion in self.opciones.all():
            if (opcion.derivacion_externa and
                opcion.derivacion_externa.borrado is True):
                return False
        return True

    def valida_audio(self):
        """
        Este método se encarga de validar que el audio de la campana actual
        sea válido.
        """
        audios_de_campana = self.audios_de_campana.all()
        if not audios_de_campana:
            return False

        for audio_de_campana in audios_de_campana:
            posibles_audios = [audio_de_campana.audio_asterisk,
                               audio_de_campana.archivo_de_audio,
                               audio_de_campana.tts,
                               audio_de_campana.tts_mensaje]
            if not any(posibles_audios):
                return False
        return True

    def valida_tts(self):
        """
        Este método valida que, en caso que alguno AudioDeCampana de la campana
        sea tts, cada uno de los tts que posea concuerden con alguna columna
        de la base de datos que tenga la campana.
        Devuelve True or False.
        """
        metadata = self.bd_contacto.get_metadata()

        audios_de_campana = self.audios_de_campana.all()
        for audio_de_campana in audios_de_campana:
            if (audio_de_campana.tts and audio_de_campana.tts not in
                    metadata.nombres_de_columnas):
                return False
        return True

    def obtener_actuaciones_validas(self):
        if self.es_template:
            return []
        return super(Campana, self).obtener_actuaciones_validas()

    def get_nombre_contexto_para_asterisk(self):
        """Devuelve un texto para ser usado en Asterisk,
        para nombrar el contexto asociado a la campana.
        """
        assert self.id
        return 'campania_{0}'.format(self.id)

    def valida_estado_en_definicion(self):
        """
        Este método se encarga de validar que el estado de la campana
        actual sea ESTADO_EN_DEFINICION.

        Devuelve un booleano.
        """
        return self.estado == Campana.ESTADO_EN_DEFINICION

    def obtener_duracion_de_audio_en_segundos(self):
        """
        Devuelve la duración del audio de la campana en segundos.
        """
        duracion_de_audio_en_segundo = (self.duracion_de_audio.hour * 3600 +
                                        self.duracion_de_audio.minute * 60 +
                                        self.duracion_de_audio.second)

        return duracion_de_audio_en_segundo

    def clean(self, *args, **kwargs):
        """
        Valida que al crear una campaña la fechas de
        inicialización sea menor o igual a la fecha de
        finalización.
        """
        super(Campana, self).clean(*args, **kwargs)

        fecha_hoy = datetime.date.today()
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio > self.fecha_fin:
                raise ValidationError({
                    'fecha_inicio': ["La fecha de inicio debe ser\
                        menor o igual a la fecha de finalización."],
                    'fecha_fin': ["La fecha de inicio debe ser\
                        mayor o igual a la fecha de finalización."],
                })
            elif self.fecha_inicio < fecha_hoy:
                raise ValidationError({
                    'fecha_inicio': ["La fecha de inicio debe ser\
                        mayor o igual a la fecha actual."],
                })

        try:
            cantidad_contactos = self.bd_contacto.get_cantidad_contactos()
        except:
            pass
        else:
            if not self.cantidad_canales < cantidad_contactos:
                raise ValidationError({
                        'cantidad_canales': ["La cantidad de canales debe ser\
                            menor a la cantidad de contactos de la base de\
                            datos."]
                    })

    class Meta:
        ordering = ['pk']

    def __unicode__(self):
        return self.nombre


class CampanaSmsManager(BaseCampanaYCampanaSmsManager):

    def obtener_ultimo_identificador_sms(self):
        """
        Este metodo se encarga de devolver el siguinte identificador sms
        y si no existe campana sms me devuelve 1000
        """
        try:
            identificador = \
                self.latest('id').identificador_campana_sms + 1
        except CampanaSms.DoesNotExist:
            identificador = 1000

        return identificador

    def obtener_confirmadas(self):
        """Devuelve campañas en estado confirmadas.
        """
        return self.filter(estado=CampanaSms.ESTADO_CONFIRMADA)

    def obtener_pausadas(self):
        """Devuelve campañas en estado pausadas.
        """
        return self.filter(estado=CampanaSms.ESTADO_PAUSADA)

    def obtener_para_detalle(self, campana_sms_id):
        """Devuelve la campaña pasada por ID, siempre que a dicha
        campaña se le pueda ver el detalle, debe estar en estado activa,
        pausada, finalifada o depurada.

        En caso de no encontarse, lanza SuspiciousOperation
        """
        try:
            ESTADOS_VER_DETALLE = [CampanaSms.ESTADO_CONFIRMADA,
                                   CampanaSms.ESTADO_PAUSADA]
            return self.filter(estado__in=ESTADOS_VER_DETALLE).get(
                pk=campana_sms_id)
        except CampanaSms.DoesNotExist:
            raise(SuspiciousOperation("No se encontro campana en estadp"
                                      "ESTADO_CONFIRMADA ó ESTADO_PAUSADA."))

    def obtener_campana_sms_para_reciclar(self, campana_sms_id):
        """Devuelve la campaña sms pasada por ID, siempre que dicha
        campaña pueda ser reciclada. Debe haber estar confirmada ó pausada.

        En caso de no encontarse, lanza SuspiciousOperation
        """
        try:
            ESTADOS_RECICLAR = [CampanaSms.ESTADO_CONFIRMADA,
                                CampanaSms.ESTADO_PAUSADA]
            return self.filter(estado__in=ESTADOS_RECICLAR).get(
                pk=campana_sms_id)
        except CampanaSms.DoesNotExist:
            raise(SuspiciousOperation("No se encontro campana en estado"
                                      "ESTADO_CONFIRMADA ó ESTADO_PAUSADA"))

    def reciclar_campana_sms(self, campana_sms_id, bd_contacto):
        """
        Este método replica la campana pasada por parámetro con fin de
        reciclar la misma.
        """
        try:
            campana_sms = self.get(pk=campana_sms_id)
            # Fixme chequear a futuro unestado

        except CampanaSms.DoesNotExist:
            logger.warn("No se pudo recuperar la CampanaSms: %s", campana_sms_id)
            raise FtsRecicladoCampanaError("No se pudo recuperar la Campaña de Sms.")
        else:
            campana_reciclada = self.replicar_campana_sms(campana_sms)
            campana_reciclada.nombre = '{0} (reciclada)'.format(
                campana_reciclada.nombre)
            campana_reciclada.bd_contacto = bd_contacto
            campana_reciclada.save()

        return campana_reciclada

    def replicar_campana_sms(self, campana_sms):
        """
        Este método se encarga de replicar una campana existente, creando una
        campana nueva de iguales características.
        """
        assert isinstance(campana_sms, CampanaSms)

        # Replica Campana.
        campana_replicada = self.create(
            nombre=campana_sms.nombre,
            cantidad_chips=campana_sms.cantidad_chips,
            fecha_inicio=campana_sms.fecha_inicio,
            fecha_fin=campana_sms.fecha_fin,
            bd_contacto=campana_sms.bd_contacto,
            template_mensaje=campana_sms.template_mensaje,
            template_mensaje_opcional=campana_sms.template_mensaje_opcional,
            template_mensaje_alternativo=campana_sms.template_mensaje_alternativo,
            tiene_respuesta=campana_sms.tiene_respuesta,
            identificador_campana_sms=self.obtener_ultimo_identificador_sms(),
        )

        # Replica OpcionSms
        opciones_sms = campana_sms.opcionsmss.all()
        for opcion in opciones_sms:
            OpcionSms.objects.create(
                respuesta=opcion.respuesta,
                respuesta_descripcion=opcion.respuesta_descripcion,
                campana_sms=campana_replicada,
            )

        # Replica Actuaciones.
        actuaciones = campana_sms.actuaciones.all()

        for actuacion in actuaciones:
            ActuacionSms.objects.create(
                dia_semanal=actuacion.dia_semanal,
                hora_desde=actuacion.hora_desde,
                hora_hasta=actuacion.hora_hasta,
                campana_sms=campana_replicada,
            )

        return campana_replicada

    def obtener_pausada_para_eliminar(self, campana_sms_id):
        """Devuelve la campaña pasada por ID, siempre que dicha
        campaña pueda ser eliminada.

        En caso de no encontarse, lanza SuspiciousOperation
        """
        try:
            return self.filter(
                estado=CampanaSms.ESTADO_PAUSADA).get(pk=campana_sms_id)
        except CampanaSms.DoesNotExist:
            raise(SuspiciousOperation("No se encontro campana en "
                                      "estado ESTADO_PAUSADA"))

    def obtener_pausadas_confirmadas_para_reportes(self):
        """Devuelve campañas sms confirmadas y pausadas para listado de reportes
        debe estar ordenadas.
        """
        ESTADOS_REPORTE = [CampanaSms.ESTADO_PAUSADA,
                           CampanaSms.ESTADO_CONFIRMADA
                           ]
        return self.filter(estado__in=ESTADOS_REPORTE).order_by('-id')

    def obtener_tiene_repuesta_reporte(self, campana_sms_id):
        """Devuelve la campaña pasada por ID, siempre que dicha
        campaña pueda ser mostrada.

        Si tiene_respuesta es True

        En caso de no encontarse, lanza SuspiciousOperation
        """
        try:
            return self.filter(tiene_respuesta=True).get(pk=campana_sms_id)
        except CampanaSms.DoesNotExist:
            raise(SuspiciousOperation("No se encontro campana en "
                                      "tiene_respuesta"))


class CampanaSms(AbstractCampana):
    """
    Representa una campana de envíos de SMS.
    """

    objects_default = models.Manager()
    # Por defecto django utiliza el primer manager instanciado. Se aplica al
    # admin de django, y no aplica las customizaciones del resto de los
    # managers que se creen.

    objects = CampanaSmsManager()

    TIPO_RECICLADO_TOTAL = 1
    TIPO_RECICLADO_ERROR_ENVIO = 2
    TIPO_RECICLADO_ENVIADO_SIN_CONFIRMACION = 3

    TIPO_RECICLADO_UNICO = (
        (TIPO_RECICLADO_TOTAL, 'TOTAL'),
    )

    TIPO_RECICLADO_CONJUNTO = (
        (TIPO_RECICLADO_ERROR_ENVIO, 'ERROR DE ENVIO'),
        (TIPO_RECICLADO_ENVIADO_SIN_CONFIRMACION, 'ENVIADO SIN CONFIRMACION'),
    )

    # FIXME: El atributo estado podría ir en la clase base,
    # pero las constantes que definen las choices no se
    # sobreescriben. Revisar.
    ESTADO_EN_DEFINICION = 1
    """La campaña esta siendo definida en el wizard"""

    ESTADO_CONFIRMADA = 2
    """Se completó la definición de la campaña en el wizard"""

    ESTADO_PAUSADA = 3
    """La capaña fue pausada"""

    ESTADO_BORRADA = 4
    """La campaña ya fue borrada"""

    ESTADOS = (
        (ESTADO_EN_DEFINICION, '(en definicion)'),
        (ESTADO_CONFIRMADA, 'Confirmada'),
        (ESTADO_PAUSADA, 'Pausada'),
    )

    estado = models.PositiveIntegerField(
        choices=ESTADOS, default=ESTADO_EN_DEFINICION)

    cantidad_chips = models.PositiveIntegerField()
    template_mensaje = models.TextField()
    template_mensaje_opcional = models.TextField(null=True, blank=True)
    template_mensaje_alternativo = models.TextField(null=True, blank=True)
    tiene_respuesta = models.BooleanField(default=False)
    identificador_campana_sms = models.PositiveIntegerField(unique=True)

    class Meta:
        ordering = ['pk']

    def __unicode__(self):
        return self.nombre

    def valida_mensaje(self):
        if self.template_mensaje:
            return True
        return False

    def puede_borrarse(self):
        """Metodo que realiza los chequeos necesarios del modelo, y
        devuelve booleano indincando si se puede o no borrar.

        Actualmente solo chequea el estado de la campaña sms.

        :returns: bool - True si la campaña puede borrarse.
        """
        return self.estado == Campana.ESTADO_PAUSADA

    def confirmar(self):
        """
        Setea la campana sms como confirmada, lista para ser utilizada.
        """

        logger.info("Seteando campana sms %s como CONFIRMADA", self.id)
        assert self.estado == CampanaSms.ESTADO_EN_DEFINICION
        self.estado = self.ESTADO_CONFIRMADA
        self.save()

    def borrar(self):
        """
        Setea la campaña como BORRADA
        """
        logger.info("Seteando campana sms %s como BORRADA", self.id)
        assert self.puede_borrarse()

        self.estado = CampanaSms.ESTADO_BORRADA
        self.save()

    def pausar(self):
        """Setea la campaña como ESTADO_PAUSADA"""
        logger.info("Seteando campana %s como ESTADO_PAUSADA", self.id)
        assert self.estado == CampanaSms.ESTADO_CONFIRMADA
        self.estado = Campana.ESTADO_PAUSADA
        self.save()

    def despausar(self):
        """Setea la campaña como ESTADO_ACTIVA.
        """
        logger.info("Seteando campana %s como ESTADO_CONFIRMADA", self.id)
        assert self.estado == CampanaSms.ESTADO_PAUSADA
        self.estado = CampanaSms.ESTADO_CONFIRMADA
        self.save()


class AudioDeCampanaManager(models.Manager):

    def obtener_siguiente_orden(self, campana_id):
        try:
            audio_de_campana = self.filter(campana=campana_id).latest('orden')
            return audio_de_campana.orden + 1
        except AudioDeCampana.DoesNotExist:
            return 1


class AudioDeCampana(models.Model):
    """
    Representa los audios que tienen las campañas.
    """

    objects = AudioDeCampanaManager()

    ORDEN_SENTIDO_UP = 0
    ORDEN_SENTIDO_DOWN = 1

    orden = models.PositiveIntegerField()
    audio_descripcion = models.CharField(
        max_length=100,
        null=True, blank=True,
    )
    audio_original = models.FileField(
        upload_to=upload_to_audios_originales,
        max_length=100,
        null=True, blank=True,
    )
    audio_asterisk = models.FileField(
        upload_to=upload_to_audios_asterisk,
        max_length=100,
        null=True, blank=True,
    )
    tts = models.CharField(
        max_length=128,
        null=True, blank=True,
    )
    tts_mensaje = models.TextField(null=True, blank=True)
    archivo_de_audio = models.ForeignKey(
        'ArchivoDeAudio',
        null=True, blank=True,
    )
    campana = models.ForeignKey(
        'Campana',
        related_name='audios_de_campana'
    )

    def __unicode__(self):
        return "{0} Orden: {1}".format(self.pk, self.orden)

    class Meta:
        ordering = ['orden']
        unique_together = ("orden", "campana")

    def obtener_audio_anterior(self):
        """
        Este método devuelve el audio de campana anterior a self, teniendo en
        cuenta que pertenezca a la misma campana que self.
        """
        return AudioDeCampana.objects.filter(campana=self.campana,
                                             orden__lt=self.orden).last()

    def obtener_audio_siguiente(self):
        """
        Este método devuelve el audio de campana siguiente a self, teniendo en
        cuenta que pertenezca a la misma campana que self.
        """
        return AudioDeCampana.objects.filter(campana=self.campana,
                                             orden__gt=self.orden).first()


#==============================================================================
# AgregacionDeEventoDeContacto
#==============================================================================

class AgregacionDeEventoDeContactoManager(models.Manager):

    def _plpython_recalcular_aedc_completamente(self, campana):
        """Ejecuta el procedimiento almancenado / plpython
        `recalculate_agregacion_edc_py_v1()`.

        Re-calcula COMPLETAMENTE las agregaciones (a diferencia del
        otro procedimiento almanceado, que ACTUALIZA las agragaciones,
        teniendo en cuenta sólo los EDC pendientes de procesar).

        Este metodo debe ser llamado englobado en una transacción, ya
        que bloquea AEDC.

        Este metodo NO debería ser llamado directamente. En su lugar,
        utilice Campana.recalcular_aedc_completamente()
        """

        with log_timing(logger,
            "recalcular_aedc(): recalculo de agregacion tardo %s seg"):
            cursor = connection.cursor()
            cursor.execute(
                "SELECT recalculate_agregacion_edc_py_v1(%s, %s)",
                    [campana.id, campana.cantidad_intentos])

        values = cursor.fetchall()
        row = values[0]
        ret_value = row[0]

        # Return values
        #       0: RECALCULO OK
        #      -1: ERROR DE LOCK
        #       X: EL UPDATE HA FALLADO -> genera EXCEPCION
        assert ret_value == 0, ("_plpython_recalcular_aedc_completamente(): "
            "el procedimiento almacenado no devolvio valor esperado. "
            "Devolvio: %s", ret_value)

    def procesa_agregacion(self, campana_id, cantidad_intentos,
                           tipo_agregacion):
        """
        Sumariza los contadores de cada intento de contacto de la campana.
        :param campana_id: De que campana que se sumarizaran los contadores.
        :type campana_id: int
        """

        campana = Campana.objects.get(pk=campana_id)
        limite_intentos = campana.cantidad_intentos
        total_contactos = campana.bd_contacto.get_cantidad_contactos()
        dic_totales = {
            'limite_intentos': limite_intentos,
            'total_contactos': total_contactos,
        }

        if not total_contactos:
            logger.warn("procesa_agregacion(): saliendo porque la "
                "bd para la campana %s no posee datos", campana.id)
            return dic_totales

        if (tipo_agregacion !=
            AgregacionDeEventoDeContacto.TIPO_AGREGACION_REPORTE):

            with log_timing(logger,
                "procesa_agregacion(): recalculo de agregacion tardo %s seg"):
                with transaction.atomic(savepoint=False):
                    cursor = connection.cursor()
                    cursor.execute("SELECT update_agregacion_edc_py_v1(%s)",
                        [campana.id])

        agregaciones_campana = self.filter(campana_id=campana_id)

        dic_totales.update(agregaciones_campana.aggregate(
            total_intentados=Sum('cantidad_intentos'),
            total_atentidos=Sum('cantidad_finalizados'),
            total_opcion_0=Sum('cantidad_opcion_0'),
            total_opcion_1=Sum('cantidad_opcion_1'),
            total_opcion_2=Sum('cantidad_opcion_2'),
            total_opcion_3=Sum('cantidad_opcion_3'),
            total_opcion_4=Sum('cantidad_opcion_4'),
            total_opcion_5=Sum('cantidad_opcion_5'),
            total_opcion_6=Sum('cantidad_opcion_6'),
            total_opcion_7=Sum('cantidad_opcion_7'),
            total_opcion_8=Sum('cantidad_opcion_8'),
            total_opcion_9=Sum('cantidad_opcion_9'))
        )

        total_no_llamados = total_contactos - dic_totales[
            'total_intentados']
        if total_no_llamados < 0:
            total_no_llamados = 0

        total_no_atendidos = total_contactos - (total_no_llamados +
            dic_totales['total_atentidos'])

        total_opciones = 0
        for opcion in range(10):
            total_opciones += dic_totales['total_opcion_{0}'.format(
                opcion)]

        total_atendidos_intentos = dict((agregacion_campana.numero_intento,
            agregacion_campana.cantidad_finalizados)
            for agregacion_campana in agregaciones_campana)

        finalizados = 0
        for agregacion_campana in agregaciones_campana:
            finalizados += agregacion_campana.cantidad_finalizados

            finalizados_limite = 0
            if agregacion_campana == limite_intentos:
                if agregacion_campana.cantidad_intentos >\
                    agregacion_campana.cantidad_finalizados:
                    finalizados_limite =\
                        (agregacion_campana.cantidad_intentos -
                        agregacion_campana.cantidad_finalizados)

            porcentaje_avance = float(100 * (finalizados +
                    finalizados_limite) / total_contactos)

        dic_totales.update({
            'total_no_llamados': total_no_llamados,
            'total_no_atendidos': total_no_atendidos,
            'total_opciones': total_opciones,
            'total_atendidos_intentos': total_atendidos_intentos,
            'porcentaje_avance': porcentaje_avance})

        return dic_totales


class AgregacionDeEventoDeContacto(models.Model):
    """
    Representa los contadores de EventoDeContacto para
    *cada grupo de intentos* de llamadas de una Campana.
    Por lo que si una Campana tiene un limite de 2 intentos
    para cada contacto, esa campana debería tener 2 registros
    con las cantidades, de ciertos eventos, de ese intento.
    """
    TIPO_AGREGACION_SUPERVISION = 1
    TIPO_AGREGACION_REPORTE = 2
    TIPO_AGREGACION_DEPURACION = 3

    objects = AgregacionDeEventoDeContactoManager()

    campana_id = models.IntegerField(db_index=True)
    numero_intento = models.IntegerField()
    cantidad_intentos = models.IntegerField(default=0)
    cantidad_finalizados = models.IntegerField(default=0)
    cantidad_opcion_0 = models.IntegerField(default=0)
    cantidad_opcion_1 = models.IntegerField(default=0)
    cantidad_opcion_2 = models.IntegerField(default=0)
    cantidad_opcion_3 = models.IntegerField(default=0)
    cantidad_opcion_4 = models.IntegerField(default=0)
    cantidad_opcion_5 = models.IntegerField(default=0)
    cantidad_opcion_6 = models.IntegerField(default=0)
    cantidad_opcion_7 = models.IntegerField(default=0)
    cantidad_opcion_8 = models.IntegerField(default=0)
    cantidad_opcion_9 = models.IntegerField(default=0)
    timestamp_ultima_actualizacion = models.DateTimeField(auto_now_add=True)
    timestamp_ultimo_evento = models.DateTimeField()
    tipo_agregacion = models.IntegerField(null=True)

    def __unicode__(self):
        return "AgregacionDeEventoDeContacto-{0}-{1}".format(
            self.campana_id, self.numero_intento)


#==============================================================================
# Opciones
#==============================================================================

class Opcion(models.Model):
    """
    Representa una Opción a marcar en la llamada.
    Cada opción realiza una acción concreta. Por
    ejemplo, derivar la llamada a un agente.
    """

    """Considero opciones solo del 0 a 9"""
    (CERO, UNO, DOS, TRES, CUATRO,
    CINCO, SEIS, SIETE, OCHO, NUEVE) = range(0, 10)
    DIGITO_CHOICES = (
        (CERO, '0'),
        (UNO, '1'),
        (DOS, '2'),
        (TRES, '3'),
        (CUATRO, '4'),
        (CINCO, '5'),
        (SEIS, '6'),
        (SIETE, '7'),
        (OCHO, '8'),
        (NUEVE, '9'),
    )
    digito = models.PositiveIntegerField(
        choices=DIGITO_CHOICES,
    )

    DERIVAR_GRUPO_ATENCION = 0
    """Deriva la llamada. Ejemplo Grupo Atencion."""

    DERIVAR_DERIVACION_EXTERNA = 1
    """Deriva la llamada. Ejemplo Grupo Atencion."""

    CALIFICAR = 2
    """Estable una calificación a la llamada."""

    VOICEMAIL = 3
    """Habilita para dejar un mensaje de voz."""

    REPETIR = 4
    """Repetir el mensaje."""

    ACCION_CHOICES = (
        (DERIVAR_GRUPO_ATENCION, 'DERIVAR GRUPO ATENCION'),
        (DERIVAR_DERIVACION_EXTERNA, 'DERIVAR DERIVACION EXTERNA'),
        (CALIFICAR, 'CALIFICAR'),
        (REPETIR, 'REPETIR'),
    )
    accion = models.PositiveIntegerField(
        choices=ACCION_CHOICES,
    )
    derivacion_externa = models.ForeignKey(
        'DerivacionExterna',
        null=True, blank=True,
    )
    grupo_atencion = models.ForeignKey(
        'GrupoAtencion',
        null=True, blank=True,
    )
    calificacion = models.ForeignKey(
        'Calificacion',
        null=True, blank=True,
    )
    campana = models.ForeignKey(
        'Campana',
        related_name='opciones'
    )

    def __unicode__(self):
        return "Campaña {0} - Opción: {1}".format(
            self.campana,
            self.digito,
        )

    def get_descripcion_de_opcion(self):
        if self.accion == Opcion.DERIVAR_GRUPO_ATENCION:
            if self.grupo_atencion:
                return "Der. {0}".format(
                    self.grupo_atencion.nombre)
            else:
                return "Derivar"

        if self.accion == Opcion.DERIVAR_DERIVACION_EXTERNA:
            if self.grupo_atencion:
                return "Der.. {0}".format(
                    self.derivacion_externa.nombre)
            else:
                return "Derivar"

        if self.accion == Opcion.CALIFICAR:
            if self.calificacion:
                return "{0}".format(
                    self.calificacion.nombre)
            else:
                return "Calificar"
        if self.accion == Opcion.REPETIR:
            return "Repetir"

        return "Opcion desconocida"

    class Meta:
        #unique_together = ("digito", "campana")
        unique_together = (
            ("digito", "campana"),
            ("accion", "campana", "grupo_atencion"),
            ("accion", "campana", "calificacion"),
        )


#==============================================================================
# Actuaciones
#==============================================================================


class AbstractActuacion(models.Model):
    """
    Modelo abstracto para las actuaciones de las campanas
    de audio y sms.
    """

    """Dias de la semana, compatibles con datetime.date.weekday()"""
    LUNES = 0
    MARTES = 1
    MIERCOLES = 2
    JUEVES = 3
    VIERNES = 4
    SABADO = 5
    DOMINGO = 6

    DIA_SEMANAL_CHOICES = (
        (LUNES, 'LUNES'),
        (MARTES, 'MARTES'),
        (MIERCOLES, 'MIERCOLES'),
        (JUEVES, 'JUEVES'),
        (VIERNES, 'VIERNES'),
        (SABADO, 'SABADO'),
        (DOMINGO, 'DOMINGO'),
    )
    dia_semanal = models.PositiveIntegerField(
        choices=DIA_SEMANAL_CHOICES,
    )

    hora_desde = models.TimeField()
    hora_hasta = models.TimeField()

    class Meta:
        abstract = True

    def verifica_actuacion(self, hoy_ahora):
        """
        Este método verifica que el día de la semana y la hora
        pasada en el parámetro hoy_ahora sea válida para la
        actuación actual.
        Devuelve True o False.
        """

        assert isinstance(hoy_ahora, datetime.datetime)

        dia_semanal = hoy_ahora.weekday()
        hora_actual = datetime.time(
            hoy_ahora.hour, hoy_ahora.minute, hoy_ahora.second)

        if not self.dia_semanal == dia_semanal:
            return False

        if not self.hora_desde <= hora_actual <= self.hora_hasta:
            return False

        return True

    def dia_concuerda(self, fecha_a_chequear):
        """Este método evalua si el dia de la actuacion actual `self`
        concuerda con el dia de la semana de la fecha pasada por parametro.

        :param fecha_a_chequear: fecha a chequear
        :type fecha_a_chequear: `datetime.date`
        :returns: bool - True si la actuacion es para el mismo dia de
                  la semana que el dia de la semana de `fecha_a_chequear`
        """
        # NO quiero que funcione con `datatime` ni ninguna otra
        #  subclase, más que específicamente `datetime.date`,
        #  por eso no uso `isinstance()`.
        assert type(fecha_a_chequear) == datetime.date

        return self.dia_semanal == fecha_a_chequear.weekday()

    def es_anterior_a(self, time_a_chequear):
        """Este método evalua si el rango de tiempo de la actuacion
        actual `self` es anterior a la hora pasada por parametro.
        Verifica que sea 'estrictamente' anterior, o sea, ambas horas
        de la Actuacion deben ser anteriores a la hora a chequear
        para que devuelva True.

        :param time_a_chequear: hora a chequear
        :type time_a_chequear: `datetime.time`
        :returns: bool - True si ambas horas de la actuacion son anteriores
                  a la hora pasada por parametro `time_a_chequear`.
        """
        # NO quiero que funcione con ninguna subclase, más que
        #  específicamente `datetime.time`, por eso no uso `isinstance()`.
        assert type(time_a_chequear) == datetime.time

        # Es algo redundante chequear ambos, pero bueno...
        return self.hora_desde < time_a_chequear and \
            self.hora_hasta < time_a_chequear

    def clean(self):
        """
        Valida que al crear una actuación a una campaña
        no exista ya una actuación en el rango horario
        especificado y en el día semanal seleccionado.
        """
        if self.hora_desde and self.hora_hasta:
            if self.hora_desde >= self.hora_hasta:
                raise ValidationError({
                    'hora_desde': ["La hora desde debe ser\
                        menor o igual a la hora hasta."],
                    'hora_hasta': ["La hora hasta debe ser\
                        mayor a la hora desde."],
                })

            conflicto = self.get_campana().actuaciones.filter(
                dia_semanal=self.dia_semanal,
                hora_desde__lte=self.hora_hasta,
                hora_hasta__gte=self.hora_desde,
            )
            if any(conflicto):
                raise ValidationError({
                    'hora_desde': ["Ya esta cubierto el rango horario\
                        en ese día semanal."],
                    'hora_hasta': ["Ya esta cubierto el rango horario\
                        en ese día semanal."],
                })


class Actuacion(AbstractActuacion):
    """
    Representa los días de la semana y los
    horarios en que una campaña se ejecuta.
    """

    campana = models.ForeignKey(
        'Campana',
        related_name='actuaciones'
    )

    def __unicode__(self):
        return "Campaña {0} - Actuación: {1}".format(
            self.campana,
            self.get_dia_semanal_display(),
        )

    def get_campana(self):
        return self.campana


class ActuacionSms(AbstractActuacion):
    """
    Representa los días de la semana y los
    horarios en que una campaña sms se ejecuta.
    """

    campana_sms = models.ForeignKey(
        'CampanaSms',
        related_name='actuaciones'
    )

    def __unicode__(self):
        return "CampañaSms {0} - Actuación: {1}".format(
            self.campana_sms,
            self.get_dia_semanal_display(),
        )

    def get_campana(self):
        return self.campana_sms


#==============================================================================
# Calificacion
#==============================================================================

class Calificacion(models.Model):
    """
    Representa una Calificacion
    """
    nombre = models.CharField(
        max_length=64,
    )
    campana = models.ForeignKey(
        'Campana',
        related_name='calificaciones'
    )

    def __unicode__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']


#==============================================================================
# ArchivoDeAudio
#==============================================================================

class ArchivoDeAudioManager(models.Manager):
    """Manager para ArchivoDeAudio"""

    def get_queryset(self):
        return super(ArchivoDeAudioManager, self).get_queryset().exclude(
            borrado=True)


class ArchivoDeAudio(models.Model):
    """
    Representa una ArchivoDeAudio
    """
    objects_default = models.Manager()
    # Por defecto django utiliza el primer manager instanciado. Se aplica al
    # admin de django, y no aplica las customizaciones del resto de los
    # managers que se creen.

    objects = ArchivoDeAudioManager()

    descripcion = models.CharField(
        max_length=100,
    )
    audio_original = models.FileField(
        upload_to=upload_to_audios_originales,
        max_length=100,
        null=True, blank=True,
    )
    audio_asterisk = models.FileField(
        upload_to=upload_to_audios_asterisk,
        max_length=100,
        null=True, blank=True,
    )
    borrado = models.BooleanField(
        default=False,
        editable=False,
    )

    def __unicode__(self):
        if self.borrado:
            return '(ELiminado) {0}'.format(self.descripcion)
        return self.descripcion

    def borrar(self):
        """
        Setea la ArchivoDeAudio como BORRADO.
        """
        logger.info("Seteando ArchivoDeAudio %s como BORRADO", self.id)

        self.borrado = True
        self.save()


#==============================================================================
# DuracionDeLlamada
#==============================================================================

class DuracionDeLlamadaManager(models.Manager):
    """Manager para DuracionDeLlamada"""

    def obtener_duracion_de_llamdas(self, numero_telefono):
        return self.filter(numero_telefono__contains=numero_telefono)

    def obtener_de_campana(self, campana):
        return self.filter(campana=campana)


class DuracionDeLlamada(models.Model):
    """Representa la duración de las llamdas de las campanas, con el fin
        de contar con los datos para búsquedas y estadísticas"""

    objects_default = models.Manager()
    # Por defecto django utiliza el primer manager instanciado. Se aplica al
    # admin de django, y no aplica las customizaciones del resto de los
    # managers que se creen.

    objects = DuracionDeLlamadaManager()

    campana = models.ForeignKey('Campana')
    numero_telefono = models.CharField(max_length=20)
    fecha_hora_llamada = models.DateTimeField()
    duracion_en_segundos = models.PositiveIntegerField()
    eventos_del_contacto = models.TextField()


#==============================================================================
# SMSs
#==============================================================================


class OpcionSms(models.Model):
    """
    Representa las posibles respuesta que puede tener una CampanaSms.
    """

    respuesta = models.CharField(max_length=64)
    respuesta_descripcion = models.CharField(
        max_length=100,
        null=True, blank=True,
    )
    campana_sms = models.ForeignKey(
        'CampanaSms',
        related_name='opcionsmss'
    )

    def __unicode__(self):
        return "CampañaSms {0} - Respuesta: {1}".format(
            self.campana_sms,
            self.respuesta,
        )