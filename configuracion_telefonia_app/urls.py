# -*- coding: utf-8 -*-
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

from django.conf.urls import url

from configuracion_telefonia_app import views
from ominicontacto_app.auth.decorators import (
    administrador_requerido, administrador_o_supervisor_requerido)


urlpatterns = [
    url(r'^configuracion_telefonia/troncal_sip/lista/$',
        administrador_requerido(views.TroncalSIPListView.as_view()),
        name='lista_troncal_sip',
        ),
    url(r'^configuracion_telefonia/troncal_sip/crear/$',
        administrador_requerido(views.TroncalSIPCreateView.as_view()),
        name='crear_troncal_sip',
        ),
    url(r'^configuracion_telefonia/troncal_sip/(?P<pk>\d+)/editar/$',
        administrador_requerido(views.TroncalSIPUpdateView.as_view()),
        name='editar_troncal_sip',
        ),
    url(r'^configuracion_telefonia/troncal_sip/(?P<pk>\d+)/eliminar/$',
        administrador_requerido(views.TroncalSIPDeleteView.as_view()),
        name='eliminar_troncal_sip',
        ),
    url(r'^configuracion_telefonia/ruta_saliente/lista/$',
        administrador_requerido(views.RutaSalienteListView.as_view()),
        name='lista_rutas_salientes',
        ),
    url(r'^configuracion_telefonia/ruta_saliente/crear/$',
        administrador_requerido(views.RutaSalienteCreateView.as_view()),
        name='crear_ruta_saliente',
        ),
    url(r'^configuracion_telefonia/ruta_saliente/(?P<pk>\d+)/editar/$',
        administrador_requerido(views.RutaSalienteUpdateView.as_view()),
        name='editar_ruta_saliente'),
    url(r'^configuracion_telefonia/ruta_saliente/eliminar/(?P<pk>\d+)/$',
        administrador_requerido(views.EliminarRutaSaliente.as_view()),
        name='eliminar_ruta_saliente',
        ),
    url(r'^configuracion_telefonia/ruta_entrante/lista/$',
        administrador_requerido(views.RutaEntranteListView.as_view()),
        name='lista_rutas_entrantes',
        ),
    url(r'^configuracion_telefonia/ruta_entrante/crear/$',
        administrador_requerido(views.RutaEntranteCreateView.as_view()),
        name='crear_ruta_entrante',
        ),
    url(r'^configuracion_telefonia/ruta_entrante/(?P<pk>\d+)/editar/$',
        administrador_requerido(views.RutaEntranteUpdateView.as_view()),
        name='editar_ruta_entrante',
        ),
    url(r'^configuracion_telefonia/ruta_entrante/(?P<pk>\d+)/eliminar/$',
        administrador_requerido(views.RutaEntranteDeleteView.as_view()),
        name='eliminar_ruta_entrante',
        ),
    url(r'^configuracion_telefonia/ruta_entrante/obtener_destinos_tipo/(?P<tipo_destino>\d+)/$',
        administrador_requerido(views.ApiObtenerDestinosEntrantes.as_view()),
        name='obtener_destinos_tipo',
        ),
    url(r'^configuracion_telefonia/ivr/lista/$',
        administrador_requerido(views.IVRListView.as_view()),
        name='lista_ivrs',
        ),
    url(r'^configuracion_telefonia/ivr/crear/$',
        administrador_requerido(views.IVRCreateView.as_view()),
        name='crear_ivr',
        ),
    url(r'^configuracion_telefonia/ivr/content/crear/$',
        administrador_requerido(views.IVRContentCreateView.as_view()),
        name='crear_ivr_content',
        ),
    url(r'^configuracion_telefonia/ivr/(?P<pk>\d+)/editar/$',
        administrador_requerido(views.IVRUpdateView.as_view()),
        name='editar_ivr',
        ),
    url(r'^configuracion_telefonia/ivr/(?P<pk>\d+)/eliminar/$',
        administrador_requerido(views.IVRDeleteView.as_view()),
        name='eliminar_ivr',
        ),
    url(r'^configuracion_telefonia/grupo_horario/lista/$',
        administrador_o_supervisor_requerido(views.GrupoHorarioListView.as_view()),
        name='lista_grupos_horarios',
        ),
    url(r'^configuracion_telefonia/grupo_horario/crear/$',
        administrador_o_supervisor_requerido(views.GrupoHorarioCreateView.as_view()),
        name='crear_grupo_horario',
        ),
    url(r'^configuracion_telefonia/grupo_horario/(?P<pk>\d+)/editar/$',
        administrador_o_supervisor_requerido(views.GrupoHorarioUpdateView.as_view()),
        name='editar_grupo_horario',
        ),
    url(r'^configuracion_telefonia/grupo_horario/(?P<pk>\d+)/eliminar/$',
        administrador_o_supervisor_requerido(views.GrupoHorarioDeleteView.as_view()),
        name='eliminar_grupo_horario',
        ),
    url(r'^configuracion_telefonia/validacion_fecha_hora/lista/$',
        administrador_o_supervisor_requerido(views.ValidacionFechaHoraListView.as_view()),
        name='lista_validaciones_fecha_hora',
        ),
    url(r'^configuracion_telefonia/validacion_fecha_hora/crear/$',
        administrador_o_supervisor_requerido(views.ValidacionFechaHoraCreateView.as_view()),
        name='crear_validacion_fecha_hora',
        ),
    url(r'^configuracion_telefonia/validacion_fecha_hora/(?P<pk>\d+)/editar/$',
        administrador_o_supervisor_requerido(views.ValidacionFechaHoraUpdateView.as_view()),
        name='editar_validacion_fecha_hora',
        ),
    url(r'^configuracion_telefonia/validacion_fecha_hora/(?P<pk>\d+)/eliminar/$',
        administrador_o_supervisor_requerido(views.ValidacionFechaHoraDeleteView.as_view()),
        name='eliminar_validacion_fecha_hora',
        ),
]
