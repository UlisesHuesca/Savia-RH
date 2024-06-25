import django_filters
from django.db.models import Q
from django.db.models import CharField, Value
from django.db.models.functions import Concat
from django_filters import DateFilter, CharFilter
from .models import Prenomina
from proyecto.models import Vacaciones_dias_tomados
from proyecto.models import Empresa, Distrito, Vacaciones_dias_tomados, Catorcenas, Economicos_dia_tomado
from django.db.models import Exists, OuterRef
import datetime 
from datetime import timedelta, date

class PrenominaFilter(django_filters.FilterSet):
    incidencias = django_filters.ChoiceFilter(label='Opción', choices=(
        ('1', 'Retardos'),
        ('2', 'Castigos'),
        ('3', 'Permiso con goce de sueldo'),
        ('4', 'Permiso sin goce de sueldo'),
        ('5', 'Descanso'),
        ('6', 'Incapacidades'),
        ('7', 'Faltas'),
        ('8', 'Comisión'),
        ('9', 'Domingo'),
        ('10', 'Dia extra'),
        ('11', 'Vacaciones'),
        ('12', 'Economicos')
    ), method='filtrar_por_incidencias')
    
    id = django_filters.NumberFilter(field_name='id')
    numero_de_trabajador = django_filters.NumberFilter(field_name='empleado__status__perfil__numero_de_trabajador')
    nombres_apellidos = CharFilter(method='nombres_apellidos_filter', label="Search")
    empresa = django_filters.ModelChoiceFilter(queryset=Empresa.objects.all(), field_name='empleado__status__perfil__empresa__empresa')
    distrito = django_filters.ModelChoiceFilter(queryset=Distrito.objects.all(), field_name='empleado__status__perfil__distrito__distrito')
    start_date = DateFilter(field_name='catorcena__fecha_inicial', lookup_expr='gte')
    end_date = DateFilter(field_name='catorcena__fecha_final', lookup_expr='lte')
    
    #incidencias = django_filters.ChoiceFilter(choices=opciones, method='filtrar_por_incidencias')
    
    #subproyecto = django_filters.CharFilter(field_name='status__perfil__subproyecto', lookup_expr='icontains')
    BAJA_CHOICES = ((False, 'Activo'),(True, 'Dado de baja'))
    baja = django_filters.ChoiceFilter(field_name='empleado__status__perfil__baja',choices=BAJA_CHOICES,empty_label=None)
    
    class Meta:
        model = Prenomina
        fields = ['id', 'numero_de_trabajador','nombres_apellidos','empresa','distrito','baja','catorcena',]

    def nombres_apellidos_filter(self, queryset, name, value):
        return queryset.annotate(nombres_apellidos_combined=Concat('empleado__status__perfil__nombres', Value(' '), 'empleado__status__perfil__apellidos', output_field=CharField())).filter(nombres_apellidos_combined__icontains=value)
    
    def filtrar_por_incidencias(self, queryset, name, value):
        if value == '1':
            premominas = queryset.filter(retardos__fecha__isnull = False)
            return queryset.filter(id__in=premominas)
        if value == '2':
            premominas = queryset.filter(castigos__fecha__isnull = False)
            return queryset.filter(id__in=premominas)
        if value == '3':
            premominas = queryset.filter(permiso_goce__fecha__isnull = False)
            return queryset.filter(id__in=premominas)
        if value == '4':
            premominas = queryset.filter(permiso_sin__fecha__isnull = False)
            return queryset.filter(id__in=premominas)
        if value == '5':
            premominas = queryset.filter(descanso__fecha__isnull = False)
            return queryset.filter(id__in=premominas)
        if value == '6':
            premominas = queryset.filter(incapacidades__fecha__isnull = False)
            return queryset.filter(id__in=premominas)
        if value == '7':
            premominas = queryset.filter(faltas__fecha__isnull = False)
            return queryset.filter(id__in=premominas)
        if value == '8':
            premominas = queryset.filter(comision__fecha__isnull = False)
            return queryset.filter(id__in=premominas)
        if value == '9':
            premominas = queryset.filter(domingo__fecha__isnull = False)
            return queryset.filter(id__in=premominas)
        if value == '10':
            premominas = queryset.filter(dia_extra__fecha__isnull = False)
            return queryset.filter(id__in=premominas)
        if value == '11':
            ahora = datetime.date.today()
            catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
            #Filtro fecha de inicio y fecha fin de dia tomado que este alguna entre el rango de la catorcena
            datos = Vacaciones_dias_tomados.objects.filter(Q(fecha_inicio__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) |Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
            status_ids = datos.values_list('prenomina__status', flat=True)
            return queryset.filter(empleado__status__id__in=status_ids)
        if value == '12':
            ahora = datetime.date.today()
            catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
            datos = Economicos_dia_tomado.objects.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
            status_ids = datos.values_list('prenomina__status', flat=True)
            return queryset.filter(empleado__status__id__in=status_ids)
        else:
            return queryset