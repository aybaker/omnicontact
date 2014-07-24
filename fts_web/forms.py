#-*- coding: utf-8 -*-

"""
Formularios de Django
"""

from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Submit, Div

from bootstrap3_datetime.widgets import DateTimePicker

from fts_web.models import (
    Actuacion, AgenteGrupoAtencion, BaseDatosContacto,
    Campana, Calificacion, GrupoAtencion, Opcion
)


#=========================================================================
# Grupos de Atención
#=========================================================================

class AgenteGrupoAtencionForm(forms.ModelForm):

    class Meta:
        model = GrupoAtencion
        exclude = ('grupo_atencion',)
        labels = {
            'numero_interno': '',
        }


class BaseAgenteGrupoAtencionFormset(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(BaseAgenteGrupoAtencionFormset, self).__init__(*args, **kwargs)
        self.forms[0].empty_permitted = False

AgentesGrupoAtencionFormSet = inlineformset_factory(
    GrupoAtencion, AgenteGrupoAtencion,
    form=AgenteGrupoAtencionForm,
    formset=BaseAgenteGrupoAtencionFormset,
    extra=3,
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


#=========================================================================
# Base Datos Contactos
#=========================================================================

class BaseDatosContactoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('nombre'),
            Field('archivo_importacion'),
        )
        super(BaseDatosContactoForm, self).__init__(*args, **kwargs)

    class Meta:
        model = BaseDatosContacto
        exclude = ('columna_datos', 'sin_definir', 'columnas',
                   'nombre_archivo_importacion', 'cantidad_contactos',
                   'estado')


#=========================================================================
# Campaña
#=========================================================================

class CampanaForm(forms.ModelForm):
    fecha_inicio = forms.DateField(
        widget=DateTimePicker(options={"format": "DD/MM/YYYY",
                                       "pickTime": False}),
        help_text='Ejemplo: 10/04/2014')
    fecha_fin = forms.DateField(
        widget=DateTimePicker(options={"format": "DD/MM/YYYY",
                                       "pickTime": False}),
        help_text='Ejemplo: 20/04/2014')
    bd_contacto = forms.ModelChoiceField(
        queryset=BaseDatosContacto.objects.obtener_definidas(),
    )

    def __init__(self, reciclado=False, *args, **kwargs):
        super(CampanaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        if reciclado:
            self.fields.pop('bd_contacto')

            layout = Layout(
                Field('nombre'),
                Field('cantidad_canales'),
                Field('cantidad_intentos'),
                Field('segundos_ring'),
                Field('fecha_inicio'),
                Field('fecha_fin')
            )
        else:
            layout = Layout(
                Field('nombre'),
                Field('cantidad_canales'),
                Field('cantidad_intentos'),
                Field('segundos_ring'),
                Field('fecha_inicio'),
                Field('fecha_fin'),
                Field('bd_contacto')
            )
        self.helper.layout = layout

    class Meta:
        model = Campana
        exclude = ('estado',)


class AudioForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(AudioForm, self).__init__(*args, **kwargs)
        self.fields['audio_original'].required = True

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('audio_original'),
        )

    class Meta:
        model = Campana
        fields = ('audio_original',)
        widgets = {
            'audio_original': forms.FileInput(),
        }
        labels = {
            'audio_original': 'Audio',
        }
        help_texts = {
            'audio_original': """Seleccione el archivo de audio que desea para
            la Campaña. Si ya existe uno y guarda otro, el audio será
            reemplazado.""",
        }


class ConfirmaForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.add_input(
            Submit('confirma', 'Confirmar Campaña',
                   css_class='btn btn-success btn-lg modal_proceso_grande')
        )
        # self.helper.add_input(
        #     Submit('cancela', 'Cancelar', css_class='btn-danger')
        # )
        super(ConfirmaForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Campana
        fields = ()


class TipoRecicladoForm(forms.Form):
    tipo_reciclado_unico = forms.ChoiceField(
        choices=Campana.TIPO_RECICLADO_UNICO,
        widget=forms.RadioSelect,
        required=False,
    )
    tipo_reciclado_conjunto = forms.MultipleChoiceField(
        choices=Campana.TIPO_RECICLADO_CONJUNTO,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(TipoRecicladoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.form_id = 'id_guardar'
        self.helper.form_method = 'post'

        self.helper.add_input(
            Submit('continuar', 'Continuar',
                   css_class='btn btn-primary pull-right modal_proceso_grande')
        )

        self.helper.layout = Layout(
            Field('tipo_reciclado_unico', css_class='radio_reciclado'),
            Field('tipo_reciclado_conjunto', css_class='checkboxs_reciclado'),
        )


#=========================================================================
# Calificaciones
#=========================================================================

class CalificacionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('nombre'),
            Field('campana', type="hidden"),
        )
        super(CalificacionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Calificacion


#=========================================================================
# Opciones
#=========================================================================

class OpcionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        CSS_CLASS_GRUPO_ATENCION = 'accion accion-{0}'.format(Opcion.DERIVAR)
        CSS_CLASS_CALIFICACION = 'accion accion-{0}'.format(Opcion.CALIFICAR)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('digito'),
            Field('accion'),
            Field('grupo_atencion', css_class=CSS_CLASS_GRUPO_ATENCION),
            Field('calificacion', css_class=CSS_CLASS_CALIFICACION),
            Field('campana', type="hidden"),
        )
        super(OpcionForm, self).__init__(*args, **kwargs)
        self.fields['calificacion'].queryset = Calificacion.objects.filter(
            campana=self.initial['campana'])

    class Meta:
        model = Opcion

    def clean(self):
        cleaned_data = super(OpcionForm, self).clean()
        accion = cleaned_data.get("accion")
        grupo_atencion = cleaned_data.get("grupo_atencion")
        calificacion = cleaned_data.get("calificacion")

        msg = 'Este campo es requerido'
        if accion == Opcion.DERIVAR and not grupo_atencion:
            self._errors["grupo_atencion"] = self.error_class([msg])

        elif accion == Opcion.CALIFICAR and not calificacion:
            self._errors["calificacion"] = self.error_class([msg])

        return cleaned_data


#=========================================================================
# Actuación
#=========================================================================

class ActuacionForm(forms.ModelForm):
    hora_desde = forms.TimeField(
        help_text='Ejemplo: 09:10',
        widget=DateTimePicker(options={"format": "HH:mm",
                                       "pickDate": False},
                              icon_attrs={'class': 'glyphicon glyphicon-time'})
    )
    hora_hasta = forms.TimeField(
        help_text='Ejemplo: 20:30',
        widget=DateTimePicker(options={"format": "HH:mm",
                                       "pickDate": False},
                              icon_attrs={'class': 'glyphicon glyphicon-time'})
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('dia_semanal'),
            Field('hora_desde'),
            Field('hora_hasta'),
            Field('campana', type="hidden"),
        )
        super(ActuacionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Actuacion
