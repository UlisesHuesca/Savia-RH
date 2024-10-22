from django.shortcuts import render
# views.py
from rest_framework import generics
from proyecto.models import Perfil, TablaFestivos
from .serializers import PerfilSerializer, PerfilIngenieriaSerializer, TablaFestivosSerializer
from rest_framework.decorators import api_view, renderer_classes, throttle_classes
from rest_framework.response import Response 
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import UserRateThrottle
from .throttles import TenCallsPerMinute
from django.core.paginator import Paginator, EmptyPage
from datetime import datetime

# Create your views here.
    #Vista basada en clases Vista para listar todos los perfiles
"""class PerfilListAPIView(generics.ListAPIView):
    queryset = Perfil.objects.all()
    serializer_class = PerfilSerializer

 Vista para obtener un perfil específico por su ID
class PerfilDetailAPIView(generics.RetrieveAPIView):
    queryset = Perfil.objects.all()"""

#Vistas basadas en funciones para listar todos los perfiles

    #Sin paginación
@api_view(['GET']) #Vista de perfiles para sistemas y rh con mucha información
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def perfil_list(request):
    if request.user.groups.filter(name='Api admin').exists():
        perfiles = Perfil.objects.filter(complete = True).order_by('numero_de_trabajador')  # Ordena por numero_de_trabajador
        serializer = PerfilSerializer(perfiles, many=True)
        return Response(serializer.data) 
    else:
        return Response({"message": "You are not authorized"}, 403)

@api_view(['GET']) #Vista de perfiles para ingenieria sin información sencible
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def perfil_list_ingenieria(request):
    perfiles = Perfil.objects.filter(complete = True).order_by('numero_de_trabajador')  # Ordena por numero_de_trabajador
    serializer = PerfilIngenieriaSerializer(perfiles, many=True)
    return Response(serializer.data) 

@api_view(['GET'])  # Vista para obtener días festivos del año actual
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def tabla_festivos_actual(request):
    current_year = datetime.now().year
    # Filtramos los días festivos del año actual
    festivos = TablaFestivos.objects.filter(dia_festivo__year=current_year)
    serializer = TablaFestivosSerializer(festivos, many=True)
    return Response(serializer.data)

    #Con paginación
"""@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes({UserRateThrottle})
def perfil_list(request):
    perfiles = Perfil.objects.all()  # Obtenemos todos los perfiles

    # Obtenemos los parámetros de paginación de la URL (con valores por defecto)
    page = request.query_params.get('page', 1)
    per_page = request.query_params.get('per_page', 10)
    
    ordering = request.query_params.get('ordering', 'numero_de_trabajador')
    perfiles = perfiles.order_by(ordering)

    # Aplicar paginación
    paginator = Paginator(perfiles, per_page)
    try:
        perfiles_paginated = paginator.page(page)
    except EmptyPage:
        perfiles_paginated = []

    # Serializar los datos paginados
    serializer = PerfilSerializer(perfiles_paginated, many=True)

    # Incluir metadatos sobre la paginación en la respuesta
    response_data = {
        'total_pages': paginator.num_pages,
        'current_page': int(page),
        'total_items': paginator.count,
        'per_page': int(per_page),
        'results': serializer.data
    }

    return Response(response_data)"""

#@api_view(['GET', 'POST'])
@api_view(['GET']) #Ver especificamente 1 perfil y añadir dato si se activa el post
@permission_classes([IsAuthenticated])
@throttle_classes({UserRateThrottle})
def perfil_detail(request, pk):
    if request.user.groups.filter(name='Api admin').exists():
        try:
            perfil = Perfil.objects.get(pk=pk)
            if request.method == 'GET':
                serializer = PerfilSerializer(perfil)
                return Response(serializer.data)
            elif request.method == 'POST':
                serializer = PerfilSerializer(perfil, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Perfil.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({"message": "You are not authorized"}, 403)
    
@api_view() #Ver el correo con el que se esta logeado el token
@permission_classes([IsAuthenticated])
def me(request):
    return Response(request.user.email)

@api_view()  #Ver so tienes permisos de admin para apis
@permission_classes([IsAuthenticated])
def admin_view(request):
    if request.user.groups.filter(name='Api admin').exists():
        return Response({"message": "Solo los admin ven esto"})
    else:
        return Response({"message": "You are not authorized"}, 403)