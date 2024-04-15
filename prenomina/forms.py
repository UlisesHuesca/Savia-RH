from django import forms
from .models import Incapacidades

class IncapacidadesForm(forms.ModelForm):
    class Meta:
        model = Incapacidades
        fields = ['fecha','fecha_fin','comentario','url']

