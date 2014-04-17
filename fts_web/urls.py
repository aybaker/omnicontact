# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings

from django.contrib import admin
from django.views.generic.base import RedirectView
admin.autodiscover()

from fts_web import views

urlpatterns = patterns('',
    url(r'^$',
        RedirectView.as_view(pattern_name='lista_campana_por_estados',
            permanent=False),
    ),

    #===============================================================================
    # Grupo Atención
    #===============================================================================
    url(r'^grupo_atencion/$',
        views.GrupoAtencionListView.as_view(),
        name='lista_grupo_atencion',
    ),
    url(r'^grupo_atencion/nuevo/$',
        views.GrupoAtencionCreateView.as_view(),
        name='nuevo_grupo_atencion',
    ),
    # url(r'^grupo_atencion/(?P<pk>\d+)/$',
    #     views.GrupoAtencionUpdateView.as_view(),
    #     name='edita_grupo_atencion',
    # ),
    # url(r'^grupo_atencion/elimina/(?P<pk>\d+)/$',
    #     views.GrupoAtencionDeleteView.as_view(),
    #     name='elimina_grupo_atencion',
    # ),

    #===============================================================================
    # Base Datos Contacto
    #===============================================================================
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

    #===============================================================================
    # Campaña
    #===============================================================================
    url(r'^campanas/$',
        views.CampanaListView.as_view(),
        name='lista_campana',
    ),
    url(r'^campana/datos_basicos/$',
        views.CampanaCreateView.as_view(),
        name='nueva_campana',
    ),
    url(r'^campana/(?P<pk>\d+)/calificaciones/$',
        views.CalificacionCampanaCreateView.as_view(),
        name='calificacion_campana',
    ),
    url(r'^campana/(?P<pk>\d+)/opciones/$',
        views.OpcionCampanaCreateView.as_view(),
        name='opcion_campana',
    ),
    url(r'^campana/(?P<pk>\d+)/actuacion/$',
        views.ActuacionCampanaCreateView.as_view(),
        name='actuacion_campana',
    ),
    url(r'^campana/(?P<pk>\d+)/confirma/$',
        views.ConfirmaCampanaView.as_view(),
        name='confirma_campana',
    ),
    url(r'^campana/(?P<pk>\d+)/estado/pausa/$',
        views.PausaCampanaView.as_view(),
        name='estado_pausa_campana',
    ),
    url(r'^campana/(?P<pk>\d+)/estado/activa/$',
        views.ActivaCampanaView.as_view(),
        name='estado_activa_campana',
    ),
    url(r'^campanas/estados/$',
        views.CampanaPorEstadoListView.as_view(),
        name='lista_campana_por_estados',
    ),

    url(r'^campana/(?P<pk>\d+)/detalle_estado/$',
        views.CampanaPorEstadoDetailView.as_view(),
        name='campana_detalle_de_estado',
    ),

    #===============================================================================
    # AGI
    #===============================================================================
    url(r'^_/agi/contesto/(?P<call_id>\d+)/$',
        views.registar_llamada_contestada,
        name='registar_llamada_contestada',
    ),

    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG and settings.FTS_ENHANCED_URLS:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
