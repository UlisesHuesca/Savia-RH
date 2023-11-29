from django.shortcuts import render,redirect
#verificar autenticacion del usuario
from django.contrib.auth.decorators import login_required
#se importa los modelos de la otra app
from django.shortcuts import get_object_or_404
from proyecto.models import Distrito,Perfil,Puesto,UserDatos
from .models import Categoria,Subcategoria,Bono,Solicitud,BonoSolicitado
from .forms import SolicitudForm, BonoSolicitadoForm
from django.http import JsonResponse
from django.core.serializers import serialize
import json
from datetime import datetime

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

#para crear solicitudes de bonos
@login_required(login_url='user-login')
def crearSolicitudBonosVarilleros(request):
    #se obtiene el usuario logueado
    usuario = get_object_or_404(UserDatos,user_id = request.user.id)
    #se obtiene el perfil del usuario logueado
    solicitante = get_object_or_404(Perfil,numero_de_trabajador = usuario.numero_de_trabajador)
    
    if request.method == "POST":     
        data = json.loads(request.body)

        solicitud = Solicitud.objects.create(
            folio = 2,
            solicitante_id = solicitante.id,
            bono_id = data['bono'],
            total = data['cantidad'],
            fecha = datetime.now(),
        )
        
        bono = BonoSolicitado.objects.create(
            solicitud_id = solicitud.id,
            trabajador_id = data['empleado'],
            puesto_id = data['puesto'],
            distrito_id = usuario.distrito.id,
            cantidad = data['cantidad'],
            fecha = datetime.now()
            
            
            
        )
        
        
       
        
        datos = {
            'status':200,
            'bono':bono.id
        }
        
        return JsonResponse(datos)
        
        #data = {"solicitante":solicitante.id,'folio':data['folio'],'bono':data['bono'],'total':data['cantidad'],'fecha':datetime.now()}
        #solicitud, created = Solicitud.objects.get_or_create(folio = data['folio'])
        #if created:
        """
            solicitud.folio = data['folio']
            solicitud.solicitante_id = solicitante.id
            solicitud.bono_id = data['bono']
            solicitud.total = data['cantidad']
            solicitud.fecha = datetime.now()
                            
            #solicitud = solicitud.save()
            #return JsonResponse(solicitud,safe=False,status = 200)
            return JsonResponse({'mjs':'creado'})
        """
    else:
        #se obtienen los bonos que pertenecen al bono varillero y se ordenan por nombre
        #subcategorias = Subcategoria.objects.filter(esquema_categoria_id=1).order_by('nombre')
        solicitudForm = SolicitudForm()
        #se obtienen los empleados por distrito, se refiere que solamente el supervisor puede ver de su distrito
        #empleados = Perfil.objects.filter(distrito_id = solicitante.distrito_id ).order_by('nombres')
        empleados = Perfil.objects.filter(distrito_id = 2 ).order_by('nombres')
        #puestos = Puesto.objects.filter(pk__in=[176,177,178,138])
        #print(puestos)
        bonoSolicitadoForm = BonoSolicitadoForm()
        bonoSolicitadoForm.fields["trabajador"].queryset = empleados
        #bonoSolicitadoForm.fields["puesto"].queryset = puestos
        
       
        folio = 1 #Solicitud.objects.count() + 1
        
        contexto = {
            'usuario':usuario,
            'solicitante':solicitante,
            'solicitudForm':solicitudForm,
            'bonoSolicitadoForm':bonoSolicitadoForm,
            #'subcategorias':subcategorias,
            #'empleados':empleados,
            #'puestos':puestos,
            'folio':folio
        }
        
        return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)
        

#solicita la cantidad de un bono en especifico de la tabla de esquema de bonos definidos
@login_required(login_url='user-login')
def solicitarEsquemaBono(request):
    if request.method == "POST":
        #se obtiene el usuario logueado
        usuario = get_object_or_404(UserDatos,user_id = request.user.id)
        #se obtienen los datos enviados del servidor            
        data = json.loads(request.body)
            
        #response_data = {'message': data}
        #return JsonResponse(response_data,safe=False)
            
        esquema_bono = Bono.objects.filter(esquema_subcategoria_id = data['bono'], distrito_id = usuario.distrito.id, puesto_id = data['puesto'])
        serialized_data = serialize("json", esquema_bono)
        serialized_data = json.loads(serialized_data)
        return JsonResponse(serialized_data, safe=False, status=200)

        #datos = {'mensaje': 'comunicacion con el back'}
        #return JsonResponse(datos)
            
    
    
    

