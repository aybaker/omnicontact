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

from django.conf import settings
from django.conf.urls import url, include
from django.views.static import serve
from django.contrib.auth.decorators import login_required

from ominicontacto_app import (
    views, views_base_de_datos_contacto, views_contacto, views_campana_creacion,
    views_grabacion, views_calificacion, views_formulario, views_agente,
    views_calificacion_cliente, views_campana, views_campana_reportes,
    views_agenda_contacto, views_campana_dialer_creacion, views_campana_dialer,
    views_back_list, views_sitio_externo, views_queue_member,
    views_campana_dialer_template, views_campana_manual_creacion, views_campana_manual,
    views_campana_preview, views_archivo_de_audio, views_user_profiles, views_sistema_externo
)

from ominicontacto_app.views_utils import (
    handler400, handler403, handler404, handler500
)

from ominicontacto_app.auth.decorators import (
    administrador_requerido, administrador_o_supervisor_requerido, agente_requerido,
    permiso_administracion_requerido)

handler400 = handler400
handler403 = handler403
handler404 = handler404
handler500 = handler500


urlpatterns = [
    url(r'^admin/defender/', include('defender.urls')),  # defender admin

    # ==========================================================================
    # Base
    # ==========================================================================
    url(r'^$', views.index_view, name='index'),

    url(r'^accounts/login/$', views.login_view, name='login'),

    url(r'^consola/$',
        agente_requerido(views.ConsolaAgenteView.as_view()),
        name='consola_de_agente'),

    url(r'^acerca/$',
        login_required(views.AcercaTemplateView.as_view()),
        name='acerca',
        ),

    url(r'^blanco/$',
        login_required(views.BlancoView.as_view()),
        name='view_blanco'),

    url(r'^registro/$',
        administrador_requerido(views.RegistroFormView.as_view()),
        name='registrar_usuario',
        ),

    # ==========================================================================
    # Usuarios y Perfiles
    # ==========================================================================
    url(r'^user/nuevo/$',
        administrador_o_supervisor_requerido(views_user_profiles.CustomUserFormView.as_view()),
        name='user_nuevo',
        ),
    url(r'^user/list/page(?P<page>[0-9]+)/$',
        administrador_o_supervisor_requerido(views_user_profiles.UserListView.as_view()),
        name='user_list'
        ),
    url(r'^user/delete/(?P<pk>\d+)/$',
        administrador_o_supervisor_requerido(views_user_profiles.UserDeleteView.as_view()),
        name='user_delete',
        ),
    url(r'^user/update/(?P<pk>\d+)/$',
        administrador_o_supervisor_requerido(views_user_profiles.CustomerUserUpdateView.as_view()),
        name='user_update',
        ),
    # Perfil Agente  ==========================================================
    url(r'^agente/list/$',
        administrador_o_supervisor_requerido(views_user_profiles.AgenteListView.as_view()),
        name='agente_list',
        ),
    url(r'^user/agenteprofile/update/(?P<pk_agenteprofile>\d+)/$',
        administrador_requerido(views_user_profiles.AgenteProfileUpdateView.as_view()),
        name='agenteprofile_update',
        ),
    url(r'^agente/(?P<pk_agente>\d+)/activar/$',
        administrador_o_supervisor_requerido(views_user_profiles.ActivarAgenteView.as_view()),
        name="agente_activar"),
    url(r'^agente/(?P<pk_agente>\d+)/desactivar/$',
        administrador_o_supervisor_requerido(views_user_profiles.DesactivarAgenteView.as_view()),
        name="agente_desactivar"),
    # Perfil Supervisor  =======================================================
    url(r'^supervisor/list/$',
        administrador_requerido(views_user_profiles.SupervisorListView.as_view()),
        name='supervisor_list',
        ),
    url(r'^supervisor/(?P<pk>\d+)/update/$',
        administrador_requerido(views_user_profiles.SupervisorProfileUpdateView.as_view()),
        name='supervisor_update',
        ),
    # Perfil Webphone Cliente  ================================================
    url(r'^cliente_webphone/list/$',
        administrador_requerido(views_user_profiles.ClienteWebPhoneListView.as_view()),
        name='cliente_webphone_list',
        ),
    url(r'^agente/(?P<pk>\d+)/cambiar_estado_activacion/$',
        administrador_o_supervisor_requerido(
            views_user_profiles.ToggleActivarClienteWebPhoneView.as_view()),
        name="cliente_webphone_toggle_activacion"),

    # ==========================================================================
    # Grupos
    # ==========================================================================
    url(r'^grupo/list/$',
        administrador_o_supervisor_requerido(views.GrupoListView.as_view()), name='grupo_list',
        ),
    url(r'^grupo/nuevo/$',
        administrador_o_supervisor_requerido(views.GrupoCreateView.as_view()), name='grupo_nuevo',
        ),
    url(r'^grupo/update/(?P<pk>\d+)/$',
        administrador_o_supervisor_requerido(views.GrupoUpdateView.as_view()),
        name='grupo_update',
        ),
    url(r'^grupo/delete/(?P<pk>\d+)/$',
        administrador_o_supervisor_requerido(views.GrupoDeleteView.as_view()),
        name='grupo_delete',
        ),

    # ==========================================================================
    # Pausas
    # ==========================================================================
    url(r'^pausa/list/$',
        administrador_o_supervisor_requerido(views.PausaListView.as_view()),
        name='pausa_list',
        ),
    url(r'^pausa/nuevo/$',
        administrador_o_supervisor_requerido(views.PausaCreateView.as_view()),
        name='pausa_nuevo',
        ),
    url(r'^pausa/update/(?P<pk>\d+)/$',
        administrador_o_supervisor_requerido(views.PausaUpdateView.as_view()),
        name='pausa_update',
        ),
    url(r'^pausa/delete/(?P<pk>\d+)/$',
        administrador_o_supervisor_requerido(views.PausaToggleDeleteView.as_view()),
        name='pausa_delete',
        ),

    # ==========================================================================
    # Grabaciones
    # ==========================================================================
    url(r'^node/grabacion/marcar/$',
        login_required(views_grabacion.MarcarGrabacionView.as_view()),
        name='grabacion_marcar',
        ),
    url(r'^grabacion/descripcion/(?P<callid>[\d .]+)/$',
        login_required(views_grabacion.GrabacionDescripcionView.as_view()),
        name='grabacion_descripcion',
        ),
    url(r'^grabacion/buscar/(?P<pagina>\d+)/$',
        permiso_administracion_requerido(
            views_grabacion.BusquedaGrabacionSupervisorFormView.as_view()),
        name='grabacion_buscar',
        ),
    url(r'^grabacion/agente/buscar/(?P<pagina>\d+)/$',
        agente_requerido(views_grabacion.BusquedaGrabacionAgenteFormView.as_view()),
        name='grabacion_agente_buscar',
        ),

    # ==========================================================================
    # Servicios para phoneJS
    # ==========================================================================
    url(r'^service/campana/activas/$',
        agente_requerido(
            views_agente.CampanasActivasView.as_view()),
        name="service_campanas_activas"),
    url(r'^service/agente/otros_agentes_de_grupo/$',
        agente_requerido(
            views_agente.AgentesDeGrupoPropioView.as_view()),
        name="service_agentes_de_grupo"),

    # ==========================================================================
    # Base Datos Contacto
    # ==========================================================================
    url(r'^base_datos_contacto/$',
        administrador_o_supervisor_requerido(
            views_base_de_datos_contacto.BaseDatosContactoListView.as_view()),
        name='lista_base_datos_contacto',
        ),
    url(r'^base_datos_contacto/nueva/$',
        administrador_o_supervisor_requerido(
            views_base_de_datos_contacto.BaseDatosContactoCreateView.as_view()),
        name='nueva_base_datos_contacto'
        ),
    url(r'^base_datos_contacto/(?P<pk_bd_contacto>\d+)/actualizar/$',
        administrador_o_supervisor_requerido(
            views_base_de_datos_contacto.BaseDatosContactoUpdateView.as_view()),
        name='update_base_datos_contacto'
        ),
    url(r'^base_datos_contacto/(?P<pk>\d+)/validacion/$',
        administrador_o_supervisor_requerido(
            views_base_de_datos_contacto.DefineBaseDatosContactoView.as_view()),
        name='define_base_datos_contacto',
        ),
    url(r'^base_datos_contacto/(?P<bd_contacto>\d+)/agregar/$',
        administrador_o_supervisor_requerido(views_contacto.ContactoBDContactoCreateView.as_view()),
        name='agregar_contacto',
        ),
    url(r'^base_datos_contacto/(?P<pk>\d+)/validacion_actualizacion/$',
        administrador_o_supervisor_requerido(
            views_base_de_datos_contacto.ActualizaBaseDatosContactoView.as_view()),
        name='actualiza_base_datos_contacto',
        ),

    url(r'^base_datos_contacto/(?P<bd_contacto>\d+)/list_contacto/$',
        administrador_o_supervisor_requerido(views_contacto.ContactoBDContactoListView.as_view()),
        name='contacto_list_bd_contacto',
        ),
    url(r'^base_datos_contacto/(?P<pk_contacto>\d+)/update/$',
        administrador_o_supervisor_requerido(views_contacto.ContactoBDContactoUpdateView.as_view()),
        name='actualizar_contacto',
        ),
    url(r'^base_datos_contacto/(?P<pk_contacto>\d+)/eliminar/$',
        administrador_o_supervisor_requerido(views_contacto.ContactoBDContactoDeleteView.as_view()),
        name='eliminar_contacto',
        ),
    url(r'^base_datos_contacto/(?P<bd_contacto>\d+)/ocultar/$',
        administrador_o_supervisor_requerido(
            views_base_de_datos_contacto.OcultarBaseView.as_view()),
        name='oculta_base_dato', ),
    url(r'^base_datos_contacto/(?P<bd_contacto>\d+)/desocultar/$',
        administrador_o_supervisor_requerido(
            views_base_de_datos_contacto.DesOcultarBaseView.as_view()),
        name='desoculta_base_datos', ),
    url(r'^base_datos_contacto/bases_ocultas/$',
        administrador_o_supervisor_requerido(views_base_de_datos_contacto.
                                             mostrar_bases_datos_borradas_ocultas_view),
        name='mostrar_bases_datos_ocultas', ),

    #  ===== Vistas de contacto para agente ====
    url(r'^contacto/list/$',
        agente_requerido(views_contacto.ContactoListView.as_view()),
        name='contacto_list',
        ),
    url(r'^contacto/(?P<pk_contacto>\d+)/update/$',
        agente_requerido(views_contacto.ContactoUpdateView.as_view()),
        name='contacto_update',
        ),

    # ==========================================================================
    #  Vistas de manipulación de contactos de una campaña / Para agente
    # ==========================================================================
    url(r'^campana/selecciona/$',
        agente_requerido(
            views_contacto.FormularioSeleccionCampanaFormView.as_view()),
        name='seleccion_campana_adicion_contacto',
        ),
    url(r'^campana/(?P<pk_campana>\d+)/nuevo_contacto/$',
        agente_requerido(
            views_contacto.FormularioNuevoContactoFormView.as_view()),
        name='nuevo_contacto_campana',
        ),
    url(r'^campana/(?P<pk_campana>\d+)/nuevo_contacto_a_llamar/(?P<telefono>\d+)/$',
        agente_requerido(
            views_contacto.FormularioNuevoContactoFormView.as_view()),
        name='nuevo_contacto_campana_a_llamar', kwargs={'accion': 'llamar'}
        ),
    # TODO: Ver si se usa esa vista para algo
    url(r'^campana/(?P<pk_campana>\d+)/busqueda_contacto/$',
        agente_requerido(
            views_contacto.CampanaBusquedaContactoFormView.as_view()),
        name="campana_busqueda_contacto"),
    url(r'^campana/(?P<pk_campana>\d+)/contactos_telefono_repetido/(?P<telefono>\d+)'
        r'/(?P<call_data_json>.+)$',
        agente_requerido(
            views_contacto.ContactosTelefonosRepetidosView.as_view()),
        name="campana_contactos_telefono_repetido"),

    url(r'^campana/(?P<pk_campana>\d+)/identificar_contacto_a_llamar'
        r'/(?P<telefono>\d+)/$',
        agente_requerido(
            views_contacto.IdentificarContactoView.as_view()),
        name="identificar_contacto_a_llamar"),


    # ==========================================================================
    #  Templates Campana Entrante
    # ==========================================================================
    url(r'^campana_entrante_template/crear/$',
        login_required(
            views_campana_creacion.CampanaEntranteTemplateCreateView.as_view()),
        name="campana_entrante_template_create"),
    url(r'^campana_entrante_template/crear_campana/(?P<pk_campana_template>\d+)$',
        login_required(
            views_campana_creacion.CampanaEntranteTemplateCreateCampanaView.as_view()),
        name="campana_entrante_template_create_campana"),
    url(r'^campana_entrante_template/lista/$',
        login_required(
            views_campana_creacion.CampanaEntranteTemplateListView.as_view()),
        name="campana_entrante_template_list"),
    url(r'^campana_entrante_template/detalle/(?P<pk>\d+)/$',
        login_required(
            views_campana_creacion.CampanaEntranteTemplateDetailView.as_view()),
        name="campana_entrante_template_detail"),
    url(r'^campana_entrante_template/elimina/(?P<pk>\d+)/$',
        login_required(
            views_campana_creacion.CampanaEntranteTemplateDeleteView.as_view()),
        name="campana_entrante_template_delete"),
    # ==========================================================================
    # Vistas varias para Agente: Reportes, logout
    # ==========================================================================
    url(r'^agente/campanas_preview/activas/$',
        agente_requerido(
            views_agente.AgenteCampanasPreviewActivasView.as_view()),
        name="campana_preview_activas_miembro"),
    url(r'^agente/campanas_preview/liberar_contacto_asignado/$',
        agente_requerido(
            views_agente.LiberarContactoAsignado.as_view()),
        name="liberar_contacto_asignado_agente"),
    url(r'^agente/(?P<pk_agente>\d+)/reporte/$',
        agente_requerido(
            views_agente.AgenteReporteCalificaciones.as_view()),
        name='reporte_agente_calificaciones',
        ),
    url(r'^agente/(?P<pk_agente>\d+)/exporta/calificaciones/$',
        agente_requerido(
            views_agente.ExportaReporteCalificacionView.as_view()),
        name='exporta_reporte_calificaciones',
        ),
    url(r'^agente/(?P<pk_agente>\d+)/exporta/formularios/$',
        agente_requerido(
            views_agente.ExportaReporteFormularioVentaView.as_view()),
        name='exporta_reporte_formularios',
        ),
    url(r'^agente/llamar/$',
        agente_requerido(
            views_agente.LlamarContactoView.as_view()),
        name='agente_llamar_contacto',
        ),
    url(r'^agente/llamar_sin_campana/$',
        agente_requerido(
            views_agente.LlamarFueraDeCampanaView.as_view()),
        name='agente_llamar_sin_campana',
        ),
    # ==========================================================================
    # Calificacion
    # ==========================================================================
    url(r'^calificacion/list/$',
        administrador_o_supervisor_requerido(views_calificacion.CalificacionListView.as_view()),
        name='calificacion_list',
        ),
    url(r'^calificacion/nuevo/$',
        administrador_o_supervisor_requerido(
            views_calificacion.CalificacionCreateView.as_view()),
        name='calificacion_nuevo',
        ),
    url(r'^calificacion/update/(?P<pk>\d+)/$',
        administrador_o_supervisor_requerido(views_calificacion.CalificacionUpdateView.as_view()),
        name='calificacion_update',
        ),
    url(r'^calificacion/delete/(?P<pk>\d+)/$',
        administrador_o_supervisor_requerido(views_calificacion.CalificacionDeleteView.as_view()),
        name='calificacion_delete',
        ),

    # ==========================================================================
    # Formulario
    # ==========================================================================
    url(r'^formulario/list/$',
        administrador_o_supervisor_requerido(views_formulario.FormularioListView.as_view()),
        name='formulario_list',
        ),
    url(r'^formulario/list/mostrar_ocultos/$',
        administrador_o_supervisor_requerido(
            views_formulario.FormularioMostrarOcultosView.as_view()),
        name='formulario_list_mostrar_ocultos',
        ),
    url(r'^formulario/nuevo/$',
        administrador_o_supervisor_requerido(views_formulario.FormularioCreateView.as_view()),
        name='formulario_nuevo',
        ),
    url(r'^formulario/(?P<pk_formulario>\d+)/field/$',
        administrador_o_supervisor_requerido(views_formulario.FieldFormularioCreateView.as_view()),
        name='formulario_field',
        ),
    url(r'^formulario/(?P<pk_formulario>\d+)/campo/(?P<pk>\d+)/orden/$',
        administrador_o_supervisor_requerido(views_formulario.FieldFormularioOrdenView.as_view()),
        name='campo_formulario_orden',
        ),
    url(r'^formulario/(?P<pk_formulario>\d+)/campo/(?P<pk>\d+)/delete/$',
        administrador_o_supervisor_requerido(views_formulario.FieldFormularioDeleteView.as_view()),
        name='formulario_field_delete',
        ),
    url(r'^formulario/(?P<pk_formulario>\d+)/vista_previa/$',
        administrador_o_supervisor_requerido(views_formulario.FormularioPreviewFormView.as_view()),
        name='formulario_vista_previa',
        ),

    url(r'^formulario/(?P<pk_formulario>\d+)/eliminar/$',
        administrador_o_supervisor_requerido(views_formulario.FormularioDeleteView.as_view()),
        name='formulario_eliminar',
        ),

    url(r'^formulario/(?P<pk_formulario>\d+)/mostrar_ocultar/$',
        administrador_o_supervisor_requerido(
            views_formulario.FormularioMostrarOcultarView.as_view()),
        name='formulario_mostrar_ocultar',
        ),

    # TODO: Verificar si se usa esta vista.
    # url(r'^formulario/(?P<pk_formulario>\d+)/create/(?P<pk_campana>\d+)/(?P<pk_contacto>\d+)'
    #     r'/(?P<id_agente>\d+)/$',
    #     administrador_o_supervisor_requerido(views_formulario.FormularioCreateFormView.as_view()),
    #     name='formulario_create',
    #     ),

    url(r'^formulario/(?P<pk_formulario>\d+)/vista/$',
        administrador_o_supervisor_requerido(views_formulario.FormularioVistaFormView.as_view()),
        name='formulario_vista',
        ),
    # ==========================================================================
    # Proceso de Calificación
    # CalificacionCliente / Formulario de Calif. de Gestión
    # ==========================================================================
    url(r'^agente/calificar_llamada/(?P<call_data_json>.+)$',
        agente_requerido(views_calificacion_cliente.CalificacionClienteFormView.as_view()),
        kwargs={'from': 'calificacion'},
        name='calificar_llamada'
        ),
    url(r'^agente/calificar_llamada_con_contacto/(?P<pk_contacto>\d+)/(?P<call_data_json>.+)$',
        agente_requerido(views_calificacion_cliente.CalificacionClienteFormView.as_view()),
        kwargs={'from': 'calificacion'},
        name='calificar_llamada_con_contacto'
        ),

    url(r'^formulario/(?P<pk_campana>\d+)/calificacion/(?P<pk_contacto>\d+)'
        '/update_calificacion/$',
        login_required(views_calificacion_cliente.CalificacionClienteFormView.as_view()),
        kwargs={'from': 'calificacion'},
        name='calificacion_formulario_update_or_create'
        ),
    url(r'^formulario/(?P<pk_campana>\d+)/calificacion/(?P<pk_contacto>\d+)'
        '/update_recalificacion/$',
        login_required(views_calificacion_cliente.CalificacionClienteFormView.as_view()),
        kwargs={'from': 'recalificacion'},
        name='recalificacion_formulario_update_or_create'
        ),
    url(r'^formulario/(?P<pk_campana>\d+)/calificacion/(?P<pk_contacto>\d+)'
        '/update_reporte/$',
        login_required(views_calificacion_cliente.CalificacionClienteFormView.as_view()),
        kwargs={'from': 'reporte'},
        name='calificacion_cliente_actualiza_desde_reporte'
        ),

    url(r'^formulario/(?P<pk_campana>\d+)/calificacion/(?P<pk_contacto>\d+)'
        '/auditar_calificacion/$',
        administrador_o_supervisor_requerido(
            views_calificacion_cliente.AuditarCalificacionClienteFormView.as_view()),
        kwargs={'from': 'audita_supervisor'},
        name='auditar_calificacion'
        ),

    # TODO: Una vez que todas las manuales sean click to call ya no existirá esta vista
    # Mientras, quedará para ser usada únicamente en llamadas manuales
    url(r'^formulario/(?P<pk_campana>\d+)/calificacion_create/(?P<telefono>\d+)/$',
        login_required(views_calificacion_cliente.CalificacionClienteFormView.as_view()),
        kwargs={'from': 'calificacion', 'pk_contacto': None, 'manual': True},
        name="calificar_por_telefono"),

    # Respuesta de Formulario para Calificación de Gestión
    url(r'^formulario/venta/(?P<pk>\d+)/detalle/$',
        agente_requerido(
            views_calificacion_cliente.RespuestaFormularioDetailView.as_view()),
        name='formulario_detalle'
        ),
    url(r'^formulario/venta/(?P<pk_calificacion>\d+)/$',
        agente_requerido(
            views_calificacion_cliente.RespuestaFormularioCreateUpdateAgenteFormView.as_view()),
        name='formulario_venta'
        ),
    url(r'^formulario/auditar_venta/(?P<pk_calificacion>\d+)/$',
        administrador_o_supervisor_requerido(
            views_calificacion_cliente.RespuestaFormularioCreateUpdateSupervisorFormView.as_view()),
        name='auditar_formulario_venta'
        ),
    # ==========================================================================
    # Agente
    # ==========================================================================
    url(r'^agente/cambiar_estado/$',
        agente_requerido(views_agente.cambiar_estado_agente_view),
        name='agente_cambiar_estado',
        ),
    # ==========================================================================
    # Supervision
    # ==========================================================================
    # Vistas utilizadas en la supervision PHP.
    # TODO: Mover e implementar mejora en supervision_app o en api_app segun corresponda
    url(r'^llamadas/activas/$',
        administrador_o_supervisor_requerido(views_campana_reportes.LlamadasActivasView.as_view()),
        name='llamadas_activas',
        ),
    url(r'^supervision/agentes/campana/(?P<campana_id>\d+)$',
        administrador_o_supervisor_requerido(views_agente.AgentesLogueadosCampana.as_view()),
        name='supervision_agentes_logueados',
        ),
    # ==========================================================================
    # Agenda Contacto
    # ==========================================================================
    url(r'^agenda_contacto/(?P<pk_contacto>\d+)/create/(?P<pk_campana>\d+)/$',
        agente_requerido(views_agenda_contacto.AgendaContactoCreateView.as_view()),
        name="agenda_contacto_create"),
    url(r'^agenda_contacto/(?P<pk>\d+)/detalle/$',
        login_required(views_agenda_contacto.AgendaContactoDetailView.as_view()),
        name="agenda_contacto_detalle"),
    url(r'^agenda_contacto/eventos/$',
        login_required(views_agenda_contacto.AgendaContactoListFormView.as_view()),
        name="agenda_contacto_listado"),
    # ==========================================================================
    # Campana Dialer
    # ==========================================================================
    url(r'^campana_dialer/list/$',
        permiso_administracion_requerido(views_campana_dialer.CampanaDialerListView.as_view()),
        name="campana_dialer_list"),
    url(r'^campana_dialer/create/$',
        administrador_o_supervisor_requerido(
            views_campana_dialer_creacion.CampanaDialerCreateView.as_view()),
        name="campana_dialer_create"),
    url(r'^campana_dialer/(?P<pk_campana>\d+)/update/$',
        administrador_o_supervisor_requerido(
            views_campana_dialer_creacion.CampanaDialerUpdateView.as_view()),
        name="campana_dialer_update"),
    url(r'^campana_dialer/start/$',
        administrador_o_supervisor_requerido(
            views_campana_dialer.PlayCampanaDialerView.as_view()),
        name='start_campana_dialer'),
    url(r'^campana_dialer/pausar/$',
        administrador_o_supervisor_requerido(
            views_campana_dialer.PausarCampanaDialerView.as_view()),
        name='pausar_campana_dialer'),
    url(r'^campana_dialer/activar/$',
        administrador_o_supervisor_requerido(
            views_campana_dialer.ActivarCampanaDialerView.as_view()),
        name='activar_campana_dialer'),
    url(r'^campana_dialer/(?P<pk_campana>\d+)/delete/$',
        administrador_o_supervisor_requerido(
            views_campana_dialer.CampanaDialerDeleteView.as_view()),
        name="campana_dialer_delete"),
    url(r'^campana_dialer/(?P<pk_campana>\d+)/ocultar/$',
        administrador_o_supervisor_requerido(
            views_campana_dialer.OcultarCampanaDialerView.as_view()),
        name="campana_dialer_ocultar"),
    url(r'^campana_dialer/(?P<pk_campana>\d+)/desocultar/$',
        administrador_o_supervisor_requerido(
            views_campana_dialer.DesOcultarCampanaDialerView.as_view()),
        name="campana_dialer_desocultar"),
    url(r'^campana_dialer/(?P<pk_campana>\d+)/update_base/$',
        administrador_o_supervisor_requerido(
            views_campana_dialer.UpdateBaseDatosDialerView.as_view()),
        name="campana_dialer_update_base"),
    url(r'^campana_dialer/(?P<pk_campana>\d+)/supervisors/$',
        administrador_requerido(
            views_campana_dialer.CampanaDialerSupervisorUpdateView.as_view()),
        name="campana_dialer_supervisors"),
    url(r'^campana_dialer/mostrar_ocultas/$',
        permiso_administracion_requerido(
            views_campana_dialer.CampanaDialerBorradasListView.as_view()),
        name="campana_dialer_mostrar_ocultas"),
    url(r'^campana_dialer/finaliza_actovas/$',
        permiso_administracion_requerido(
            views_campana_dialer.FinalizarCampanasActivasView.as_view()),
        name="campana_dialer_finaliza_activas"),
    # ==========================================================================
    # Campana Manual
    # ==========================================================================
    url(r'^campana_manual/lista/$',
        permiso_administracion_requerido(
            views_campana_manual.CampanaManualListView.as_view()),
        name="campana_manual_list"),
    url(r'^campana_manual/create/$',
        administrador_o_supervisor_requerido(
            views_campana_manual_creacion.CampanaManualCreateView.as_view()),
        name="campana_manual_create"),
    url(r'^campana_manual/(?P<pk_campana>\d+)/update/$',
        administrador_o_supervisor_requerido(
            views_campana_manual_creacion.CampanaManualUpdateView.as_view()),
        name="campana_manual_update"),
    url(r'^campana_manual/(?P<pk_campana>\d+)/delete/$',
        administrador_o_supervisor_requerido(
            views_campana_manual.CampanaManualDeleteView.as_view()),
        name="campana_manual_delete"),
    url(r'^campana_manual/(?P<pk_campana>\d+)/ocultar/$',
        administrador_o_supervisor_requerido(
            views_campana_manual.OcultarCampanaManualView.as_view()),
        name="campana_manual_ocultar"),
    url(r'^campana_manual/(?P<pk_campana>\d+)/desocultar/$',
        administrador_o_supervisor_requerido(
            views_campana_manual.DesOcultarCampanaManualView.as_view()),
        name="campana_manual_desocultar"),
    url(r'^campana_manual/(?P<pk_campana>\d+)/supervisors/$',
        administrador_requerido(
            views_campana_manual.CampanaManualSupervisorUpdateView.as_view()),
        name="campana_manual_supervisors"),
    url(r'^campana_manual/mostrar_ocultas/$',
        permiso_administracion_requerido(
            views_campana_manual.CampanaManualBorradasListView.as_view()),
        name="campana_manual_mostrar_ocultas"),
    # ==========================================================================
    # Campana Preview
    # ==========================================================================
    url(r'^campana_preview/lista/$',
        permiso_administracion_requerido(
            views_campana_preview.CampanaPreviewListView.as_view()),
        name="campana_preview_list"),
    url(r'^campana_preview/create/$',
        administrador_o_supervisor_requerido(
            views_campana_preview.CampanaPreviewCreateView.as_view()),
        name="campana_preview_create"),
    url(r'^campana_preview/(?P<pk_campana>\d+)/update/$',
        administrador_o_supervisor_requerido(
            views_campana_preview.CampanaPreviewUpdateView.as_view()),
        name="campana_preview_update"),
    url(r'^campana_preview/(?P<pk_campana>\d+)/delete/$',
        administrador_o_supervisor_requerido(
            views_campana_preview.CampanaPreviewDeleteView.as_view()),
        name="campana_preview_delete"),
    url(r'^campana_preview/(?P<pk_campana>\d+)/supervisors/$',
        administrador_requerido(
            views_campana_preview.CampanaPreviewSupervisorUpdateView.as_view()),
        name="campana_preview_supervisors"),
    url(r'^campana_preview/mostrar_ocultas/$',
        permiso_administracion_requerido(
            views_campana_preview.CampanaPreviewBorradasListView.as_view()),
        name="campana_preview_mostrar_ocultas"),
    url(r'^campana/mostrar_ocultar/(?P<pk_campana>\d+)/$',
        administrador_o_supervisor_requerido(
            views_campana_preview.campana_mostrar_ocultar_view),
        name="campana_mostrar_ocultar"),
    url(r'^campana_preview/(?P<pk_campana>\d+)/contacto/obtener/$',
        login_required(
            views_campana_preview.ObtenerContactoView.as_view()),
        name="campana_preview_dispatcher"),
    url(r'^campana_preview/validar_contacto_asignado/$',
        login_required(
            views_campana_preview.campana_validar_contacto_asignado_view),
        name="validar_contacto_asignado"),
    url(r'^campana_preview/contactos_asignados/(?P<pk_campana>\d+)/$',
        permiso_administracion_requerido(
            views_campana_preview.CampanaPreviewContactosAsignados.as_view()),
        name="contactos_preview_asignados"),
    url(r'^campana_preview/liberar_contacto_asignado/$',
        administrador_o_supervisor_requerido(
            views_campana_preview.LiberarContactoAsignado.as_view()),
        name="liberar_contacto_asignado"),
    # ==========================================================================
    # Campana Entrante
    # ==========================================================================
    url(r'campana/list/$',
        permiso_administracion_requerido(views_campana.CampanaListView.as_view()),
        name='campana_list',
        ),
    url(r'^campana/nuevo/$',
        administrador_o_supervisor_requerido(
            views_campana_creacion.CampanaEntranteCreateView.as_view()),
        name='campana_nuevo',
        ),
    url(r'^campana/(?P<pk_campana>\d+)/update/$',
        administrador_o_supervisor_requerido(
            views_campana_creacion.CampanaEntranteUpdateView.as_view()),
        name='campana_update',
        ),
    url(r'^campana/elimina/(?P<pk_campana>\d+)/$',
        administrador_o_supervisor_requerido(views_campana.CampanaDeleteView.as_view()),
        name='campana_elimina',
        ),
    url(r'^campana/(?P<pk_campana>\d+)/ocultar/$',
        administrador_o_supervisor_requerido(views_campana.OcultarCampanaView.as_view()),
        name='oculta_campana', ),
    url(r'^campana/(?P<pk_campana>\d+)/desocultar/$',
        administrador_o_supervisor_requerido(views_campana.DesOcultarCampanaView.as_view()),
        name='desoculta_campana', ),
    url(r'^campana/(?P<pk_campana>\d+)/supervisors/$',
        administrador_requerido(
            views_campana.CampanaSupervisorUpdateView.as_view()),
        name="campana_supervisors"),
    url(r'^campana/mostrar_ocultas/$',
        permiso_administracion_requerido(
            views_campana.CampanaBorradasListView.as_view()),
        name="mostrar_campanas_ocultas"),
    # ==========================================================================
    # Blacklist
    # ==========================================================================
    url(r'^backlist/nueva/$',
        administrador_requerido(views_back_list.BacklistCreateView.as_view()),
        name="back_list_create"),
    url(r'^backlist/lista/$',
        administrador_requerido(views_back_list.BackListView.as_view()),
        name="back_list_list"),
    # ==========================================================================
    # Sistema Externo
    # ==========================================================================
    url(r'^sistema_externo/list/$',
        administrador_requerido(views_sistema_externo.SistemaExternoListView.as_view()),
        name="sistema_externo_list"),
    url(r'^sistema_externo/nuevo/$',
        administrador_requerido(views_sistema_externo.SistemaExternoCreateView.as_view()),
        name="sistema_externo_create"),
    url(r'^sistema_externo/(?P<pk>\d+)/update/$',
        administrador_requerido(views_sistema_externo.SistemaExternoUpdateView.as_view()),
        name='modificar_sistema_externo', ),
    # ==========================================================================
    # Sitio Externo
    # ==========================================================================
    url(r'^sitio_externo/list/$',
        administrador_requerido(views_sitio_externo.SitioExternoListView.as_view()),
        name="sitio_externo_list"),
    url(r'^sitio_externo/nuevo/$',
        administrador_requerido(views_sitio_externo.SitioExternoCreateView.as_view()),
        name="sitio_externo_create"),
    url(r'^sitio_externo/(?P<pk_sitio_externo>\d+)/ocultar/$',
        administrador_requerido(views_sitio_externo.OcultarSitioExternoView.as_view()),
        name='oculta_sitio_externo', ),
    url(r'^sitio_externo/(?P<pk_sitio_externo>\d+)/desocultar/$',
        administrador_requerido(
            views_sitio_externo.DesOcultarSitioExternoView.as_view()),
        name='desoculta_sitio_externo', ),
    url(r'^sitio_externo/sitios_ocultos/$',
        administrador_requerido(views_sitio_externo.mostrar_sitio_externos_ocultos_view),
        name='mostrar_sitios_externo_ocultos', ),
    url(r'^sitio_externo/(?P<pk>\d+)/update/$',
        administrador_requerido(views_sitio_externo.SitioExternoUpdateView.as_view()),
        name='modificar_sitio_externo', ),
    url(r'^sitio_externo/(?P<pk>\d+)/delete/$',
        administrador_requerido(views_sitio_externo.SitioExternoDeleteView.as_view()),
        name='sitio_externo_delete'),
    # ==========================================================================
    # QueueMember
    # ==========================================================================
    url(r'^campana/(?P<pk_campana>\d+)/queue_member/$',
        administrador_o_supervisor_requerido(views_queue_member.QueueMemberCreateView.as_view()),
        name='queue_member_add',
        ),
    url(r'^campana/(?P<pk_campana>\d+)/grupo_agente/$',
        administrador_o_supervisor_requerido(views_queue_member.GrupoAgenteCreateView.as_view()),
        name='queue_member_grupo_agente',
        ),
    url(r'^queue_member/(?P<pk_campana>\d+)/queue_member_campana/$',
        administrador_o_supervisor_requerido(views_queue_member.QueueMemberCampanaView.as_view()),
        name='queue_member_campana',
        ),
    url(
        r'^queue_member/(?P<pk_queuemember>\d+)/elimina/(?P<pk_campana>\d+)/$',
        administrador_o_supervisor_requerido(views_queue_member.queue_member_delete_view),
        name='queue_member_elimina',
    ),

    # ==========================================================================
    # Campana Dialer Template
    # ==========================================================================
    url(r'^campana_dialer_template/create/$',
        login_required(
            views_campana_dialer_template.CampanaDialerTemplateCreateView.as_view()),
        name="campana_dialer_template_create"),
    url(r'^campana_dialer_template/lista/$',
        login_required(
            views_campana_dialer_template.TemplateListView.as_view()),
        name="lista_campana_dialer_template"),
    url(r'^campana_dialer_template/(?P<pk_campana_template>\d+)/crea_campana/'
        r'(?P<borrar_template>\d+)/$',
        login_required(
            views_campana_dialer_template.CampanaDialerTemplateCreateCampanaView.as_view()),
        name="crea_campana_dialer_template"),
    url(r'^campana_dialer_template/(?P<pk>\d+)/detalle/$',
        login_required(
            views_campana_dialer_template.TemplateDetailView.as_view()),
        name="campana_dialer_template_detalle"),
    url(r'^campana_dialer_template/(?P<pk_campana>\d+)/elimina/$',
        login_required(
            views_campana_dialer_template.TemplateDeleteView.as_view()),
        name="campana_dialer_template_elimina"),
    # ==========================================================================
    #  Templates Campana Manual
    # ==========================================================================
    url(r'^campana_manual_template/crear/$',
        login_required(
            views_campana_manual_creacion.CampanaManualTemplateCreateView.as_view()),
        name="campana_manual_template_create"),
    url(r'^campana_manual_template/crear_campana/(?P<pk_campana_template>\d+)$',
        login_required(
            views_campana_manual_creacion.CampanaManualTemplateCreateCampanaView.as_view()),
        name="campana_manual_template_create_campana"),
    url(r'^campana_manual_template/lista/$',
        login_required(
            views_campana_manual_creacion.CampanaManualTemplateListView.as_view()),
        name="campana_manual_template_list"),
    url(r'^campana_manual_template/detalle/(?P<pk>\d+)/$',
        login_required(
            views_campana_manual_creacion.CampanaManualTemplateDetailView.as_view()),
        name="campana_manual_template_detail"),
    url(r'^campana_manual_template/elimina/(?P<pk>\d+)/$',
        login_required(
            views_campana_manual_creacion.CampanaManualTemplateDeleteView.as_view()),
        name="campana_manual_template_delete"),
    # ==========================================================================
    #  Templates Campana Preview
    # ==========================================================================
    url(r'^campana_preview_template/crear/$',
        login_required(
            views_campana_preview.CampanaPreviewTemplateCreateView.as_view()),
        name="campana_preview_template_create"),
    url(r'^campana_preview_template/crear_campana/(?P<pk_campana_template>\d+)$',
        login_required(
            views_campana_preview.CampanaPreviewTemplateCreateCampanaView.as_view()),
        name="campana_preview_template_create_campana"),
    url(r'^campana_preview_template/lista/$',
        login_required(
            views_campana_preview.CampanaPreviewTemplateListView.as_view()),
        name="campana_preview_template_list"),
    url(r'^campana_preview_template/detalle/(?P<pk>\d+)/$',
        login_required(
            views_campana_preview.CampanaPreviewTemplateDetailView.as_view()),
        name="campana_preview_template_detail"),
    url(r'^campana_preview_template/elimina/(?P<pk>\d+)/$',
        login_required(
            views_campana_preview.CampanaPreviewTemplateDeleteView.as_view()),
        name="campana_preview_template_delete"),

    # ==========================================================================
    # Archivo de Audio
    # ==========================================================================
    url(r'^audios/$',
        administrador_o_supervisor_requerido(
            views_archivo_de_audio.ArchivoAudioListView.as_view()),
        name='lista_archivo_audio',
        ),
    url(r'^audios/create/$',
        administrador_o_supervisor_requerido(
            views_archivo_de_audio.ArchivoAudioCreateView.as_view()),
        name='create_archivo_audio',
        ),
    url(r'^audios/(?P<pk>\d+)/update/$',
        administrador_o_supervisor_requerido(
            views_archivo_de_audio.ArchivoAudioUpdateView.as_view()),
        name='edita_archivo_audio',
        ),
    url(r'^audios/(?P<pk>\d+)/eliminar/$',
        administrador_o_supervisor_requerido(
            views_archivo_de_audio.ArchivoAudioDeleteView.as_view()),
        name='eliminar_archivo_audio',
        ),


    # ######################
    # DEPRECATED ?
    # ######################

    url(r'^agenda/nuevo/$',
        agente_requerido(views.nuevo_evento_agenda_view),
        name='agenda_nuevo',
        ),
    url(r'^agenda/agente_list/$',
        agente_requerido(views.AgenteEventosFormView.as_view()),
        name='agenda_agente_list',
        ),
    url(r'^chat/mensaje/$',
        login_required(views.mensaje_chat_view),
        name='nueva_mensaje_chat',
        ),
    url(r'^chat/create/$',
        login_required(views.crear_chat_view),
        name='chat_create',
        ),
    # url(r'^ajax/mensaje_recibidos/',
    #     views.mensajes_recibidos_view,
    #     name='ajax_mensaje_recibidos'),
    # url(r'^smsThread/$',
    #     login_required(views.mensajes_recibidos_enviado_remitente_view),
    #     name='view_sms_thread'),
    # url(r'^sms/getAll/$',
    #     login_required(views.mensajes_recibidos_view),
    #     name='view_sms_get_all'),
    # url(r'^user/(?P<username>\w{0,50})/$', views.profile_page,),


]

urlpatterns += [url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}), ]

if settings.DEBUG:
    #     # static files (images, css, javascript, etc.)
    #     urlpatterns += patterns('',
    #         (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
    #             'document_root': settings.MEDIA_ROOT}))

    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
