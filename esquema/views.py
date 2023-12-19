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
import os
import logging
from proyecto.models import Distrito,Perfil,Puesto,UserDatos
from .models import Categoria,Subcategoria,Bono,Solicitud,BonoSolicitado,Requerimiento
from .forms import SolicitudForm, BonoSolicitadoForm, RequerimientoForm
from django.db import connection

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
    #se obtiene el usuario logueado
    usuario = get_object_or_404(UserDatos,user_id = request.user.id)
    #se obtiene el perfil del usuario logueado
    solicitante = get_object_or_404(Perfil,numero_de_trabajador = usuario.numero_de_trabajador)
    #se obtienen las solicitudes
    solicitudes = Solicitud.objects.filter(solicitante_id = solicitante.id).order_by('-id')
    
    contexto = {
        'usuario':usuario,
        'solicitante':solicitante,
        'solicitudes':solicitudes
    }
    
    return render(request,'esquema/bonos_varilleros/listar.html',contexto)


def obtener_valor_autoincremental_mysql():
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{Solicitud._meta.db_table}'")
        ultimo_valor_autoincremental = cursor.fetchone()[0]

    return ultimo_valor_autoincremental

def consulta_autoincrement():
    with connection.cursor() as cursor:
        query = "SHOW TABLE STATUS LIKE 'esquema_solicitud';"
        cursor.execute(query)
        resultados = cursor.fetchall()
        tupla_interna = resultados[0]
        valor = (tupla_interna[10])
        return valor
        

#para crear solicitudes de bonos
@login_required(login_url='user-login')
def crearSolicitudBonosVarilleros(request):
    #se obtiene el usuario logueado
    usuario = get_object_or_404(UserDatos,user_id = request.user.id)
    #se obtiene el perfil del usuario logueado
    solicitante = get_object_or_404(Perfil,numero_de_trabajador = usuario.numero_de_trabajador) 
    #print("null",solicitante)
    #se cargan los formularios con los valores del post
    solicitudForm = SolicitudForm()      
    bonoSolicitadoForm = BonoSolicitadoForm()
    requerimientoForm = RequerimientoForm()
    #se hace una consulta con los empleados del distrito que pertenecen
    empleados = Perfil.objects.filter(distrito_id = usuario.distrito.id).exclude(numero_de_trabajador = usuario.numero_de_trabajador).order_by('nombres')
    #se carga el formulario en automatico definiendo filtros
    bonoSolicitadoForm.fields["trabajador"].queryset = empleados 
    
    #Para guardar la solicitud
    if request.method == "POST":
        
        #obtiene el folio independientemente del formulario
        if request.POST.get('valor') is not None:
            folio = request.POST.get('valor')
        else:        
            folio = request.POST.get('folio')
        
        #obtiene un queryset de los archivos de la solicitud
        lista_archivos = Requerimiento.objects.filter(solicitud_id = folio).values("id","url")
        #obtiene los bonos que han sido agregados a la solicitud
        datos_bonos_solicitud = BonoSolicitado.objects.filter(solicitud_id = folio)
        
        #se carga el valor del bono inicial 
        valor_bono = Solicitud.objects.filter(pk=folio).values("bono_id").first()
        if valor_bono is not None:
            solicitudForm = SolicitudForm(initial={'bono': valor_bono["bono_id"]}) 
                    
        #se obtiene la cantidad total
        buscar_solicitud = Solicitud.objects.filter(folio=folio).values_list("id","total").first()
        if buscar_solicitud is not None:
            total = buscar_solicitud[1]
        else:
            total = None  
        print(total)
        
        if 'btn_archivos' in request.POST:      
            #Se envian los formularios con datos                   
            requerimientoForm = RequerimientoForm(request.POST, request.FILES)  
            archivos = request.FILES.getlist('url')
              
            #validacion     
            if requerimientoForm.is_valid():
                
                verificar_solicitud = Solicitud.objects.filter(folio = folio).values("folio")                 
                
                if not verificar_solicitud.exists(): 
                    
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
                    'lista_archivos':lista_archivos,
                    'datos_bonos_solicitud':datos_bonos_solicitud,
                    'total':total,
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
                    'lista_archivos':lista_archivos,
                    'datos_bonos_solicitud':datos_bonos_solicitud,
                    'total':total,
                    'folio':folio
                }
                
                return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)
        
        elif 'btn_agregar' in request.POST:  
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
                                        
                    #busca la solicitud
                    obj_solicitud = get_object_or_404(Solicitud, pk=folio)
                    if obj_solicitud.bono_id is None:
                        #agrega el bono
                        obj_solicitud.bono_id = bono
                        #lo actualiza
                        obj_solicitud.save()
                    
                    verificar_puesto = BonoSolicitado.objects.filter(solicitud_id = verificar_solicitud[0], puesto_id=puesto).values("puesto_id").first()
                  
                    #no seleccionar el mismo puesto 2 veces
                    if verificar_puesto is None:
                                              
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
                        
                        #se llama el formulario vacio para que pueda agregar mas bonos
                        bonoSolicitadoForm = BonoSolicitadoForm()
                        
                    else:
                        messages.error(request, "No se puede agregar el mismo puesto")
                        bonoSolicitadoForm = BonoSolicitadoForm()
                    
                    bonoSolicitadoForm.fields["trabajador"].queryset = empleados 
                                             
                    contexto = {
                        'folio':verificar_solicitud[1],
                        'usuario':usuario,
                        'solicitante':solicitante,
                        'solicitudForm':solicitudForm,
                        'bonoSolicitadoForm':bonoSolicitadoForm,
                        'solicitud':verificar_solicitud,
                        'datos_bonos_solicitud':datos_bonos_solicitud,
                        'requerimientoForm':requerimientoForm,
                        'lista_archivos':lista_archivos,
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
                                        
                    contexto = {
                        'usuario':usuario,
                        'solicitante':solicitante,
                        'solicitudForm':solicitudForm,
                        'bonoSolicitadoForm':bonoSolicitadoForm,
                        'requerimientoForm':requerimientoForm,
                        'datos_bonos_solicitud':datos_bonos_solicitud,
                        'lista_archivos':lista_archivos,
                        'folio':folio,
                        'total':solicitud.total
                    }
                    return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)  
            #se muestran los errores de validaciones      
            else:
                bonoSolicitadoForm.fields["trabajador"].queryset = empleados 
                contexto = {
                    'usuario':usuario,
                    'solicitante':solicitante,
                    'solicitudForm':solicitudForm,
                    'bonoSolicitadoForm':bonoSolicitadoForm,
                    'requerimientoForm':requerimientoForm,
                    'folio':folio,
                    'datos_bonos_solicitud':datos_bonos_solicitud,
                    'lista_archivos':lista_archivos,
                    'total':total
                }
                return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)
    #Es metodo GET - Carga los formularios
    else:
        #Genera el número de folio automaticamente
        ultimo_registro = consulta_autoincrement()
        print(ultimo_registro)
        
        #ultimo_registro = Solicitud.objects.latest('id');
        #print(ultimo_registro.id)
        if ultimo_registro is not None:
            folio = ultimo_registro + 1
        else:
            folio = 1
        
        #Se envia una lista vacia de archivos al contexto
        lista_archivos = None
        
        contexto = {
            'usuario':usuario,
            'solicitante':solicitante,
            'solicitudForm':solicitudForm,
            'bonoSolicitadoForm':bonoSolicitadoForm,
            'requerimientoForm':requerimientoForm,
            'lista_archivos':lista_archivos,
            'folio':folio
        }
        
        return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)

def updateSolicitudBonosVarilleros(request,solicitud_id):
    solicitud = get_object_or_404(Solicitud, pk=solicitud_id)
    
    usuario = get_object_or_404(UserDatos,user_id = request.user.id)
    solicitante = get_object_or_404(Perfil,numero_de_trabajador = usuario.numero_de_trabajador) 
        
    requerimientoForm = RequerimientoForm()
    solicitudForm = SolicitudForm(initial={'bono': solicitud.bono_id})
    bonoSolicitadoForm = BonoSolicitadoForm()
    datos_bonos_solicitud = BonoSolicitado.objects.filter(solicitud_id = solicitud.id)
        
    empleados = Perfil.objects.filter(distrito_id = usuario.distrito.id).exclude(numero_de_trabajador = usuario.numero_de_trabajador).order_by('nombres')
    bonoSolicitadoForm.fields["trabajador"].queryset = empleados 
    lista_archivos = Requerimiento.objects.filter(solicitud_id = solicitud.id).values("id","url")
    
    if request.method == 'POST':    
        
        if 'btn_archivos' in request.POST:                 
            
            requerimientoForm = RequerimientoForm(request.POST, request.FILES)  
            archivos = request.FILES.getlist('url')
            
            if requerimientoForm.is_valid():                 
                for archivo in archivos:
                    Requerimiento.objects.create(
                        solicitud_id = solicitud.id,
                        fecha = datetime.now(),
                        url = archivo,
                    )
                    
                messages.success(request, "Los archivos se han subido correctamente")
            
                contexto = {
                    'requerimientoForm':requerimientoForm,
                    'solicitudForm':solicitudForm,
                    'bonoSolicitadoForm': bonoSolicitadoForm,
                    'solicitud':solicitud,
                    'solicitante':solicitante,
                    'datos_bonos_solicitud':datos_bonos_solicitud,
                    'total':solicitud.total,
                    'lista_archivos':lista_archivos
                }
            
                return render(request,'esquema/bonos_varilleros/editar_solicitud.html',contexto)
            
            else:
                print('error de validaicion del archivo')
                contexto = {
                    'requerimientoForm':requerimientoForm,
                    'solicitudForm':solicitudForm,
                    'bonoSolicitadoForm': bonoSolicitadoForm,
                    'solicitud':solicitud,
                    'solicitante':solicitante,
                    'datos_bonos_solicitud':datos_bonos_solicitud,
                    'total':solicitud.total,
                    'lista_archivos':lista_archivos
                }
                 
                return render(request,'esquema/bonos_varilleros/editar_solicitud.html',contexto)
        
        elif 'btn_agregar' in request.POST:
            
            solicitudForm = SolicitudForm(request.POST)      
            bonoSolicitadoForm = BonoSolicitadoForm(request.POST)
            bonoSolicitadoForm.fields["trabajador"].queryset = empleados 
            
            if solicitudForm.is_valid() and bonoSolicitadoForm.is_valid():
                #bono = solicitudForm.cleaned_data['bono']
                trabajador = bonoSolicitadoForm.cleaned_data['trabajador']
                puesto = bonoSolicitadoForm.cleaned_data['puesto']
                cantidad = bonoSolicitadoForm.cleaned_data['cantidad']
            
                verificar_puesto = BonoSolicitado.objects.filter(solicitud_id = solicitud.id, puesto_id=puesto).values("puesto_id").first()
                
                
                if verificar_puesto is None:
                    BonoSolicitado.objects.create(
                        solicitud_id = solicitud.id,
                        trabajador_id = trabajador.id,
                        puesto_id = puesto.id,
                        distrito_id = usuario.distrito.id,
                        cantidad = cantidad,
                        fecha = datetime.now()
                    )
                        
                    total = BonoSolicitado.objects.filter(solicitud_id = solicitud.id).values("cantidad").aggregate(total=Sum('cantidad'))['total']                 
                    Solicitud.objects.filter(pk=solicitud.id).values("total").update(total=total)
                    messages.success(request, "El bono se ha agregado a la solicitud correctamente")    
                    bonoSolicitadoForm = BonoSolicitadoForm()
                    bonoSolicitadoForm.fields["trabajador"].queryset = empleados 
                else:
                    messages.error(request, "No se puede agregar el mismo puesto")
                    
                contexto = {
                        'requerimientoForm':requerimientoForm,
                        'solicitudForm':solicitudForm,
                        'bonoSolicitadoForm': bonoSolicitadoForm,
                        'solicitud':solicitud,
                        'solicitante':solicitante,
                        'datos_bonos_solicitud':datos_bonos_solicitud,
                        'total':solicitud.total,
                        'lista_archivos':lista_archivos
                }
                return render(request,'esquema/bonos_varilleros/editar_solicitud.html',contexto)
                
            else:
                 
                contexto = {
                    'requerimientoForm':requerimientoForm,
                    'solicitudForm':solicitudForm,
                    'bonoSolicitadoForm': bonoSolicitadoForm,
                    'solicitud':solicitud,
                    'solicitante':solicitante,
                    'datos_bonos_solicitud':datos_bonos_solicitud,
                    'total':solicitud.total,
                    'lista_archivos':lista_archivos
                }
        
                return render(request,'esquema/bonos_varilleros/editar_solicitud.html',contexto)
        
    else:
        contexto = {
            'requerimientoForm':requerimientoForm,
            'solicitudForm':solicitudForm,
            'bonoSolicitadoForm': bonoSolicitadoForm,
            'solicitud':solicitud,
            'solicitante':solicitante,
            'datos_bonos_solicitud':datos_bonos_solicitud,
            'total':solicitud.total,
            'lista_archivos':lista_archivos
        }
        
        return render(request,'esquema/bonos_varilleros/editar_solicitud.html',contexto)
    
    
#para eliminar solicitudes
@login_required(login_url='user-login')
def eliminarSolicitudBonosVarilleros(request,solicitud_id):
    if request.method == 'POST':
        #Se obtiene la solicitud
        solicitud_obj = get_object_or_404(Solicitud, pk = solicitud_id)
        
        #obtener los bonos a eliminar
        bonos = BonoSolicitado.objects.filter(solicitud_id = solicitud_obj.id)
        #se eliminan
        bonos.delete()
        
        #obtener los requerimientos (archivos)
        requerimientos = Requerimiento.objects.filter(solicitud_id = solicitud_obj.id)
        
        #se eliminan los archivos del static
        for archivo in requerimientos:
            if os.path.isfile(archivo.url.path):
                #print(archivo.url.path)
                os.remove(archivo.url.path)
                archivo.delete()
            
        #se eliminan
        requerimientos.delete()
        
        #se elimina la solicitud al final por las fks
        solicitud_obj.delete();
        
        data = {
                 'solicitud':solicitud_obj.folio,
        }
         
        return JsonResponse(data,safe=True,status=200)
    
#para ver detalles de la solicitud
@login_required(login_url='user-login')
def verDetallesSolicitud(request,solicitud_id):
    #se obtiene el usuario logueado
    usuario = get_object_or_404(UserDatos,user_id = request.user.id)
    #se obtiene el perfil del usuario logueado
    solicitante = get_object_or_404(Perfil,numero_de_trabajador = usuario.numero_de_trabajador)
    #se obtiene la solicitud, los bonos y lo requerimientos de esa solicitud
    solicitud = get_object_or_404(Solicitud,pk=solicitud_id)
    bonos = BonoSolicitado.objects.filter(solicitud_id = solicitud.id)
    requerimientos = Requerimiento.objects.filter(solicitud_id = solicitud.id)
        
    contexto = {
        "solicitante":solicitante,
        "solicitud":solicitud,
        "bonos":bonos,
        "requerimientos": requerimientos,
    }
    
    return render(request,'esquema/bonos_varilleros/detalles_solicitud.html',contexto)
    

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

#para remover archivos agregados
@login_required(login_url='user-login')
def removerArchivo(request,archivo_id):
    if request.method == "POST":
        try:
            archivo = get_object_or_404(Requerimiento,pk=archivo_id)
            
            if os.path.isfile(archivo.url.path):
                os.remove(archivo.url.path)
                
            archivo.delete()
                        
            return JsonResponse({"archivo_id":archivo_id},status=200,safe=False)
        except:
            return JsonResponse({'mensaje':'objecto no encontrado'},status=404,safe=True)    

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
            
    
    
    

