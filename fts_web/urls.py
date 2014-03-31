# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.views.generic.base import RedirectView
admin.autodiscover()

from fts_web import views

urlpatterns = patterns('',
    url(r'^$',
        RedirectView.as_view(pattern_name='lista_grupo_atencion',
            permanent=False),
    ),
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

    url(r'^lista_contacto/$',
        views.ListaContactoListView.as_view(),
        name='lista_lista_contacto',
    ),
    url(r'^lista_contacto/nueva/$',
        views.ListaContactoCreateUpdateView.as_view(),
        name='nuevo_lista_contacto',
    ),
    url(r'^lista_contacto/(?P<pk>\d+)/$',
        views.ListaContactoCreateUpdateView.as_view(),
        name='edita_lista_contacto',
    ),

    url(r'^admin/', include(admin.site.urls)),
)
