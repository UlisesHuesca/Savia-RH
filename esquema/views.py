from django.shortcuts import render
#verificar autenticacion del usuario
from django.contrib.auth.decorators import login_required
#se importa los modelos de la otra app
from django.shortcuts import get_object_or_404
from proyecto.models import Distrito,Perfil,Puesto,UserDatos
from .models import Categoria,Subcategoria

#Pagina inicial de los esquemas de los bonos
@login_required(login_url='user-login')
def inicio(request):
    bonos = Categoria.objects.all();
    
    context= {
        'bonos':bonos,
    }
    
    return render(request,'esquema/inicio.html',context)

@login_required(login_url='user-login')
def listarBonosVarilleros(request):
    return render(request,'esquema/bonos_varilleros/listar.html')

@login_required(login_url='user-login')
def crearSolicitudBonosVarilleros(request):
    usuario = get_object_or_404(UserDatos,user_id = request.user.id)
    solicitante = get_object_or_404(Perfil,numero_de_trabajador = usuario.numero_de_trabajador)
    subcategorias = Subcategoria.objects.all().order_by('nombre') #se refieren a los bonos que pertenecen de varillero
    
    contexto = {
        'solicitante':solicitante,
        'subcategorias':subcategorias
    }
    
    return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)

