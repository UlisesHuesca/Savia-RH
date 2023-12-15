from django.urls import path
from . import views

urlpatterns = [
    #Bono Varillero
    path('bonos/', views.inicio, name='bono_inicio'),
    path('bonos_varillero/', views.listarBonosVarilleros, name='listarBonosVarilleros'),
    path('bonos_varillero/crear_solicitud/', views.crearSolicitudBonosVarilleros, name="crearSolicitudBonosVarilleros"),
    path('bonos_varillero/<int:solicitud_id>/ver-detalles-solicitud/', views.verDetallesSolicitud, name="verDetalleSolicitud"),
    path('solicitar_esquema_bonos/',views.solicitarEsquemaBono),
    path('remover_bono/<int:bono_id>/',views.removerBono),
    path('remover_archivo/<int:archivo_id>/',views.removerArchivo),
    
]