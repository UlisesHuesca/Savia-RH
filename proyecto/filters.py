import django_filters
from django.db.models import Q
from django.db.models import CharField, Value
from django.db.models.functions import Concat
from .models import Perfil, Status, Bonos, Costo, DatosBancarios, Vacaciones, Uniformes, Economicos, Catorcenas, Distrito, Empresa
from .models import Solicitud_vacaciones, Solicitud_economicos
from django_filters import DateFilter, CharFilter
import datetime

class PerfilFilter(django_filters.FilterSet):
    nombres_apellidos = CharFilter(method ='my_filter', label="Search")

    class Meta:
        model = Perfil
        fields = ['numero_de_trabajador','empresa','distrito','nombres_apellidos','proyecto','subproyecto',]

    def my_filter(self, queryset, name, value):
        return queryset.annotate(nombres_apellidos_combined=Concat('nombres', Value(' '), 'apellidos', output_field=CharField())).filter(nombres_apellidos_combined__icontains=value)

class StatusFilter(django_filters.FilterSet):
    numero_de_trabajador = django_filters.NumberFilter(field_name='perfil__numero_de_trabajador')
    empresa = django_filters.CharFilter(field_name='perfil__empresa__empresa', lookup_expr='icontains')
    distrito = django_filters.ModelChoiceFilter(queryset=Distrito.objects.all(), field_name='perfil__distrito__distrito')
    nombres_apellidos = CharFilter(method='nombres_apellidos_filter', label="Search")
    profesion = django_filters.CharFilter(field_name='profesion', lookup_expr='icontains')
    BAJA_CHOICES = ((False, 'Activo'),(True, 'Dado de baja'))
    baja = django_filters.ChoiceFilter(field_name='perfil__baja',choices=BAJA_CHOICES,empty_label=None)
    
    class Meta:
        model = Status
        fields = ['numero_de_trabajador','empresa','nombres_apellidos','profesion','tipo_de_contrato','distrito','baja']

    def nombres_apellidos_filter(self, queryset, name, value):
        return queryset.annotate(nombres_apellidos_combined=Concat('perfil__nombres', Value(' '), 'perfil__apellidos', output_field=CharField())).filter(nombres_apellidos_combined__icontains=value)

class BancariosFilter(django_filters.FilterSet):
    numero_de_trabajador = django_filters.NumberFilter(field_name='status__perfil__numero_de_trabajador')
    nombres_apellidos = CharFilter(method='nombres_apellidos_filter', label="Search")
    no_de_cuenta = django_filters.CharFilter(field_name='no_de_cuenta', lookup_expr='icontains')
    distrito = django_filters.ModelChoiceFilter(queryset=Distrito.objects.all(), field_name='status__perfil__distrito__distrito')
    BAJA_CHOICES = ((False, 'Activo'),(True, 'Dado de baja'))
    baja = django_filters.ChoiceFilter(field_name='status__perfil__baja',choices=BAJA_CHOICES,empty_label=None)
    class Meta:
        model = DatosBancarios
        fields = ['numero_de_trabajador','nombres_apellidos','no_de_cuenta','banco','distrito','baja']

    def nombres_apellidos_filter(self, queryset, name, value):
        return queryset.annotate(nombres_apellidos_combined=Concat('status__perfil__nombres', Value(' '), 'status__perfil__apellidos', output_field=CharField())).filter(nombres_apellidos_combined__icontains=value)


class CostoFilter(django_filters.FilterSet):
    numero_de_trabajador = django_filters.NumberFilter(field_name='status__perfil__numero_de_trabajador')
    nombres_apellidos = CharFilter(method='nombres_apellidos_filter', label="Search")
    empresa = django_filters.ModelChoiceFilter(queryset=Empresa.objects.all(), field_name='status__perfil__empresa__empresa')
    distrito = django_filters.ModelChoiceFilter(queryset=Distrito.objects.all(), field_name='status__perfil__distrito__distrito')
    #proyecto = django_filters.CharFilter(field_name='status__perfil__proyecto', lookup_expr='icontains')
    #subproyecto = django_filters.CharFilter(field_name='status__perfil__subproyecto', lookup_expr='icontains')
    BAJA_CHOICES = ((False, 'Activo'),(True, 'Dado de baja'))
    baja = django_filters.ChoiceFilter(field_name='status__perfil__baja',choices=BAJA_CHOICES,empty_label=None)
    class Meta:
        model = Costo
        fields = ['numero_de_trabajador','nombres_apellidos','empresa','distrito','baja']

    def nombres_apellidos_filter(self, queryset, name, value):
        return queryset.annotate(nombres_apellidos_combined=Concat('status__perfil__nombres', Value(' '), 'status__perfil__apellidos', output_field=CharField())).filter(nombres_apellidos_combined__icontains=value)


class BonosFilter(django_filters.FilterSet):
    nombres_apellidos = CharFilter(method='nombres_apellidos_filter', label="Search")
    start_date = DateFilter(field_name = 'fecha_bono', lookup_expr='gte')
    end_date = DateFilter(field_name = 'fecha_bono', lookup_expr='lte')
    distrito = django_filters.ModelChoiceFilter(queryset=Distrito.objects.all(), field_name='costo__status__perfil__distrito__distrito')
    BAJA_CHOICES = ((False, 'Activo'),(True, 'Dado de baja'))
    baja = django_filters.ChoiceFilter(field_name='costo__status__perfil__baja',choices=BAJA_CHOICES,empty_label=None)
    numero_catorcena = django_filters.NumberFilter(method='numero_catorcena_filter', label="Número de Catorcena")
    
    def numero_catorcena_filter(self, queryset, name, value):
        if value:
            try:
                # Obtener la catorcena correspondiente al número ingresado y año actual
                año_actual = datetime.date.today().year
                catorcena = Catorcenas.objects.get(catorcena=value, fecha_inicial__year=año_actual)

                # Filtrar los bonos que tienen fechas dentro del rango de la catorcena
                return queryset.filter(
                    Q(fecha_bono__range=(catorcena.fecha_inicial, catorcena.fecha_final)) |
                    Q(mes_bono__range=(catorcena.fecha_inicial, catorcena.fecha_final))
                )
            except Catorcenas.DoesNotExist:
                return queryset.none()
        return queryset

    class Meta:
        model = Bonos
        fields = ['start_date','end_date','nombres_apellidos','distrito','baja','numero_catorcena']

    def nombres_apellidos_filter(self, queryset, name, value):
        return queryset.annotate(nombres_apellidos_combined=Concat('costo__status__perfil__nombres', Value(' '), 'costo__status__perfil__apellidos', output_field=CharField())).filter(nombres_apellidos_combined__icontains=value)

class VacacionesFilter(django_filters.FilterSet):
    numero_de_trabajador = django_filters.NumberFilter(field_name='status__perfil__numero_de_trabajador')
    nombres_apellidos = CharFilter(method='nombres_apellidos_filter', label="Search")
    distrito = django_filters.ModelChoiceFilter(queryset=Distrito.objects.all(), field_name='status__perfil__distrito__distrito')
    BAJA_CHOICES = ((False, 'Activo'),(True, 'Dado de baja'))
    baja = django_filters.ChoiceFilter(field_name='status__perfil__baja',choices=BAJA_CHOICES,empty_label=None)

    class Meta:
        model = Vacaciones
        fields = ['numero_de_trabajador','nombres_apellidos','distrito','baja']

    def nombres_apellidos_filter(self, queryset, name, value):
        return queryset.annotate(nombres_apellidos_combined=Concat('status__perfil__nombres', Value(' '), 'status__perfil__apellidos', output_field=CharField())).filter(nombres_apellidos_combined__icontains=value)
#Uniformes usa el filter de status
class EconomicosFilter(django_filters.FilterSet):
    nombres_apellidos = CharFilter(method='nombres_apellidos_filter', label="Search")
    distrito = django_filters.ModelChoiceFilter(queryset=Distrito.objects.all(), field_name='status__perfil__distrito__distrito')
    BAJA_CHOICES = ((False, 'Activo'),(True, 'Dado de baja'))
    baja = django_filters.ChoiceFilter(field_name='status__perfil__baja',choices=BAJA_CHOICES,empty_label=None)
    class Meta:
        model = Economicos
        fields = ['nombres_apellidos','distrito','baja']

    def nombres_apellidos_filter(self, queryset, name, value):
        return queryset.annotate(nombres_apellidos_combined=Concat('status__perfil__nombres', Value(' '), 'status__perfil__apellidos', output_field=CharField())).filter(nombres_apellidos_combined__icontains=value)

class Costo_historicFilter(django_filters.FilterSet):
    start_date = DateFilter(field_name = 'updated_at', lookup_expr='gte')
    end_date = DateFilter(field_name = 'updated_at', lookup_expr='lte')

    class Meta:
        model = Costo
        fields = ['start_date','end_date',]

class CatorcenasFilter(django_filters.FilterSet):
    start_date = DateFilter(field_name = 'fecha_inicial', lookup_expr='gte')
    end_date = DateFilter(field_name = 'fecha_inicial', lookup_expr='lte')

    class Meta:
        model = Catorcenas
        fields = ['start_date','end_date',]

class DistritoFilter(django_filters.FilterSet):
    distrito = django_filters.CharFilter(field_name='distrito', lookup_expr='icontains')
    class Meta:
        model = Distrito
        fields = ['distrito',]

class SolicitudesVacacionesFilter(django_filters.FilterSet):
    numero_de_trabajador = django_filters.NumberFilter(field_name='status__perfil__numero_de_trabajador')
    nombres = CharFilter(method ='nombres_filter', label="Search")
    distrito = django_filters.ModelChoiceFilter(queryset=Distrito.objects.all(), field_name='status__perfil__distrito__distrito')

    class Meta:
        model = Solicitud_vacaciones
        fields = ['nombres','distrito','numero_de_trabajador',]

    def nombres_filter(self, queryset, name, value):
        return queryset.filter(Q(status__perfil__nombres__icontains = value) | Q(status__perfil__apellidos__icontains = value))

class SolicitudesEconomicosFilter(django_filters.FilterSet):
    numero_de_trabajador = django_filters.NumberFilter(field_name='status__perfil__numero_de_trabajador')
    nombres = CharFilter(method ='nombres_filter', label="Search")
    distrito = django_filters.ModelChoiceFilter(queryset=Distrito.objects.all(), field_name='status__perfil__distrito__distrito')
    class Meta:
        model = Solicitud_economicos
        fields = ['nombres','distrito','numero_de_trabajador',]

    def nombres_filter(self, queryset, name, value):
        return queryset.filter(Q(status__perfil__nombres__icontains = value) | Q(status__perfil__apellidos__icontains = value))