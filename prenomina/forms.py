from django import forms
from .models import Incapacidades, Tipo_incapacidad
from esquema.models import Puesto

class IncapacidadesForm(forms.ModelForm):
    #Se define un choiceField para seleccionar 
    opciones = (
        (None, 'Selecciona una opción'),
        (2, 'Castigos'),
        (3, 'Permisos con goce'),
        (4, 'Permisos sin goce'),
    )
    
    # Define el campo de selección utilizando ChoiceField
    incidencias = forms.ChoiceField(choices=opciones)
    
    class Meta:
        model = Incapacidades
        fields = ['fecha','fecha_fin','dia_inhabil','comentario','url']

class IncapacidadesTipoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].queryset = Tipo_incapacidad.objects.all()
        
    class Meta:
        model = Incapacidades
        fields = ['tipo','subsecuente','dia_inhabil','fecha','fecha_fin','comentario','url']
        
    
    
    
