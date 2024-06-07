from django import forms
from .models import PrenominaIncidencias, Incidencia, IncidenciaRango
from proyecto.models import Dia_vacacion
from django.forms import formset_factory
from django.core.cache import cache

from datetime import date, timedelta

class PrenominaIncidenciasForm(forms.ModelForm):    
    class Meta:
        model = PrenominaIncidencias
        fields = ['fecha', 'comentario', 'incidencia']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha'].widget.attrs['readonly'] = 'readonly'
        
        #se crea la cache para la consulta de las incidencias
        cache_key = 'incidencias_cache'
        incidencias_cache = cache.get(cache_key)
        if not incidencias_cache:
            incidencias_cache = Incidencia.objects.all().order_by('tipo')
            cache.set(cache_key, incidencias_cache)
        self.fields['incidencia'].queryset = incidencias_cache
        
        #eliminar cache
        #incidencias_cache = cache.get(cache_key)
        #cache.delete(cache_key)
        
        
PrenominaIncidenciasFormSet = formset_factory(PrenominaIncidenciasForm, extra=0) 
        





        
    
    
