# -*- coding: utf-8 -*-
# from django.db.models import get_model
# from django import forms

# from crispy_forms.helper import FormHelper
# from crispy_forms.layout import (
#     Layout, Fieldset, ButtonHolder, Submit,
#     Div,
# )

# GrupoAtencion = get_model('fts_web', 'GrupoAtencion')


# class GrupoAtencionForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         super(GrupoAtencionForm, self).__init__(*args, **kwargs)

#         # If you pass FormHelper constructor a form instance
#         # It builds a default layout with all its fields
#         self.helper = FormHelper(self)

#         # You can dynamically adjust your layout
#         self.helper.layout.append(Submit('save', 'save'))

#     class Meta:
#         model = GrupoAtencion
