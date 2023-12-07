from django.contrib import admin

from .models import Categoria, Subcategoria,Bono,Solicitud,Requerimiento

# Register your models here.
admin.site.register(Categoria)
admin.site.register(Subcategoria)
admin.site.register(Bono)
admin.site.register(Solicitud)
admin.site.register(Requerimiento)