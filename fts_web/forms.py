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

from fts_web.models import (Actuacion, AgenteGrupoAtencion, ArchivoDeAudio,
                            BaseDatosContacto, Campana, Calificacion,
                            GrupoAtencion, Opcion, DerivacionExterna)


# =============================================================================
# Derivación Externa
# =============================================================================

class DerivacionExternaForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('nombre'),
            Field('dial_string'),
        )
        super(DerivacionExternaForm, self).__init__(*args, **kwargs)

    class Meta:
        model = DerivacionExterna


# =============================================================================
# Grupos de Atención
# =============================================================================

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


# =============================================================================
# Base Datos Contactos
# =============================================================================

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
        exclude = ('sin_definir', 'nombre_archivo_importacion', 'estado',
                   'cantidad_contactos')


class DefineColumnaTelefonoForm(forms.Form):

    def __init__(self, cantidad_columnas=0, *args, **kwargs):
        super(DefineColumnaTelefonoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        COLUMNAS_TELEFONO = []
        for columna in range(int(cantidad_columnas)):
            COLUMNAS_TELEFONO.append((columna, 'Columna{0}'.format(columna)))

        self.fields['telefono'] = forms.ChoiceField(choices=COLUMNAS_TELEFONO,
                                                    widget=forms.RadioSelect(
                                                        attrs={'class':
                                                               'telefono'}))
        self.helper.layout = Layout(Field('telefono'))


class DefineDatosExtrasForm(forms.Form):

    def __init__(self, cantidad_columnas=0, *args, **kwargs):
        super(DefineDatosExtrasForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        crispy_fields = []
        for columna in range(int(cantidad_columnas)):
            value = forms.ChoiceField(choices=BaseDatosContacto.DATOS_EXTRAS,
                                      required=False, label="",
                                      widget=forms.Select(
                                          attrs={'class': 'datos-extras'}))
            self.fields['datos-extras-{0}'.format(columna)] = value

            crispy_fields.append(Field('datos-extras-{0}'.format(columna)))
        self.helper.layout = Layout(crispy_fields)


class DefineNombreColumnaForm(forms.Form):

    def __init__(self, cantidad_columnas=0, *args, **kwargs):
        super(DefineNombreColumnaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        crispy_fields = []
        for columna in range(int(cantidad_columnas)):
            self.fields['nombre-columna-{0}'.format(columna)] = \
                forms.CharField(label="", initial='Columna{0}'.format(columna),
                                widget=forms.TextInput(attrs={'class':
                                                       'nombre-columna'}))
            crispy_fields.append(Field('nombre-columna-{0}'.format(columna)))
        self.helper.layout = Layout(crispy_fields)


# =============================================================================
# Template
# =============================================================================

class TemplateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TemplateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        layout = Layout(
            Field('nombre'),
            Field('cantidad_canales'),
            Field('cantidad_intentos'),
            Field('segundos_ring'),
        )
        self.helper.layout = layout

    class Meta:
        model = Campana
        exclude = ('estado', 'fecha_inicio', 'fecha_fin', 'bd_contacto',
                   'es_template')


# =============================================================================
# Campaña
# =============================================================================

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
    queryset = ArchivoDeAudio.objects.all()
    archivo_audio = forms.ModelChoiceField(label='Archivo de Audio',
                                           required=False,
                                           queryset=queryset)

    check_audio_original = forms.BooleanField(label="Especificar Audio",
                                              required=False,
                                              widget=forms.CheckboxInput())

    def __init__(self, id_archivo_audio=None, *args, **kwargs):
        super(AudioForm, self).__init__(*args, **kwargs)
        self.fields['archivo_audio'].initial = id_archivo_audio
        self.fields['audio_original'].widget.attrs['disabled'] = True

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('archivo_audio'),
            Field('check_audio_original'),
            Field('audio_original'),
        )

    class Meta:
        model = Campana
        fields = ('audio_original',)
        widgets = {
            'audio_original': forms.FileInput(),
        }
        labels = {
            'audio_original': '',
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
            Submit('confirma', 'Confirmar Creación',
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


# =============================================================================
# Calificaciones
# =============================================================================

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


# =============================================================================
# Opciones
# =============================================================================

class OpcionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        CSS_CLASS_GRUPO_ATENCION = 'accion accion-{0}'.format(
            Opcion.DERIVAR_GRUPO_ATENCION)
        CSS_CLASS_DERIVACION_EXTERNA = 'accion accion-{0}'.format(
            Opcion.DERIVAR_DERIVACION_EXTERNA)
        CSS_CLASS_CALIFICACION = 'accion accion-{0}'.format(Opcion.CALIFICAR)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('digito'),
            Field('accion'),
            Field('grupo_atencion', css_class=CSS_CLASS_GRUPO_ATENCION),
            Field('derivacion_externa',
                  css_class=CSS_CLASS_DERIVACION_EXTERNA),
            Field('calificacion', css_class=CSS_CLASS_CALIFICACION),
            Field('campana', type="hidden"),
        )
        super(OpcionForm, self).__init__(*args, **kwargs)
        self.fields['grupo_atencion'].queryset = GrupoAtencion.objects.all()
        self.fields['derivacion_externa'].queryset = \
            DerivacionExterna.objects.all()
        self.fields['calificacion'].queryset = Calificacion.objects.filter(
            campana=self.initial['campana'])

    class Meta:
        model = Opcion

    def clean(self):
        cleaned_data = super(OpcionForm, self).clean()
        accion = cleaned_data.get("accion")
        grupo_atencion = cleaned_data.get("grupo_atencion")
        derivacion_externa = cleaned_data.get("derivacion_externa")
        calificacion = cleaned_data.get("calificacion")

        msg = 'Este campo es requerido'
        if accion == Opcion.DERIVAR_GRUPO_ATENCION and not grupo_atencion:
            self._errors["grupo_atencion"] = self.error_class([msg])
        elif (accion == Opcion.DERIVAR_DERIVACION_EXTERNA
              and not derivacion_externa):
            self._errors["grupo_atencion"] = self.error_class([msg])
        elif accion == Opcion.CALIFICAR and not calificacion:
            self._errors["calificacion"] = self.error_class([msg])
        return cleaned_data


# =============================================================================
# Actuación
# =============================================================================

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


# =============================================================================
# Archivo De Audio
# =============================================================================


class ArchivoAudioForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ArchivoAudioForm, self).__init__(*args, **kwargs)
        self.fields['audio_original'].required = True

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('descripcion'),
            Field('audio_original'),
        )

    class Meta:
        model = ArchivoDeAudio
        fields = ('descripcion', 'audio_original',)
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
