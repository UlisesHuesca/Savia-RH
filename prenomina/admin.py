from django.contrib import admin

# Register your models here.
from .models import Prenomina
from .models import Retardos
from .models import Castigos
from .models import Permiso_goce
from .models import Permiso_sin
from .models import Descanso
from .models import Incapacidades
from .models import Faltas
from .models import Comision
from .models import Domingo
from .models import Dia_extra
from .models import Tipo_incapacidad

admin.site.register(Prenomina)
admin.site.register(Retardos)
admin.site.register(Castigos)
admin.site.register(Permiso_goce)
admin.site.register(Permiso_sin)
admin.site.register(Descanso)
admin.site.register(Incapacidades)
admin.site.register(Faltas)
admin.site.register(Comision)
admin.site.register(Domingo)
admin.site.register(Dia_extra)
admin.site.register(Tipo_incapacidad)