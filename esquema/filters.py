import django_filters

from .models import Subcategoria,Solicitud
from revisar.models import AutorizarSolicitudes,Estado
from proyecto.models import TipoPerfil, Distrito
from esquema.models import BonoSolicitado,Puesto
from django.db.models import CharField, Value
from django.db.models.functions import Concat
from django_filters import CharFilter

from datetime import datetime, timedelta

class BonoSolicitadoFilter(django_filters.FilterSet):
    distrito = django_filters.ModelChoiceFilter(queryset=Distrito.objects.filter(id__in=[1,2,4,6,5]), field_name='distrito__distrito')
    folio = django_filters.NumberFilter(field_name="solicitud_id")
    nombres_apellidos = CharFilter(method='nombres_apellidos_filter', label="Search")
    bono = django_filters.ModelChoiceFilter(queryset=Subcategoria.objects.all(), field_name='solicitud__bono')
    puesto = django_filters.ModelChoiceFilter(queryset=Puesto.objects.all().order_by('puesto'), field_name='puesto')
    no_trabajador = django_filters.NumberFilter(field_name="trabajador__numero_de_trabajador")
    #Fecha emision
    fecha_inicio = django_filters.DateFilter(field_name='fecha', lookup_expr='gte', label='Fecha de inicio')
    fecha_fin = django_filters.DateFilter(field_name='fecha', lookup_expr='lte', label='Fecha de fin', method='sumar_un_dia')
    #fecha aprobacion
    fecha_inicio_a = django_filters.DateFilter(field_name='solicitud__fecha_autorizacion', lookup_expr='gte', label='Fecha de inicio')
    fecha_fin_a = django_filters.DateFilter(field_name='solicitud__fecha_autorizacion', lookup_expr='lte', label='Fecha de fin', method='sumar_un_dia')
    #fecha catorcena
    fecha_inicial_catorcena = django_filters.DateFilter(field_name='solicitud__fecha_autorizacion', lookup_expr='gte', label='Fecha de inicio')
    fecha_final_catorcena = django_filters.DateFilter(field_name='solicitud__fecha_autorizacion', lookup_expr='lte', label='Fecha de fin',  method='sumar_un_dia')
    
    def custom_extract_date(self, queryset, name, value):
        return queryset.filter(fecha__date__lte=value)
  
    
    #suma un dia a la fecha fin. porque a la hora de buscar me resta un dia, tal vez tenga que ver por las horas y minutos
    def sumar_un_dia(self, queryset, name, value):
        sumar = value + timedelta(1)
        return queryset.filter(**{f"{name}__lt": sumar})
    
    class Meta:
        model = BonoSolicitado
        fields = ['folio','distrito','nombres_apellidos','bono','puesto','no_trabajador']
    
    
    def nombres_apellidos_filter(self, queryset, name, value):
        return queryset.annotate(nombres_apellidos_combined=Concat('trabajador__nombres', Value(' '), 'trabajador__apellidos', output_field=CharField())).filter(nombres_apellidos_combined__icontains=value)




class AutorizarSolicitudesFilter(django_filters.FilterSet):
    estado = django_filters.ModelChoiceFilter(queryset=Estado.objects.all().order_by('tipo'), field_name='estado__tipo')
    bono = django_filters.ModelChoiceFilter(queryset=Subcategoria.objects.all().order_by('nombre'),field_name="solicitud__bono")
    rol = django_filters.ModelChoiceFilter(queryset=TipoPerfil.objects.filter(id__in=[6,7,8]), field_name='tipo_perfil__nombre')
    distrito = django_filters.ModelChoiceFilter(queryset=Distrito.objects.filter(id__in=[1,4,2,6,5]).order_by('distrito'), field_name="perfil__distrito")
    folio = django_filters.NumberFilter(field_name="solicitud_id")
    #fecha emision
    fecha_inicio = django_filters.DateFilter(field_name='solicitud__fecha', lookup_expr='gte', label='Fecha de inicio')
    fecha_fin = django_filters.DateFilter(field_name='solicitud__fecha', lookup_expr='lte', label='Fecha de fin', method='sumar_un_dia')
    #fecha revision
    fecha_inicio_r = django_filters.DateFilter(field_name='created_at', lookup_expr='gte', label='Fecha de inicio')
    fecha_fin_r = django_filters.DateFilter(field_name='created_at', lookup_expr='lte', label='Fecha de fin', method='sumar_un_dia')
    #suma un dia a la fecha fin. porque a la hora de buscar me resta un dia, tal vez tenga que ver por las horas y minutos
    def sumar_un_dia(self, queryset, name, value):
        sumar = value + timedelta(1)
        return queryset.filter(**{f"{name}__lt": sumar})
    
    class Meta:
        model = AutorizarSolicitudes
        fields = ['estado','bono','rol','folio','distrito','fecha_inicio','fecha_fin','fecha_inicio_r','fecha_fin_r']
        
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