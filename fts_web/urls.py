# -*- coding: utf-8 -*-
#from __future__ import unicode_literals
from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from fts_web import views

urlpatterns = patterns('',
    url(r'^grupo_atencion/$',
        views.GrupoAtencionCreateUpdateView.as_view(),
        name='grupo_atencion',
    ),
    url(r'^grupo_atencion/(?P<pk>\d+)/$',
        views.GrupoAtencionCreateUpdateView.as_view(),
        name='grupo_atencion',
    ),

    url(r'^admin/', include(admin.site.urls)),
)
