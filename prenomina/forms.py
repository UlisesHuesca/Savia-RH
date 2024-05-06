from django import forms
from .models import Incapacidades

class IncapacidadesForm(forms.ModelForm):
    #Se define un choiceField para seleccionar 
    opciones = (
        (None, 'Selecciona una opción'),
        (1, 'Incapacidades'),
        (2, 'Castigos'),
        (3, 'Permisos con goce'),
        (4, 'Permisos sin goce'),
    )

    # Define el campo de selección utilizando ChoiceField
    incidencias = forms.ChoiceField(choices=opciones)
    
    class Meta:
        model = Incapacidades
        fields = ['fecha','fecha_fin','comentario','url']

