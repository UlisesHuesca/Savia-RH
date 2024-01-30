import django_filters
from .models import Subcategoria,Solicitud
from datetime import datetime, timedelta
                            
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