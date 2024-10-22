# urls.py
from django.urls import path
from . import views  
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
        #Para vistas basadas en clases
    #path('perfiles/', PerfilListAPIView.as_view(), name='perfil-list'),
    #path('perfiles/<int:pk>/', PerfilDetailAPIView.as_view(), name='perfil-detail'),

    #Vistas basadas en funciones
    path('me/', views.me), #Ver propio email    
    path('admin-view/', views.admin_view),  #Vista para grupo determinado en el admin (group)
    path('perfiles/', views.perfil_list, name='perfil-list'), #Vista para pasar datos perfil RH a Savia 2
    path('perfiles/<int:pk>/', views.perfil_detail, name='perfil-detail'),#Vista para un perfil especifico
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),#Obtener token logeandote con un form con tu usuario
    path('perfiles_ingenieria/', views.perfil_list_ingenieria, name='perfil-ingenieria-list'),
    path('festivos_actual/', views.tabla_festivos_actual, name='tabla_festivos_actual'),
]