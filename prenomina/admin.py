from django.contrib import admin

# Register your models here.
from .models import Prenomina, Incidencia, IncidenciasRango, IncapacidadesRango, pagar_incapacidad

admin.site.register(Prenomina)
admin.site.register(Incidencia)
admin.site.register(IncidenciasRango)
admin.site.register(IncapacidadesRango)
admin.site.register(pagar_incapacidad)

