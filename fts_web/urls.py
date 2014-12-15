# -*- coding: utf-8 -*-

"""
Mapeos de URLs para la aplicación
"""

from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.contrib import admin
from django.views.generic.base import RedirectView
from fts_web import views


admin.autodiscover()


urlpatterns = patterns('',
    url(r'^$',
        RedirectView.as_view(pattern_name='lista_campana_por_estados',
            permanent=False),
    ),

    #==========================================================================
    # Acerca
    #==========================================================================
    url(r'^acerca/$',
        login_required(views.AcercaTemplateView.as_view()),
        name='acerca',
    ),

    #==========================================================================
    # Derivación
    #==========================================================================
    url(r'^derivacion/$',
        login_required(views.DerivacionListView.as_view()),
        name='lista_derivacion',
    ),
    url(r'^derivacion_externa/nueva/$',
        login_required(views.DerivacionExternaCreateView.as_view()),
        name='nueva_derivacion_externa',
    ),
    url(r'^derivacion_externa/(?P<pk>\d+)/$',
        login_required(views.DerivacionExternaUpdateView.as_view()),
        name='edita_derivacion_externa',
    ),
    url(r'^derivacion_externa/(?P<pk>\d+)/elimina/$',
        login_required(views.DerivacionExternaDeleteView.as_view()),
        name='derivacion_externa_elimina',
    ),
    url(r'^grupo_atencion/nuevo/$',
        login_required(views.GrupoAtencionCreateView.as_view()),
        name='nuevo_grupo_atencion',
    ),
    url(r'^grupo_atencion/(?P<pk>\d+)/$',
        login_required(views.GrupoAtencionUpdateView.as_view()),
        name='edita_grupo_atencion',
    ),
    url(r'^grupo_atencion/(?P<pk>\d+)/elimina/$',
        login_required(views.GrupoAtencionDeleteView.as_view()),
        name='grupo_atencion_elimina',
    ),

    #==========================================================================
    # Base Datos Contacto
    #==========================================================================
    url(r'^base_datos_contacto/$',
        login_required(views.BaseDatosContactoListView.as_view()),
        name='lista_base_datos_contacto',
    ),
    url(r'^base_datos_contacto/nueva/$',
        login_required(views.BaseDatosContactoCreateView.as_view()),
        name='nueva_base_datos_contacto',
    ),
    url(r'^base_datos_contacto/(?P<pk>\d+)/validacion/$',
        login_required(views.DefineBaseDatosContactoView.as_view()),
        name='define_base_datos_contacto',
    ),
    url(r'^base_datos_contacto/(?P<pk>\d+)/depurar/$',
        login_required(views.DepuraBaseDatosContactoView.as_view()),
        name='depurar_base_datos_contacto',
    ),

    #==========================================================================
    # Template
    #==========================================================================
    url(r'^templates/$',
        login_required(views.TemplateListView.as_view()),
        name='lista_template',
    ),
    url(r'^template/(?P<pk_campana>\d+)/$',
        login_required(views.DetalleTemplateView.as_view()),
        name='detalle_template',
    ),
    url(r'^template/nuevo_template/$',
        login_required(views.TemplateCreateView.as_view()),
        name='nuevo_template',
    ),
    url(r'^template/(?P<pk_campana>\d+)/elimina/$',
        login_required(views.TemplateDeleteView.as_view()),
        name='template_elimina',
    ),
    url(r'^template/(?P<pk_campana>\d+)/datos_basicos/$',
        login_required(views.TemplateaUpdateView.as_view()),
        name='datos_basicos_template',
    ),
    url(r'^template/(?P<pk_campana>\d+)/audios/$',
        login_required(views.AudioTemplateCreateView.as_view()),
        name='audio_template',
    ),
    url(r'^template/(?P<pk_campana>\d+)/audio/(?P<pk>\d+)/orden/$',
        login_required(views.AudioTemplateOrdenView.as_view()),
        name='audio_template_orden',
    ),
    url(r'^template/(?P<pk_campana>\d+)/audios/(?P<pk>\d+)/elimina/$',
        login_required(views.AudiosTemplateDeleteView.as_view()),
        name='audios_template_elimina',
    ),
    url(r'^template/(?P<pk_campana>\d+)/calificaciones/$',
        login_required(views.CalificacionTemplateCreateView.as_view()),
        name='calificacion_template',
    ),
    url(r'^template/(?P<pk_campana>\d+)/calificacion/(?P<pk>\d+)/elimina/$',
        login_required(views.CalificacionTemplateDeleteView.as_view()),
        name='calificacion_template_elimina',
    ),
    url(r'^template/(?P<pk_campana>\d+)/opciones/$',
        login_required(views.OpcionTemplateCreateView.as_view()),
        name='opcion_template',
    ),
    url(r'^template/(?P<pk_campana>\d+)/opcion/(?P<pk>\d+)/elimina/$',
        login_required(views.OpcionTemplateDeleteView.as_view()),
        name='opcion_template_elimina',
    ),
    url(r'^template/(?P<pk_campana>\d+)/actuacion/$',
        login_required(views.ActuacionTemplateCreateView.as_view()),
        name='actuacion_template',
    ),
    url(r'^template/(?P<pk_campana>\d+)/actuacion/(?P<pk>\d+)/elimina/$',
        login_required(views.ActuacionTemplateDeleteView.as_view()),
        name='actuacion_template_elimina',
    ),
    url(r'^template/(?P<pk_campana>\d+)/confirma/$',
        login_required(views.ConfirmaTemplateView.as_view()),
        name='confirma_template',
    ),
    url(r'^template/(?P<pk_campana>\d+)/crea_campana/$',
        login_required(views.CreaCampanaTemplateView.as_view()),
        name='crea_campana_template',
    ),


    #==========================================================================
    # CampañaSMS
    #==========================================================================
#     url(r'^campanas/$',
#         login_required(views.CampanaListView.as_view()),
#         name='lista_campana',
#     ),
#     url(r'^campana/(?P<pk_campana>\d+)/$',
#         login_required(views.DetalleCampanView.as_view()),
#         name='detalle_campana',
#     ),
    url(r'^campana_sms/nueva_campana_sms/$',
        login_required(views.CampanaSmsCreateView.as_view()),
        name='nueva_campana_sms',
    ),
#     url(r'^campana/(?P<pk_campana>\d+)/elimina/$',
#         login_required(views.CampanaDeleteView.as_view()),
#         name='campana_elimina',
#     ),
    url(r'^campana_sms/(?P<pk_campana_sms>\d+)/datos_basicos/$',
        login_required(views.CampanaSmsUpdateView.as_view()),
        name='datos_basicos_campana_sms',
    ),
    url(r'^campana_sms/(?P<pk_campana_sms>\d+)/cuerpo_mensaje/$',
        login_required(views.TemplateMensajeCampanaSmsUpdateView.as_view()),
        name='template_mensaje_campana_sms',
    ),
    url(r'^campana_sms/(?P<pk_campana_sms>\d+)/respuestas/$',
        login_required(views.OpcionSmsCampanaSmsCreateView.as_view()),
        name='opcion_sms_campana_sms',
    ),
    url(r'^campana_sms/(?P<pk_campana_sms>\d+)/respuesta/(?P<pk>\d+)/elimina/$',
        login_required(views.OpcionSmsCampanaSmsDeleteView.as_view()),
        name='opcion_sms_campana_sms_elimina',
    ),
    url(r'^campana_sms/(?P<pk_campana_sms>\d+)/actuacion/$',
        login_required(views.ActuacionSmsCampanaSmsCreateView.as_view()),
        name='actuacion_sms_campana_sms',
    ),
    url(r'^campana_sms/(?P<pk_campana_sms>\d+)/actuacion/(?P<pk>\d+)/elimina/$',
        login_required(views.ActuacionSmsCampanaSmsDeleteView.as_view()),
        name='actuacion_sms_campana_sms_elimina',
    ),
#     url(r'^campana/(?P<pk_campana>\d+)/confirma/$',
#         login_required(views.ConfirmaCampanaView.as_view()),
#         name='confirma_campana',
#     ),





    #==========================================================================
    # Campaña
    #==========================================================================
    url(r'^campanas/$',
        login_required(views.CampanaListView.as_view()),
        name='lista_campana',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/$',
        login_required(views.DetalleCampanView.as_view()),
        name='detalle_campana',
    ),
    url(r'^campana/nueva_campana/$',
        login_required(views.CampanaCreateView.as_view()),
        name='nueva_campana',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/elimina/$',
        login_required(views.CampanaDeleteView.as_view()),
        name='campana_elimina',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/datos_basicos/$',
        login_required(views.CampanaUpdateView.as_view()),
        name='datos_basicos_campana',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/audios/$',
        login_required(views.AudioCampanaCreateView.as_view()),
        name='audio_campana',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/audio/(?P<pk>\d+)/orden/$',
        login_required(views.AudioCampanaOrdenView.as_view()),
        name='audio_campana_orden',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/audio/(?P<pk>\d+)/elimina/$',
        login_required(views.AudiosCampanaDeleteView.as_view()),
        name='audios_campana_elimina',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/calificaciones/$',
        login_required(views.CalificacionCampanaCreateView.as_view()),
        name='calificacion_campana',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/calificacion/(?P<pk>\d+)/elimina/$',
        login_required(views.CalificacionCampanaDeleteView.as_view()),
        name='calificacion_campana_elimina',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/opciones/$',
        login_required(views.OpcionCampanaCreateView.as_view()),
        name='opcion_campana',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/opcion/(?P<pk>\d+)/elimina/$',
        login_required(views.OpcionCampanaDeleteView.as_view()),
        name='opcion_campana_elimina',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/actuacion/$',
        login_required(views.ActuacionCampanaCreateView.as_view()),
        name='actuacion_campana',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/actuacion/(?P<pk>\d+)/elimina/$',
        login_required(views.ActuacionCampanaDeleteView.as_view()),
        name='actuacion_campana_elimina',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/confirma/$',
        login_required(views.ConfirmaCampanaView.as_view()),
        name='confirma_campana',
    ),
    url(r'^campana/estado/finaliza/$',
        login_required(views.FinalizaCampanaView.as_view()),
        name='estado_finaliza_campana',
    ),
    url(r'^campana/estado/pausa/$',
        login_required(views.PausaCampanaView.as_view()),
        name='estado_pausa_campana',
    ),
    url(r'^campana/estado/activa/$',
        login_required(views.ActivaCampanaView.as_view()),
        name='estado_activa_campana',
    ),

    #Reciclado
    url(r'^campana/(?P<pk_campana>\d+)/recicla/tipo/$',
        login_required(views.TipoRecicladoCampanaView.as_view()),
        name='tipo_reciclado_campana',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/recicla/redefinicion/$',
        login_required(views.RedefinicionRecicladoCampanaView.as_view()),
        name='redefinicion_reciclado_campana',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/recicla/actuacion/$',
        login_required(views.ActuacionRecicladoCampanaView.as_view()),
        name='actuacion_reciclado_campana',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/recicla/actuacion/(?P<pk>\d+)/elimina/$',
        login_required(views.ActuacionRecicladoCampanaDeleteView.as_view()),
        name='actuacion_reciclado_campana_elimina',
    ),
    url(r'^campana/(?P<pk_campana>\d+)/recicla/confirma/$',
        login_required(views.ConfirmaRecicladoCampanaView.as_view()),
        name='confirma_reciclado_campana',
    ),

    # Supervisión
    url(r'^campanas/estados/$',
        login_required(views.CampanaPorEstadoListView.as_view()),
        name='lista_campana_por_estados',
    ),
    url(r'^campana/(?P<pk>\d+)/detalle_estado_opciones/$',
        login_required(views.CampanaEstadoOpcionesDetailView.as_view()),
        name='detalle_estado_opciones',
    ),

    # Reportes
    url(r'^campanas/reportes/$',
        login_required(views.CampanaReporteListView.as_view()),
        name='lista_campana_reportes',
    ),
    url(r'^campana/(?P<pk>\d+)/detalle_reporte/$',
        login_required(views.CampanaReporteDetailView.as_view()),
        name='detalle_campana_reporte',
    ),
    url(r'^campana/(?P<pk>\d+)/exporta/$',
        login_required(views.ExportaReporteCampanaView.as_view()),
        name='exporta_campana_reporte',
    ),

    # Nuevas url de gráficos de reportes
    url(r'^campana/(?P<pk>\d+)/grafico/duracion_de_llamada$',
        login_required(views.CreaGraficoDeDuracionDeLlamada.as_view()),
        name='grafico_de_duracion_de_llamada',
    ),


    #==========================================================================
    # Búsqueda de Llamadas
    #==========================================================================
    url(r'^busqueda/llamadas$',
        login_required(views.BusquedaDeLlamadasView.as_view()),
        name='busqueda_de_llamadas',
    ),

    #==========================================================================
    # Archivo de Audio
    #==========================================================================
    url(r'^audios/$',
        login_required(views.ArchivoAudioListView.as_view()),
        name='lista_archivo_audio',
    ),
    url(r'^audios/nuevo/$',
        login_required(views.ArchivoAudioCreateView.as_view()),
        name='nuevo_archivo_audio',
    ),
    url(r'^audios/(?P<pk>\d+)/$',
        login_required(views.ArchivoAudioUpdateView.as_view()),
        name='edita_archivo_audio',
    ),
    url(r'^audios/(?P<pk>\d+)/elimina/$',
        login_required(views.ArchivoAudioDeleteView.as_view()),
        name='elimina_archivo_audio',
    ),

    #==========================================================================
    # Vistas para estadisticas
    #==========================================================================
    url(r'^daemon/status/',
        login_required(views.DaemonStatusView.as_view()),
        name='daemon_status'
    ),

    #==========================================================================
    # Vistas para pruebas
    #==========================================================================
    url(r'^test/view/exception/', 'fts_web.views.test_view_exception'),


    #==========================================================================
    # Logueo, Deslogueo
    #==========================================================================
    url(r'^logueo/$',
        'django.contrib.auth.views.login',
        {'template_name': 'logueo.html'},
        name="logueo"
    ),
    url(r'^deslogueo/$',
        'django.contrib.auth.views.logout',
        {'next_page': '/logueo'},
        name="deslogueo"
    ),


    #==========================================================================
    # admin
    #==========================================================================
    url(r'^ftsenderweb/', include(admin.site.urls)),

)

if settings.DEBUG and settings.FTS_ENHANCED_URLS:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

if settings.FTS_TESTING_MODE:
    urlpatterns += patterns('',
        url(r'^asterisk-ami-http/simulador', 'fts_tests.views.simulador'),
        url(r'^asterisk-ami-http/(?P<code>.+)/mxml', 'fts_tests.views.mxml'),
    )
