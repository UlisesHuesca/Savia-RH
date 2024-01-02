from django.contrib import admin
from .models import Categoria, Subcategoria,Bono,Solicitud,Requerimiento

# Register your models here.
admin.site.register(Categoria)
admin.site.register(Subcategoria)

admin.site.register(Solicitud)
admin.site.register(Requerimiento)

class BonoAdmin(admin.ModelAdmin):
    ordering = ['esquema_subcategoria']
    list_display = ['esquema_subcategoria','puesto','distrito','importe']
    search_fields = ['esquema_subcategoria__nombre','puesto__puesto','distrito__distrito','importe']
    list_filter = ['esquema_subcategoria','distrito']

admin.site.register(Bono,BonoAdmin)