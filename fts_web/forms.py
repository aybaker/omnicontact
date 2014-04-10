#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.forms.models import inlineformset_factory

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Submit
from fts_web.models import (
    AgenteGrupoAtencion, Campana, GrupoAtencion,
    BaseDatosContacto, Opcion,
)


#===============================================================================
# Grupos de Atención
#===============================================================================

class AgenteGrupoAtencionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('numero_interno'),
        )
        super(AgenteGrupoAtencionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = GrupoAtencion
        exclude = ('grupo_atencion',)
        labels = {
            'numero_interno': '',
        }

AgentesGrupoAtencionFormSet = inlineformset_factory(
    GrupoAtencion, AgenteGrupoAtencion,
    form=AgenteGrupoAtencionForm,
    extra=1,
)


class GrupoAtencionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('nombre'),
            Field('timeout'),
            Field('ring_strategy'),
        )
        super(GrupoAtencionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = GrupoAtencion


#===============================================================================
# Base Datos Contactos
#===============================================================================

class BaseDatosContactoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('nombre'),
        )
        super(BaseDatosContactoForm, self).__init__(*args, **kwargs)

    class Meta:
        model = BaseDatosContacto


#===============================================================================
# Campaña
#===============================================================================

class CampanaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('nombre'),
            Field('reproduccion'),
            Field('bd_contacto')
        )
        super(CampanaForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Campana
        exclude = ('estado', 'fecha_inicio', 'fecha_fin')


class ConfirmaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.add_input(
            Submit('confirma', 'Confirmar Nueva Campaña')
        )
        # self.helper.add_input(
        #     Submit('cancela', 'Cancelar', css_class='btn-danger')
        # )
        super(ConfirmaForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Campana
        fields = ()


#===============================================================================
# Opciones
#===============================================================================

class OpcionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('digito'),
            Field('accion'),
            Field('grupo_atencion'),
            Field('campana', type="hidden"),
        )
        super(OpcionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Opcion


#===============================================================================
# Formulario File
#===============================================================================

class FileForm(forms.Form):
    file = forms.FileField(
        label="Seleccione el archivo",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('file'),
        )
        super(FileForm, self).__init__(*args, **kwargs)
