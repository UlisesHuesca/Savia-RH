from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from prenomina import views

urlpatterns = [
    path('Prenomina', views.Tabla_prenomina, name='Prenomina'),
    path('revisar/<int:pk>/', views.PrenominaRevisar, name='Prenomina_revisar'),
    path('programar_incidencias/<int:pk>', views.crear_rango_incidencias, name='crear_rango_incidencias')
    
    #path('programar_incidencias/<int:pk>/',views.programar_incidencias, name="programar_incidencias"),
    #path('programar_incapacidades/<int:pk>/',views.programar_incapacidades, name="programar_incapacidades")
    #path('crear_rango_incidencias/<int:pk>/',views.crear_rango_incidencias, name="crear_rango_incidencias")
    #path('Perfil/Baja/<int:pk>/', views.Baja_empleado, name='Baja_empleado'),  
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)