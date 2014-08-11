# -*- coding: utf-8 -*-

"""
Mapeos de URLs para la aplicación
"""

from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
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
        views.AcercaTemplateView.as_view(),
        name='acerca',
    ),

    #==========================================================================
    # Derivación
    #==========================================================================
    url(r'^derivacion/$',
        views.DerivacionListView.as_view(),
        name='lista_derivacion',
    ),

    url(r'^derivacion_externa/nueva/$',
        views.DerivacionExternaCreateView.as_view(),
        name='nueva_derivacion_externa',
    ),
    url(r'^derivacion_externa/(?P<pk>\d+)/$',
        views.DerivacionExternaUpdateView.as_view(),
        name='edita_derivacion_externa',
    ),
    url(r'^derivacion_externa/(?P<pk>\d+)/elimina/$',
        views.DerivacionExternaDeleteView.as_view(),
        name='derivacion_externa_elimina',
    ),

    url(r'^grupo_atencion/nuevo/$',
        views.GrupoAtencionCreateView.as_view(),
        name='nuevo_grupo_atencion',
    ),
    url(r'^grupo_atencion/(?P<pk>\d+)/$',
        views.GrupoAtencionUpdateView.as_view(),
        name='edita_grupo_atencion',
    ),
    url(r'^grupo_atencion/(?P<pk>\d+)/elimina/$',
        views.GrupoAtencionDeleteView.as_view(),
        name='grupo_atencion_elimina',
    ),

    #==========================================================================
    # Base Datos Contacto
    #==========================================================================
    url(r'^base_datos_contacto/$',
        views.BaseDatosContactoListView.as_view(),
        name='lista_base_datos_contacto',
    ),
    url(r'^base_datos_contacto/nueva/$',
        views.BaseDatosContactoCreateView.as_view(),
        name='nueva_base_datos_contacto',
    ),
    url(r'^base_datos_contacto/(?P<pk>\d+)/validacion/$',
        views.DefineBaseDatosContactoView.as_view(),
        name='define_base_datos_contacto',
    ),
    url(r'^base_datos_contacto/(?P<pk>\d+)/depurar/$',
        views.DepuraBaseDatosContactoView.as_view(),
        name='depurar_base_datos_contacto',
    ),

    #==========================================================================
    # Template
    #==========================================================================
    # url(r'^campanas/$',
    #     views.CampanaListView.as_view(),
    #     name='lista_campana',
    # ),
    # url(r'^campana/(?P<pk>\d+)/$',
    #     views.DetalleCampanView.as_view(),
    #     name='detalle_campana',
    # ),
    url(r'^template/nuevo_template/$',
        views.TemplateCreateView.as_view(),
        name='nuevo_template',
    ),
    # url(r'^campana/(?P<pk>\d+)/elimina/$',
    #     views.CampanaDeleteView.as_view(),
    #     name='campana_elimina',
    # ),
    url(r'^template/(?P<pk>\d+)/datos_basicos/$',
        views.TemplateaUpdateView.as_view(),
        name='datos_basicos_template',
    ),
    url(r'^template/(?P<pk>\d+)/audio/$',
        views.AudioTemplateCreateView.as_view(),
        name='audio_template',
    ),
    url(r'^template/(?P<pk>\d+)/calificaciones/$',
        views.CalificacionTemplateCreateView.as_view(),
        name='calificacion_template',
    ),
    url(r'^template/calificacion/(?P<pk>\d+)/elimina/$',
        views.CalificacionTemplateDeleteView.as_view(),
        name='calificacion_template_elimina',
    ),
    url(r'^template/(?P<pk>\d+)/opciones/$',
        views.OpcionTemplateCreateView.as_view(),
        name='opcion_template',
    ),
    url(r'^template/opcion/(?P<pk>\d+)/elimina/$',
        views.OpcionTemplateDeleteView.as_view(),
        name='opcion_template_elimina',
    ),
    url(r'^template/(?P<pk>\d+)/actuacion/$',
        views.ActuacionTemplateCreateView.as_view(),
        name='actuacion_template',
    ),
    url(r'^template/actuacion/(?P<pk>\d+)/elimina/$',
        views.ActuacionTemplateDeleteView.as_view(),
        name='actuacion_template_elimina',
    ),
    url(r'^template/(?P<pk>\d+)/confirma/$',
        views.ConfirmaTemplateView.as_view(),
        name='confirma_template',
    ),

    #==========================================================================
    # Campaña
    #==========================================================================
    url(r'^campanas/$',
        views.CampanaListView.as_view(),
        name='lista_campana',
    ),
    url(r'^campana/(?P<pk>\d+)/$',
        views.DetalleCampanView.as_view(),
        name='detalle_campana',
    ),
    url(r'^campana/nueva_campana/$',
        views.CampanaCreateView.as_view(),
        name='nueva_campana',
    ),
    url(r'^campana/(?P<pk>\d+)/elimina/$',
        views.CampanaDeleteView.as_view(),
        name='campana_elimina',
    ),
    url(r'^campana/(?P<pk>\d+)/datos_basicos/$',
        views.CampanaUpdateView.as_view(),
        name='datos_basicos_campana',
    ),
    url(r'^campana/(?P<pk>\d+)/audio/$',
        views.AudioCampanaCreateView.as_view(),
        name='audio_campana',
    ),
    url(r'^campana/(?P<pk>\d+)/calificaciones/$',
        views.CalificacionCampanaCreateView.as_view(),
        name='calificacion_campana',
    ),
    url(r'^campana/calificacion/(?P<pk>\d+)/elimina/$',
        views.CalificacionCampanaDeleteView.as_view(),
        name='calificacion_campana_elimina',
    ),
    url(r'^campana/(?P<pk>\d+)/opciones/$',
        views.OpcionCampanaCreateView.as_view(),
        name='opcion_campana',
    ),
    url(r'^campana/opcion/(?P<pk>\d+)/elimina/$',
        views.OpcionCampanaDeleteView.as_view(),
        name='opcion_campana_elimina',
    ),
    url(r'^campana/(?P<pk>\d+)/actuacion/$',
        views.ActuacionCampanaCreateView.as_view(),
        name='actuacion_campana',
    ),
    url(r'^campana/actuacion/(?P<pk>\d+)/elimina/$',
        views.ActuacionCampanaDeleteView.as_view(),
        name='actuacion_campana_elimina',
    ),
    url(r'^campana/(?P<pk>\d+)/confirma/$',
        views.ConfirmaCampanaView.as_view(),
        name='confirma_campana',
    ),
    url(r'^campana/estado/finaliza/$',
        views.FinalizaCampanaView.as_view(),
        name='estado_finaliza_campana',
    ),
    url(r'^campana/estado/pausa/$',
        views.PausaCampanaView.as_view(),
        name='estado_pausa_campana',
    ),
    url(r'^campana/estado/activa/$',
        views.ActivaCampanaView.as_view(),
        name='estado_activa_campana',
    ),

    #Reciclado
    url(r'^campana/(?P<pk>\d+)/recicla/tipo/$',
        views.TipoRecicladoCampanaView.as_view(),
        name='tipo_reciclado_campana',
    ),
    url(r'^campana/(?P<pk>\d+)/recicla/redefinicion/$',
        views.RedefinicionRecicladoCampanaView.as_view(),
        name='redefinicion_reciclado_campana',
    ),
    url(r'^campana/(?P<pk>\d+)/recicla/actuacion/$',
        views.ActuacionRecicladoCampanaView.as_view(),
        name='actuacion_reciclado_campana',
    ),
    url(r'^campana/recicla/actuacion/(?P<pk>\d+)/elimina/$',
        views.ActuacionRecicladoCampanaDeleteView.as_view(),
        name='actuacion_reciclado_campana_elimina',
    ),
    url(r'^campana/(?P<pk>\d+)/recicla/confirma/$',
        views.ConfirmaRecicladoCampanaView.as_view(),
        name='confirma_reciclado_campana',
    ),

    # Supervisión
    url(r'^campanas/estados/$',
        views.CampanaPorEstadoListView.as_view(),
        name='lista_campana_por_estados',
    ),
    url(r'^campana/(?P<pk>\d+)/detalle_estado_opciones/$',
        views.CampanaEstadoOpcionesDetailView.as_view(),
        name='detalle_estado_opciones',
    ),

    # Reportes
    url(r'^campanas/reportes/$',
        views.CampanaReporteListView.as_view(),
        name='lista_campana_reportes',
    ),
    url(r'^campana/(?P<pk>\d+)/detalle_reporte/$',
        views.CampanaReporteDetailView.as_view(),
        name='detalle_campana_reporte',
    ),
    url(r'^campana/(?P<pk>\d+)/exporta/$',
        views.ExportaReporteCampanaView.as_view(),
        name='exporta_campana_reporte',
    ),

    #==========================================================================
    # Vistas para estadisticas
    #==========================================================================
    url(r'^daemon/status/',
        views.DaemonStatusView.as_view(),
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
