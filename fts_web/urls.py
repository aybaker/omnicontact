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
        RedirectView.as_view(pattern_name='lista_grupo_atencion',
            permanent=False),
    ),

    #===============================================================================
    # Grupo Atención
    #===============================================================================
    url(r'^grupo_atencion/$',
        views.GrupoAtencionListView.as_view(),
        name='lista_grupo_atencion',
    ),
    url(r'^grupo_atencion/nuevo$',
        views.GrupoAtencionCreateView.as_view(),
        name='nuevo_grupo_atencion',
    ),
    url(r'^grupo_atencion/(?P<pk>\d+)/$',
        views.GrupoAtencionUpdateView.as_view(),
        name='edita_grupo_atencion',
    ),
    url(r'^grupo_atencion/elimina/(?P<pk>\d+)/$',
        views.GrupoAtencionDeleteView.as_view(),
        name='elimina_grupo_atencion',
    ),

    #===============================================================================
    # Lista Contacto
    #===============================================================================
    url(r'^lista_contacto/$',
        views.ListaContactoListView.as_view(),
        name='lista_lista_contacto',
    ),
    url(r'^lista_contacto/nueva/$',
        views.ListaContactoCreateView.as_view(),
        name='nueva_lista_contacto',
    ),
    url(r'^lista_contacto/(?P<pk>\d+)/$',
        views.ListaContactoUpdateView.as_view(),
        name='edita_lista_contacto',
    ),

    #===============================================================================
    # Campaña
    #===============================================================================
    url(r'^campanas/$',
        views.CampanaListView.as_view(),
        name='lista_campana',
    ),
    url(r'^campana/nueva/$',
        views.CampanaCreateView.as_view(),
        name='nueva_campana',
    ),
    url(r'^campana/(?P<pk>\d+)/$',
        views.CampanaUpdateView.as_view(),
        name='edita_campana',
    ),
    url(r'^campana/confirma/(?P<pk>\d+)/$',
        views.ConfirmaCampanaView.as_view(),
        name='confirma_campana',
    ),


    url(r'^admin/', include(admin.site.urls)),
)