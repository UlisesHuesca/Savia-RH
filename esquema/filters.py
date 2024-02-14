import django_filters

from .models import Subcategoria,Solicitud
from revisar.models import AutorizarSolicitudes,Estado
from proyecto.models import TipoPerfil, Distrito

from datetime import datetime, timedelta

class AutorizarSolicitudesFilter(django_filters.FilterSet):
    estado = django_filters.ModelChoiceFilter(queryset=Estado.objects.all().order_by('tipo'), field_name='estado__tipo')
    bono = django_filters.ModelChoiceFilter(queryset=Subcategoria.objects.all().order_by('nombre'),field_name="solicitud__bono")
    rol = django_filters.ModelChoiceFilter(queryset=TipoPerfil.objects.filter(id__in=[6,7]), field_name='tipo_perfil__nombre')
    distrito = django_filters.ModelChoiceFilter(queryset=Distrito.objects.filter(id__in=[4,2,6,5]), field_name="perfil__distrito")
    folio = django_filters.NumberFilter(field_name="solicitud_id")
    
    class Meta:
        model = AutorizarSolicitudes
        fields = ['estado','bono','rol','folio','distrito']
        
    def sumar_un_dia(self, queryset, name, value):
        sumar = value + timedelta(1)
        return queryset.filter(**{f"{name}__lt": sumar})
        
class SubcategoriaFilter(django_filters.FilterSet):
    class Meta:
        model = Subcategoria
        fields = ['nombre']
        
class SolicitudFilter(django_filters.FilterSet):
    #date = django_filters.DateFilter(field_name='fecha', lookup_expr='gte', label='Fecha')
    fecha_inicio = django_filters.DateFilter(field_name='fecha', lookup_expr='gte', label='Fecha de inicio')
    fecha_fin = django_filters.DateFilter(field_name='fecha', lookup_expr='lte', label='Fecha de fin', method='sumar_un_dia')
   
    #suma un dia a la fecha fin. porque a la hora de buscar me resta un dia, tal vez tenga que ver por las horas y minutos
    def sumar_un_dia(self, queryset, name, value):
        sumar = value + timedelta(1)
        return queryset.filter(**{f"{name}__lt": sumar})
    
    class Meta:
        model = Solicitud
        fields = ['folio','bono','fecha','fecha_inicio','fecha_fin']