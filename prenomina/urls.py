from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from prenomina import views

urlpatterns = [
    path('Prenomina', views.Tabla_prenomina, name='Prenomina'),
    path('revisar/<int:pk>/', views.PrenominaRevisar, name='Prenomina_revisar'),
    path('revisar_ajax/<int:pk>/', views.prenomina_revisar_ajax, name='Prenomina_revisar_ajax'),
    #path('Perfil/Baja/<int:pk>/', views.Baja_empleado, name='Baja_empleado'),  

    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)