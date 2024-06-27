from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from prenomina import views

urlpatterns = [
    path('Prenomina', views.Tabla_prenomina, name='Prenomina'),
    path('revisar/<int:pk>/', views.PrenominaRevisar, name='Prenomina_revisar'),
    path('registrar_rango_incidencias/<int:pk>/', views.registrar_rango_incidencias, name='registrar_rango_incidencias'),
    path('filtrar_prenominas/<int:pk>/', views.filtrar_prenominas, name="filtrar_prenominas")
    
    #path('Perfil/Baja/<int:pk>/', views.Baja_empleado, name='Baja_empleado'),  
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)