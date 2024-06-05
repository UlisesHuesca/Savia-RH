from django import forms
from .models import PrenominaIncidencias, Incidencia, IncidenciasRango
from proyecto.models import Dia_vacacion
from django.forms import modelformset_factory


class IncidenciasRangoForm(forms.ModelForm):
    class Meta:
        model = IncidenciasRango
        fields = ['incidencia', 'fecha_inicio', 'fecha_fin','dia_inhabil','comentario','soporte']
        required = {
            'comentario':False
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['incidencia'].queryset = Incidencia.objects.filter(pk__in=[7,8,9])
        #self.fields['dia_inhabil'].queryset = Incidencia.objects.all()

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


        
    
    
