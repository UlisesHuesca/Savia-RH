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
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Sum

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

    
    #Para guardar la solicitud
    if request.method == "POST":     
        folio = request.POST.get('folio')
        solicitudForm = SolicitudForm(request.POST)
        empleados = Perfil.objects.filter(distrito_id = usuario.distrito.id ).order_by('nombres')
        bonoSolicitadoForm = BonoSolicitadoForm(request.POST)
        bonoSolicitadoForm.fields["trabajador"].queryset = empleados 
        
        #validación de los formularios
        if solicitudForm.is_valid() and bonoSolicitadoForm.is_valid():
            #total = BonoSolicitado.objects.filter(solicitud_id = 2).aggregate(total=Sum('cantidad'))['total']
            #print(total)
             
            #obtener los datos de los formularios
            bono = solicitudForm.cleaned_data['bono']
            trabajador = bonoSolicitadoForm.cleaned_data['trabajador']
            puesto = bonoSolicitadoForm.cleaned_data['puesto']
            cantidad = bonoSolicitadoForm.cleaned_data['cantidad']
            verificar_solicitud = Solicitud.objects.filter(folio=folio).values_list("id","folio").first()
            
            #verifica si el folio ya existe - es para agregar mas bonos a la misma solicitud en el mismo flujo
            if verificar_solicitud is not None:  
                #Existe la solicitud
                                
                empleados = Perfil.objects.filter(distrito_id = usuario.distrito.id ).order_by('nombres')
                bonoSolicitadoForm = BonoSolicitadoForm()
                bonoSolicitadoForm.fields["trabajador"].queryset = empleados
                  
                #Agregar un bono a la solicitud correspondiente                           
                BonoSolicitado.objects.create(
                    solicitud_id = verificar_solicitud[0],
                    trabajador_id = trabajador.id,
                    puesto_id = puesto.id,
                    distrito_id = usuario.distrito.id,
                    cantidad = cantidad,
                    fecha = datetime.now()
                )
                
                #Actuliza la cantidad del total de la solicitud 
                total = BonoSolicitado.objects.filter(solicitud_id = verificar_solicitud[0]).aggregate(total=Sum('cantidad'))['total']                 
                Solicitud.objects.filter(pk=verificar_solicitud[0]).update(total=total)
               
                messages.success(request, "El bono se ha agregado a la solicitud correctamente")
                                
                buscar_Solicitud = Solicitud.objects.filter(folio=folio).values_list("id").first()
                datos_bonos_solicitud = BonoSolicitado.objects.filter(solicitud_id = buscar_Solicitud)
                
                contexto = {
                    'folio':verificar_solicitud[1],
                    'usuario':usuario,
                    'solicitante':solicitante,
                    'solicitudForm':solicitudForm,
                    'bonoSolicitadoForm':bonoSolicitadoForm,
                    'solicitud':verificar_solicitud,
                    'datos_bonos_solicitud':datos_bonos_solicitud,
                    'total':total
                }
                return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)
            else:
                #No existe la solicitud
                
                #se crea la solicitud
                solicitud = Solicitud.objects.create(
                    folio = folio,
                    solicitante_id = solicitante.id,
                    bono_id = bono.id,
                    total = cantidad,
                    fecha = datetime.now()
                )
                
                #se crea el bono solicitado
                BonoSolicitado.objects.create(
                    solicitud_id = solicitud.id,
                    trabajador_id = trabajador.id,
                    puesto_id = puesto.id,
                    distrito_id = usuario.distrito.id,
                    cantidad = cantidad,
                    fecha = datetime.now()
                )

                
                messages.success(request, "La solicitud se ha creado correctamente")
                
                valor_bono = bono.id
                solicitudForm = SolicitudForm(initial={'bono': valor_bono}) 
        
                #se llama el formulario para el bono que se va a agregar
                bonoSolicitadoForm = BonoSolicitadoForm()
                #se filtra por distrito
                bonoSolicitadoForm.fields["trabajador"].queryset = empleados
                
                #busca los bonos solicitados de la solicitud correspondiente
                buscar_Solicitud = Solicitud.objects.filter(folio=folio).values_list("id").first()
                datos_bonos_solicitud = BonoSolicitado.objects.filter(solicitud_id = buscar_Solicitud)
                
                contexto = {
                    'usuario':usuario,
                    'solicitante':solicitante,
                    'solicitudForm':solicitudForm,
                    'bonoSolicitadoForm':bonoSolicitadoForm,
                    'datos_bonos_solicitud':datos_bonos_solicitud,
                    'folio':folio,
                    'total':solicitud.total
                }
                return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)  
        #se muestran los errores de validaciones      
        else:
            buscar_solicitud = Solicitud.objects.filter(folio=folio).values_list("id","total").first()
            datos_bonos_solicitud = BonoSolicitado.objects.filter(solicitud_id = buscar_solicitud[0])
            contexto = {
                'usuario':usuario,
                'solicitante':solicitante,
                'solicitudForm':solicitudForm,
                'bonoSolicitadoForm':bonoSolicitadoForm,
                'folio':folio,
                'datos_bonos_solicitud':datos_bonos_solicitud,
                'total':buscar_solicitud[1]
            }
            return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)
    #Es metodo GET - carga el formulario
    else:
        #Genera el número de folio automaticamente
        ultimo_registro = Solicitud.objects.values('id').last()
        if ultimo_registro is not None:
            folio = ultimo_registro['id'] + 1 
        else:
            folio = 1
        #se obtienen los bonos que pertenecen al bono varillero y se ordenan por nombre
        solicitudForm = SolicitudForm()
        #se obtienen los empleados por distrito, se refiere que solamente el supervisor puede ver de su distrito
        empleados = Perfil.objects.filter(distrito_id = usuario.distrito.id ).order_by('nombres')
        #se llama el formulario para el bono que se va a solicitar
        bonoSolicitadoForm = BonoSolicitadoForm()
        #se filtra por distrito
        bonoSolicitadoForm.fields["trabajador"].queryset = empleados
        
        contexto = {
            'usuario':usuario,
            'solicitante':solicitante,
            'solicitudForm':solicitudForm,
            'bonoSolicitadoForm':bonoSolicitadoForm,
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
            
    
    
    

