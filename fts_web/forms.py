#-*- coding: utf-8 -*-
from django.db.models import get_model
from django import forms
from django.forms.models import inlineformset_factory

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field


GrupoAtencion = get_model('fts_web', 'GrupoAtencion')
AgenteGrupoAtencion = get_model('fts_web', 'AgenteGrupoAtencion')


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

    def clean_nombre(self):
        data = self.cleaned_data['nombre']
        if not data:
            raise forms.ValidationError("Este campo es requerido.")
        return data
