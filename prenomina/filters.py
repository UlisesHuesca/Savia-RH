import django_filters
from django.db.models import Q
from django.db.models import CharField, Value
from django.db.models.functions import Concat
from django_filters import DateFilter, CharFilter
from .models import Prenomina
from proyecto.models import Empresa, Distrito


class PrenominaFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter(field_name='id')
    numero_de_trabajador = django_filters.NumberFilter(field_name='empleado__status__perfil__numero_de_trabajador')
    nombres_apellidos = CharFilter(method='nombres_apellidos_filter', label="Search")
    empresa = django_filters.ModelChoiceFilter(queryset=Empresa.objects.all(), field_name='empleado__status__perfil__empresa__empresa')
    distrito = django_filters.ModelChoiceFilter(queryset=Distrito.objects.all(), field_name='empleado__status__perfil__distrito__distrito')
    #proyecto = django_filters.CharFilter(field_name='status__perfil__proyecto', lookup_expr='icontains')
    #subproyecto = django_filters.CharFilter(field_name='status__perfil__subproyecto', lookup_expr='icontains')
    BAJA_CHOICES = ((False, 'Activo'),(True, 'Dado de baja'))
    baja = django_filters.ChoiceFilter(field_name='empleado__status__perfil__baja',choices=BAJA_CHOICES,empty_label=None)
    class Meta:
        model = Prenomina
        fields = ['id', 'numero_de_trabajador','nombres_apellidos','empresa','distrito','baja']

    def nombres_apellidos_filter(self, queryset, name, value):
        return queryset.annotate(nombres_apellidos_combined=Concat('empleado__status__perfil__nombres', Value(' '), 'empleado__status__perfil__apellidos', output_field=CharField())).filter(nombres_apellidos_combined__icontains=value)