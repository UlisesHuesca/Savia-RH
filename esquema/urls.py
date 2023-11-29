from django.urls import path
from . import views

urlpatterns = [
    path('bonos/', views.inicio, name='bono_inicio'),
    path('bonos_varillero/', views.listarBonosVarilleros, name='listarBonosVarilleros'),
    path('bonos_varillero/crear_solicitud/', views.crearSolicitudBonosVarilleros, name="crearSolicitudBonosVarilleros"),
    path('solicitar_esquema_bonos/',views.solicitarEsquemaBono)
]