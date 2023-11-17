from django.contrib import admin

from .models import Categoria, Subcategoria, Esquema, Solicitud, EsquemaSolicitado, TipoRequerimiento, Requerimiento

# Register your models here.
admin.site.register(Categoria)
admin.site.register(Subcategoria)
admin.site.register(Esquema)
admin.site.register(Solicitud)
admin.site.register(EsquemaSolicitado)
admin.site.register(TipoRequerimiento)
admin.site.register(Requerimiento)