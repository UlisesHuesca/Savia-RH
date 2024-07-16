from django.urls import path
from . import views

urlpatterns = [
    #Bono Varillero - solicitudes
    path('bonos/', views.inicio, name='bono_inicio'),
    path('bonos_varillero/', views.listarBonosVarilleros, name='listarBonosVarilleros'),
    path('bonos_varillero/crear_solicitud/', views.crearSolicitudBonosVarilleros, name="crearSolicitudBonosVarilleros"),
    path('bonos_varillero/<int:solicitud_id>/ver-detalles-solicitud/', views.verDetallesSolicitud, name="verDetalleSolicitud"),
    path('bonos_varillero/<int:solicitud>/verificar-solicitud/', views.verificarSolicitudBonosVarilleros, name="verificarSolicitudBonosVarilleros"),
    path('bonos_varillero/bonos-aprobados', views.listarBonosVarillerosAprobados, name='listarBonosVarillerosAprobados'),
    path('bonos_varillero/generar-reporte', views.generarReporteBonosVarillerosAprobados, name="generarReporteBonosVarillerosAprobados"),
    #Modulo crear bonos
    #path('bonos_varillero/tabulador_bonos',views.tabuladorBonos, name="tabuladorBonos"),
    #api
    path('solicitar_esquema_bonos/',views.solicitarEsquemaBono),
    path('remover_bono/<int:bono_id>/',views.removerBono),
    path('remover_bonos/editar/<int:solicitud_id>/',views.removerBonosEditar),
    path('remover_archivo/<int:archivo_id>/',views.removerArchivo),
    path('enviar_solicitud/',views.EnviarSolicitudEsquemaBono),
    path('solicitar_soporte_bono/',views.solicitarSoporteBono),
    
]