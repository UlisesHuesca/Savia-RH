from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    #Bono Varillero
    path('bonos_varillero/<int:solicitud>/autorizar-solicitud', views.autorizarSolicitud, name="autorizarSolicitudes"),
    #Prenominas
    path('Prenominas/solicitudes', views.Tabla_solicitudes_prenomina, name='Prenominas_solicitudes'),
    path('revisar/<int:pk>/', views.Prenomina_Solicitud_Revisar, name='Prenomina_solicitud_revisar'),
    #path('revisar_ajax/<int:pk>/', views.prenomina_solicitudes_revisar_ajax, name='Prenomina_solicitudes_revisar_ajax'),
    #path('autorizar-solicutud/forbidden', views.forbidden, name="forbidden")
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
