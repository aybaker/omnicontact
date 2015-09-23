# -*- coding: utf-8 -*-

"""
Formularios de Django
"""

from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.forms.models import inlineformset_factory

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Div, MultiField, HTML
from bootstrap3_datetime.widgets import DateTimePicker

from fts_web.models import (Actuacion, ActuacionSms, AgenteGrupoAtencion, ArchivoDeAudio,
                            AudioDeCampana, BaseDatosContacto, Campana,
                            CampanaSms, Calificacion, GrupoAtencion, Opcion,
                            OpcionSms, DerivacionExterna)


# =============================================================================
# Derivación Externa
# =============================================================================

class DerivacionExternaForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('nombre'),
            Field('tipo_derivacion'),
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
        fields = ('nombre', 'archivo_importacion')


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
        self.helper.layout = Layout(MultiField('telefono'))


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
                                error_messages={'required': ''},
                                widget=forms.TextInput(attrs={'class':
                                                       'nombre-columna'}))
            crispy_fields.append(Field('nombre-columna-{0}'.format(columna)))
        self.helper.layout = Layout(crispy_fields)


class PrimerLineaEncabezadoForm(forms.Form):
    es_encabezado = forms.BooleanField(label="Primer fila es encabezado.",
                                       required=False)

    def __init__(self, *args, **kwargs):
        super(PrimerLineaEncabezadoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(Field('es_encabezado'))


# =============================================================================
# Template
# =============================================================================

class TemplateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TemplateForm, self).__init__(*args, **kwargs)
        self.fields['bd_contacto'].queryset =\
            BaseDatosContacto.objects.obtener_definidas()

        # FIXME: Al ser el campo un TimeField, da un error al visualizar un
        # dato cargado.
        # self.fields['duracion_de_audio'].widget = DateTimePicker(
        #     options={"format": "HH:mm:ss", "pickDate": False,
        #              "pickSeconds": True, "useSeconds": True},
        #     icon_attrs={'class': 'glyphicon glyphicon-time'})
        self.fields['duracion_de_audio'].help_text = 'Ejemplo: 00:04:30'
        self.fields['duracion_de_audio'].required = True

        self.helper = FormHelper()
        self.helper.form_tag = False

        layout = Layout(
            Field('nombre'),
            Field('cantidad_canales'),
            Field('cantidad_intentos'),
            Field('segundos_ring'),
            Field('duracion_de_audio'),
            Field('accion_contestador'),
            Field('bd_contacto')
        )
        self.helper.layout = layout

    class Meta:
        model = Campana
        fields = ('nombre', 'cantidad_canales', 'cantidad_intentos',
                  'segundos_ring', 'duracion_de_audio', 'accion_contestador',
                  'bd_contacto')

        labels = {
            'duracion_de_audio': 'Duración de los audios (HH:MM:SS)',
            'bd_contacto': 'Base de Datos de referencia para TTS',
        }
        help_texts = {
            'bd_contacto': """¡Importante! La base de datos
                              que seleccione es solo de referencia para poder
                              especificar los tts de la campaña. No se
                              utilizará la misma en la ejecución de la
                              campaña.""",
        }

    def clean(self):
        cleaned_data = super(TemplateForm, self).clean()
        cantidad_canales = cleaned_data.get("cantidad_canales")

        if cantidad_canales > settings.FTS_LIMITE_GLOBAL_DE_CANALES:
                        raise forms.ValidationError("Ha excedido el limite de "
            "cantitad de canales. Su cantidad de canales contratado "
            "es {0}".format(settings.FTS_LIMITE_GLOBAL_DE_CANALES))

        return cleaned_data


# =============================================================================
# Campaña
# =============================================================================

class CampanaForm(forms.ModelForm):
    def __init__(self, reciclado=False, *args, **kwargs):
        super(CampanaForm, self).__init__(*args, **kwargs)

        self.fields['bd_contacto'].queryset =\
            BaseDatosContacto.objects.obtener_definidas()

        self.fields['fecha_inicio'].widget = DateTimePicker(
            options={"format": "DD/MM/YYYY", "pickTime": False})
        self.fields['fecha_inicio'].help_text = 'Ejemplo: 10/04/2014'
        self.fields['fecha_inicio'].required = True

        self.fields['fecha_fin'].widget = DateTimePicker(
            options={"format": "DD/MM/YYYY", "pickTime": False})
        self.fields['fecha_fin'].help_text = 'Ejemplo: 20/04/2014'
        self.fields['fecha_fin'].required = True

        # FIXME: Al ser el campo un TimeField, da un error al visualizar un
        # dato cargado.
        # self.fields['duracion_de_audio'].widget = DateTimePicker(
        #     options={"format": "HH:mm:ss", "pickDate": False,
        #              "pickSeconds": True, "useSeconds": True},
        #     icon_attrs={'class': 'glyphicon glyphicon-time'})
        self.fields['duracion_de_audio'].help_text = 'Ejemplo: 00:04:30'
        self.fields['duracion_de_audio'].required = True

        self.helper = FormHelper()
        self.helper.form_tag = False

        if reciclado:
            self.fields.pop('bd_contacto')

            layout = Layout(
                Field('nombre'),
                Field('cantidad_canales'),
                Field('cantidad_intentos'),
                Field('segundos_ring'),
                Field('duracion_de_audio'),
                Field('fecha_inicio'),
                Field('fecha_fin'),
                Field('accion_contestador'),
            )
        else:
            self.fields['bd_contacto'].required = True

            layout = Layout(
                Field('nombre'),
                Field('cantidad_canales'),
                Field('cantidad_intentos'),
                Field('segundos_ring'),
                Field('duracion_de_audio'),
                Field('fecha_inicio'),
                Field('fecha_fin'),
                Field('accion_contestador'),
                Field('bd_contacto')
            )
        self.helper.layout = layout

    class Meta:
        model = Campana
        fields = ('nombre', 'cantidad_canales', 'cantidad_intentos',
                  'segundos_ring', 'duracion_de_audio', 'fecha_inicio',
                  'fecha_fin', 'accion_contestador', 'bd_contacto')
        labels = {
            'bd_contacto': 'Base de Datos de Contactos',
            'duracion_de_audio': 'Duración de los audios (HH:MM:SS)'
        }

    def clean(self):
        cleaned_data = super(CampanaForm, self).clean()
        cantidad_canales = cleaned_data.get("cantidad_canales")

        if cantidad_canales > settings.FTS_LIMITE_GLOBAL_DE_CANALES:
                        raise forms.ValidationError("Ha excedido el limite de "
            "cantitad de canales. Su cantidad de canales contratado "
            "es {0}".format(settings.FTS_LIMITE_GLOBAL_DE_CANALES))

        return cleaned_data


class CampanaSmsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CampanaSmsForm, self).__init__(*args, **kwargs)

        self.fields['bd_contacto'].queryset =\
            BaseDatosContacto.objects.obtener_definidas()

        self.fields['fecha_inicio'].widget = DateTimePicker(
            options={"format": "DD/MM/YYYY", "pickTime": False})
        self.fields['fecha_inicio'].help_text = 'Ejemplo: 10/04/2014'
        self.fields['fecha_inicio'].required = True

        self.fields['fecha_fin'].widget = DateTimePicker(
            options={"format": "DD/MM/YYYY", "pickTime": False})
        self.fields['fecha_fin'].help_text = 'Ejemplo: 20/04/2014'
        self.fields['fecha_fin'].required = True

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields['bd_contacto'].required = True

        layout = Layout(
            Field('nombre'),
            Field('cantidad_chips'),
            Field('fecha_inicio'),
            Field('fecha_fin'),
            Field('bd_contacto'),
            Field('tiene_respuesta'),
        )
        self.helper.layout = layout

    class Meta:
        model = CampanaSms
        fields = ('nombre', 'cantidad_chips','fecha_inicio', 'fecha_fin',
                   'bd_contacto', 'tiene_respuesta')
        labels = {
            'bd_contacto': 'Base de Datos de Contactos',
        }

    def clean_cantidad_chips(self):
        cleaned_data = super(CampanaSmsForm, self).clean()
        cantidad_chips = cleaned_data.get("cantidad_chips")

        if cantidad_chips > settings.FTS_LIMITE_GLOBAL_DE_CHIPS:
            raise forms.ValidationError("Ha excedido el limite de "
                "cantitad de modems. Su cantidad de modems contratado "
                "es {0}".format(settings.FTS_LIMITE_GLOBAL_DE_CHIPS))

        return cantidad_chips


class TemplateMensajeCampanaSmsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TemplateMensajeCampanaSmsForm, self).__init__(*args, **kwargs)

        bd_contacto_metadada = self.instance.bd_contacto.get_metadata()

        variables_de_cuerpo_mensaje = ((variable, variable)
            for variable in bd_contacto_metadada.nombres_de_columnas)

        self.fields['variables'] = forms.MultipleChoiceField(
            choices=variables_de_cuerpo_mensaje)
        self.fields['variables'].required = False

        self.helper = FormHelper()
        self.helper.form_tag = False
        layout = Layout(
            Div(
                'variables',
                css_class='col-lg-5'
            ),
            Div(
                'template_mensaje',
                css_class='col-lg-5'
            ),
        )
        self.helper.layout = layout

    class Meta:
        model = CampanaSms
        fields = ('template_mensaje',)
        labels = {
            'template_mensaje': 'Cuerpo del Mensaje',
        }


class AudioForm(forms.ModelForm):
    check_audio_original = forms.BooleanField(
        label="Seleccionar y subir audio", required=False,
        widget=forms.CheckboxInput())

    def __init__(self, tts_choices, *args, **kwargs):
        super(AudioForm, self).__init__(*args, **kwargs)
        tts_choices.insert(0, ('', '---------'))
        self.fields['tts'].widget = forms.Select(choices=tts_choices)

        self.fields['audio_original'].widget.attrs['disabled'] = True
        self.fields['archivo_de_audio'].queryset =\
            ArchivoDeAudio.objects.all()

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('archivo_de_audio'),
            Field('check_audio_original'),
            Field('audio_original'),
            Field('tts'),
            Field('campana', type="hidden"),
        )

    class Meta:
        model = AudioDeCampana
        fields = ('audio_original', 'archivo_de_audio', 'tts', 'campana')
        widgets = {
            'audio_original': forms.FileInput(),
        }
        labels = {
            'audio_original': '',
            'archivo_de_audio': 'Audio Precargado',
            'tts': 'TTS',
        }
        help_texts = {
            'audio_original': """Seleccione el archivo de audio que desea para
            la Campaña.""",
        }


class OrdenAudiosForm(forms.Form):
    sentido_orden = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(OrdenAudiosForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('sentido_orden', type="hidden"),
        )


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
        self.helper.layout = Layout(
            Field('tipo_reciclado_unico', css_class='radio_reciclado'),
            Field('tipo_reciclado_conjunto', css_class='checkboxs_reciclado'),
            HTML("""
                <button type="submit" name="continuar" id="submit-id-continuar"
                    class="btn btn-default pull-right modal_proceso_grande">
                    Continuar
                    <span class="glyphicon glyphicon-chevron-right"></span>
                </button>"""),
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


class OpcionSmsForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('respuesta'),
            Field('campana_sms', type="hidden"),
        )
        super(OpcionSmsForm, self).__init__(*args, **kwargs)

    class Meta:
        model = OpcionSms


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


class ActuacionSmsForm(forms.ModelForm):
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
            Field('campana_sms', type="hidden"),
        )
        super(ActuacionSmsForm, self).__init__(*args, **kwargs)

    class Meta:
        model = ActuacionSms


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


# =============================================================================
# Búsqueda de Llamadas
# =============================================================================

class BusquedaDeLlamadasForm(forms.Form):
    numero_telefono = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(BusquedaDeLlamadasForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('numero_telefono'),
        )
