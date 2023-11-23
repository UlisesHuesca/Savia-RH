from django.urls import path
from . import views

urlpatterns = [
    path('bonos_varilleros/', views.listarBonosVarilleros, name='listarBonosVarilleros'),
]