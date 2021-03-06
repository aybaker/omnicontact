"""ominicontacto URL Configuration
# Copyright (C) 2018 Freetech Solutions

# This file is part of OMniLeads

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.i18n import JavaScriptCatalog
import os

js_info_packages = ('ominicontacto_app',)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('ominicontacto_app.urls')),
    url(r'^', include('reciclado_app.urls')),
    url(r'^', include('reportes_app.urls')),
    url(r'^', include('configuracion_telefonia_app.urls')),
    url(r'^', include('supervision_app.urls')),
    url(r'^', include('api_app.urls')),
    url(r'^accounts/logout/$', auth_views.LogoutView.as_view(next_page='/accounts/login/'),
        name="logout"),
]

for (regex, module) in settings.ADDON_URLPATTERNS:
    urlpatterns += [url(regex, include(module)), ]

urlpatterns += [
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(packages=js_info_packages),
        name='javascript-catalog'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
]

# TODO me funciona con el if de abajo el if de arriba es mas prolijo pero no funciona
# if settings.DEBUG:
if os.getenv('DJANGO_SETTINGS_MODULE') == 'ominicontacto.settings.develop':
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
