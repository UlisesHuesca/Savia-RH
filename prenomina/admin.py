from django.contrib import admin

# Register your models here.
from .models import Prenomina, Incidencia, IncidenciaRango, PrenominaIncidencias, TipoAguinaldo, Aguinaldo

class PrenominaAdmin(admin.ModelAdmin):
    ordering = ['id']
    list_display = ('id','empleado','catorcena',)
    search_fields = ('empleado__status__perfil__numero_de_trabajador'),
    list_filter = ('empleado__status__perfil__distrito',)

class IncidenciaAdmin(admin.ModelAdmin):
    ordering = ['id',]
    list_display = ('tipo','id',)


admin.site.register(Prenomina, PrenominaAdmin)
admin.site.register(Incidencia, IncidenciaAdmin)
admin.site.register(IncidenciaRango)
admin.site.register(PrenominaIncidencias)
admin.site.register(TipoAguinaldo)
admin.site.register(Aguinaldo)