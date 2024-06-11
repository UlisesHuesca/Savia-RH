from django import forms
from .models import PrenominaIncidencias, Incidencia, IncidenciaRango
from proyecto.models import Dia_vacacion
from django.forms import formset_factory
from django.core.cache import cache
from datetime import date, timedelta


class IncidenciaRangoForm(forms.ModelForm):
    SUBSECUENTE_CHOICES = (
        (None, '---------'),  # Para representar el valor nulo
        (True, 'Sí'),
        (False, 'No'),
    )
    
    subsecuente = forms.ChoiceField(choices=SUBSECUENTE_CHOICES, required=False)
    
    class Meta:
        model = IncidenciaRango
        fields = ['fecha_inicio','fecha_fin','comentario','soporte','subsecuente','dia_inhabil','incidencia']
        
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        incidencias = Incidencia.objects.filter(id__in=[4,7,8,9,10,11,12]).order_by('tipo')
        descansos = Dia_vacacion.objects.all()
        self.fields['incidencia'].queryset = incidencias
        self.fields['dia_inhabil'].queryset = descansos
        self.fields['comentario'].required = False

class PrenominaIncidenciasForm(forms.ModelForm):    
    class Meta:
        model = PrenominaIncidencias
        fields = ['fecha', 'comentario', 'incidencia','soporte']

        #id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
        DELETE = forms.BooleanField(required=False, initial=False)  # Campo para marcar la eliminación
    
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    id_rango = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha'].widget.attrs['readonly'] = 'readonly'
        #self.fields['soporte'].widget.attrs['readonly'] = 'readonly'
        
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
        
        
PrenominaIncidenciasFormSet = formset_factory(PrenominaIncidenciasForm, extra=0,can_delete=True) 
        





        
    
    
