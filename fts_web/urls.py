# -*- coding: utf-8 -*-
#from __future__ import unicode_literals
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

from fts_web import views
print settings
urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'fts_web.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^grupo_atencion/nuevo/$',
        views.GrupoAtencionCreateView.as_view(),
        name='grupo_atencion',
    ),
    url(r'^grupo_atencion/(?P<grupo_atencion_pk>\d+)/$',
        views.GrupoAtencionCreateView.as_view(),
        name='edita_grupo_atencion',
    ),

    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()