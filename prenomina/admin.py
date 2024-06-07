from django.contrib import admin

# Register your models here.
from .models import Prenomina, PrenominaIncidencias, IncidenciaRango

admin.site.register(Prenomina)
admin.site.register(PrenominaIncidencias)
admin.site.register(IncidenciaRango)

