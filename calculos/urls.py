from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from calculos import views

urlpatterns = [
    path('calcular_prenomina', views.calcular_prenomina, name='calcular_prenomina'),
        
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)