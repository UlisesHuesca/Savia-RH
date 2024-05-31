from django import forms
from .models import PrenominaIncidencias, Incidencia
from django.forms import modelformset_factory

#Se define el formulario de la prenomina
class PrenominaIncidenciasForm(forms.ModelForm):    
    class Meta:
        model = PrenominaIncidencias
        fields = ['fecha', 'comentario', 'incidencia', 'soporte']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha'].widget.attrs['readonly'] = 'readonly'
            
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['incidencia'].queryset = Incidencia.objects.all().order_by('tipo')
        
#Se define un formset - crea 14    
PrenominaIncidenciasFormSet = modelformset_factory(PrenominaIncidencias,PrenominaIncidenciasForm, extra=0) 
    
    
