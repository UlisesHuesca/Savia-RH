from django.shortcuts import render,redirect
#verificar autenticacion del usuario
from django.contrib.auth.decorators import login_required
#se importa los modelos de la otra app
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.core.serializers import serialize
import json
from datetime import datetime
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Sum
import logging
from proyecto.models import Distrito,Perfil,Puesto,UserDatos
from .models import Categoria,Subcategoria,Bono,Solicitud,BonoSolicitado,Requerimiento
from .forms import SolicitudForm, BonoSolicitadoForm, RequerimientoForm

#Pagina inicial de los esquemas de los bonos
@login_required(login_url='user-login')
def inicio(request):
    bonos = Categoria.objects.all();
    
    context= {
        'bonos':bonos,
    }
    
    return render(request,'esquema/inicio.html',context)

#Listar las solicitudes
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
    #El numero de folio automatico   
    folio = request.POST.get('folio')
    #se cargan los formularios con los valores del post
    solicitudForm = SolicitudForm()      
    bonoSolicitadoForm = BonoSolicitadoForm()
    #solicitudForm = SolicitudForm(request.POST)      
    #bonoSolicitadoForm = BonoSolicitadoForm(request.POST)
    requerimientoForm = RequerimientoForm()
    #se hace una consulta con los empleados del distrito que pertenecen
    empleados = Perfil.objects.filter(distrito_id = usuario.distrito.id).exclude(numero_de_trabajador = usuario.numero_de_trabajador).order_by('nombres')
    #se carga el formulario en automatico definiendo filtros
    bonoSolicitadoForm.fields["trabajador"].queryset = empleados 
    
    #Para guardar la solicitud
    if request.method == "POST":
        #Para guardar archivos (requerimientos) 
        if 'btn_archivos' in request.POST:
            print("Formluario Archivos")
            requerimientoForm = RequerimientoForm(request.POST, request.FILES)
            archivos = request.FILES.getlist('url')
            folio = request.POST.get('valor')
            #Validar los archivos
            if requerimientoForm.is_valid():
                #Se crea la solicitud  
                Solicitud.objects.create(
                    folio = folio,
                    solicitante_id = solicitante.id,
                    total = 0.00,
                    fecha = datetime.now(),
                )
                #Se recorren los archivos para ser almacenados
                for archivo in archivos:
                    Requerimiento.objects.create(
                        solicitud_id = folio,
                        fecha = datetime.now(),
                        url = archivo,
                    )
                    
                contexto = {
                    'usuario':usuario,
                    'solicitante':solicitante,
                    'solicitudForm':solicitudForm,
                    'bonoSolicitadoForm':bonoSolicitadoForm,
                    'requerimientoForm':requerimientoForm,
                    'folio':folio
                }
                
                messages.success(request, "Los archivos se subieron correctamente")
                
                return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)
            else:
                contexto = {
                    'usuario':usuario,
                    'solicitante':solicitante,
                    'solicitudForm':solicitudForm,
                    'bonoSolicitadoForm':bonoSolicitadoForm,
                    'requerimientoForm':requerimientoForm,
                    'folio':folio
                }
                return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)
        elif 'btn_agregar' in request.POST:  
            print("Formluario Bono")
            solicitudForm = SolicitudForm(request.POST)      
            bonoSolicitadoForm = BonoSolicitadoForm(request.POST)       
            
            #validación de los formularios
            if solicitudForm.is_valid() and bonoSolicitadoForm.is_valid():
                #obtener los datos de los formularios
                bono = solicitudForm.cleaned_data['bono']
                trabajador = bonoSolicitadoForm.cleaned_data['trabajador']
                puesto = bonoSolicitadoForm.cleaned_data['puesto']
                cantidad = bonoSolicitadoForm.cleaned_data['cantidad']
                #consulta la solicitud en la bd
                verificar_solicitud = Solicitud.objects.filter(folio=folio).values_list("id","folio").first()
                
                #verifica si el folio ya existe - es para agregar mas bonos a la misma solicitud en el mismo flujo
                if verificar_solicitud is not None:  
                    #Existe la solicitud
                    empleados = Perfil.objects.filter(distrito_id = usuario.distrito.id).exclude(numero_de_trabajador = usuario.numero_de_trabajador).order_by('nombres')
                    #le paso el form vacio para que puede agregar mas bonos
                    bonoSolicitadoForm = BonoSolicitadoForm()
                    bonoSolicitadoForm.fields["trabajador"].queryset = empleados
                    
                    #busca la solicitud
                    obj_solicitud = get_object_or_404(Solicitud, pk=folio)
                    #agrega el bono
                    obj_solicitud.bono_id = bono
                    #lo actualiza
                    obj_solicitud.save()
                    
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
                    total = BonoSolicitado.objects.filter(solicitud_id = verificar_solicitud[0]).values("cantidad").aggregate(total=Sum('cantidad'))['total']                 
                    Solicitud.objects.filter(pk=verificar_solicitud[0]).values("total").update(total=total)
                
                    messages.success(request, "El bono se ha agregado a la solicitud correctamente")
                    
                    #Actualiza los bonos enviados a la vista
                    buscar_solicitud = Solicitud.objects.filter(folio=folio).values_list("id").first()
                    datos_bonos_solicitud = BonoSolicitado.objects.filter(solicitud_id = buscar_solicitud)
                    
                    contexto = {
                        'folio':verificar_solicitud[1],
                        'usuario':usuario,
                        'solicitante':solicitante,
                        'solicitudForm':solicitudForm,
                        'bonoSolicitadoForm':bonoSolicitadoForm,
                        'solicitud':verificar_solicitud,
                        'datos_bonos_solicitud':datos_bonos_solicitud,
                        'requerimientoForm':requerimientoForm,
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
                        'requerimientoForm':requerimientoForm,
                        'datos_bonos_solicitud':datos_bonos_solicitud,
                        'folio':folio,
                        'total':solicitud.total
                    }
                    return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)  
            #se muestran los errores de validaciones      
            else:
                buscar_solicitud = Solicitud.objects.filter(folio=folio).values_list("id","total").first()
                
                empleados = Perfil.objects.filter(distrito_id = usuario.distrito.id).exclude(numero_de_trabajador = usuario.numero_de_trabajador).order_by('nombres')
                #le paso el form vacio para que puede agregar mas bonos
                #bonoSolicitadoForm = BonoSolicitadoForm()
                bonoSolicitadoForm.fields["trabajador"].queryset = empleados
                
                if buscar_solicitud is not None:
                    datos_bonos_solicitud = BonoSolicitado.objects.filter(solicitud_id = buscar_solicitud[0])
                    total = buscar_solicitud[1]
                else:
                    total = None
                    datos_bonos_solicitud = None
            
                contexto = {
                    'usuario':usuario,
                    'solicitante':solicitante,
                    'solicitudForm':solicitudForm,
                    'bonoSolicitadoForm':bonoSolicitadoForm,
                    'requerimientoForm':requerimientoForm,
                    'folio':folio,
                    'datos_bonos_solicitud':datos_bonos_solicitud,
                    'total':total
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
       
        empleados = Perfil.objects.filter(distrito_id = usuario.distrito.id).exclude(numero_de_trabajador = usuario.numero_de_trabajador).order_by('nombres')
        
        #formulario para la carga de archivos
        requerimientoForm = RequerimientoForm()
        #se llama el formulario para el bono que se va a solicitar
        bonoSolicitadoForm = BonoSolicitadoForm()
        #se filtra por distrito
        bonoSolicitadoForm.fields["trabajador"].queryset = empleados
        
        contexto = {
            'usuario':usuario,
            'solicitante':solicitante,
            'solicitudForm':solicitudForm,
            'bonoSolicitadoForm':bonoSolicitadoForm,
            'requerimientoForm':requerimientoForm,
            'folio':folio
        }
        return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)

@login_required(login_url='user-login')
def cargarArchivos(request):
    if request.method == "POST":
        requerimientoForm = RequerimientoForm(request.POST, request.FILES)
        archivos = request.FILES.getlist('url')
        
        if requerimientoForm.is_valid():
            
            #se crea la solicitud
            solicitud = Solicitud.objects.create(
                folio = 1,
                solicitante_id = 1360,
                bono_id = 1,
                total = 0.00,
                fecha = datetime.now(),
            )
            
            for archivo in archivos:
                Requerimiento.objects.create(
                    solicitud_id = 6,
                    fecha = datetime.now(),
                    url = archivo,
                )
            
            """se almacena un archivo
            requerimiento = requerimientoForm.save(commit=False)
            requerimiento.fecha = datetime.now()
            #requerimiento.url = archivo
            requerimiento.solicitud_id = 5
            requerimiento.save()
            """            
            return HttpResponse('Fotos subidas correctamente')
        else:
            return HttpResponse("error de validacion")

#para remover bonos agregados
@login_required(login_url='user-login')
def removerBono(request,bono_id):
    if request.method == "POST":
        try:
            bono = BonoSolicitado.objects.get(pk=bono_id)
            solicitud = Solicitud.objects.get(pk=bono.solicitud_id)
            solicitud.total -= bono.cantidad
            solicitud.save()
            bono.delete()
            return JsonResponse({'bono_id': bono_id,'total':solicitud.total} ,status=200, safe=True)
        except:
            return JsonResponse({'mensaje': 'Objeto no encontrado'}, status=404,safe=True)

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
            
    
    
    

