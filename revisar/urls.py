from django.urls import path
from . import views

urlpatterns = [
    #Bono Varillero
    path('bonos_varillero/<int:solicitud>/autorizar-solicitud', views.autorizarSolicitud, name="autorizarSolicitudes"),
    #path('autorizar-solicutud/forbidden', views.forbidden, name="forbidden")
]
