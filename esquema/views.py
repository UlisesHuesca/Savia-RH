from django.shortcuts import render

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
from revisar.models import AutorizarSolicitudes
from .forms import SolicitudForm, BonoSolicitadoForm, RequerimientoForm,AutorizarSolicitudesUpdateForm,AutorizarSolicitudesGerenteUpdateForm
from django.db import connection
from django.core.paginator import Paginator
from .filters import SolicitudFilter,AutorizarSolicitudesFilter
from django.db.models import Max
from django.db.models import Subquery, OuterRef
from django.http import Http404

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
    
    subconsulta_ultima_fecha = AutorizarSolicitudes.objects.values('solicitud_id').annotate(
            ultima_fecha=Max('created_at')
        ).filter(solicitud_id=OuterRef('solicitud_id')).values('ultima_fecha')[:1]
    
    #Si es usuario administrador de distrito matriz
    if usuario.distrito.id == 1 and usuario.tipo.id ==  1:
        #obtiene la ultima autorizacion independientemente en el flujo que se encuentre
        autorizaciones = AutorizarSolicitudes.objects.filter(
            created_at=Subquery(subconsulta_ultima_fecha)
        ).select_related('solicitud', 'perfil').filter(
            solicitud__complete = 1
        ).order_by("-created_at")
    else:
        #obtiene la ultima autorizacion independientemente en el flujo que se encuentre
        autorizaciones = AutorizarSolicitudes.objects.filter(
            created_at=Subquery(subconsulta_ultima_fecha)
        ).select_related('solicitud', 'perfil').filter(
            solicitud__solicitante_id__distrito_id=solicitante.distrito_id ,solicitud__complete = 1
            #solicitud__solicitante_id__distrito_id=solicitante.distrito_id,tipo_perfil_id = usuario.tipo.id ,solicitud__complete = 1
        ).order_by("-created_at")
    
    autorizaciones_filter = AutorizarSolicitudesFilter(request.GET, queryset=autorizaciones)
    autorizaciones = autorizaciones_filter.qs
    
    p = Paginator(autorizaciones, 50)
    page = request.GET.get('page')
    salidas_list = p.get_page(page)
    autorizaciones= p.get_page(page)
    
    contexto = {
        'usuario':usuario,
        'autorizaciones':autorizaciones,
        'autorizaciones_filter': autorizaciones_filter,
        'salidas_list':salidas_list,
    }
    
    return render(request,'esquema/bonos_varilleros/listar.html',contexto)

#para crear solicitudes de bonos
@login_required(login_url='user-login')
def crearSolicitudBonosVarilleros(request):
    usuario = request.user  
    
    #Todos los supervisores pueden crear solicitudes
    if usuario.userdatos.tipo_id == 5:
        print(usuario)
        superintendente = UserDatos.objects.filter(distrito_id=usuario.userdatos.distrito, tipo_id=6).values('numero_de_trabajador').first()
        print(superintendente)
        perfil_superintendente = Perfil.objects.filter(numero_de_trabajador = superintendente['numero_de_trabajador']).values('id').first() 
        print(perfil_superintendente)
        #se obtiene el usuario logueado
        usuario = get_object_or_404(UserDatos,user_id = request.user.id)
        #se obtiene el perfil del usuario logueado
        solicitante = get_object_or_404(Perfil,numero_de_trabajador = usuario.numero_de_trabajador) 
        #se cargan los formularios con los valores del post
        solicitudForm = SolicitudForm()      
        bonoSolicitadoForm = BonoSolicitadoForm()
        requerimientoForm = RequerimientoForm()
        #se hace una consulta con los empleados del distrito que pertenecen
        empleados = Perfil.objects.filter(distrito_id = usuario.distrito.id).exclude(numero_de_trabajador = usuario.numero_de_trabajador).order_by('nombres')
        #se carga el formulario en automatico definiendo filtros
        bonoSolicitadoForm.fields["trabajador"].queryset = empleados 
        #crea el contexto
        contexto = {
                'usuario':usuario,
                'solicitante':solicitante,
                'solicitudForm':solicitudForm,
                'bonoSolicitadoForm':bonoSolicitadoForm,
                'requerimientoForm':requerimientoForm,
                'lista_archivos':None,
        }
        
        #Para guardar la solicitud
        if request.method == "POST":
            #obtiene el folio independientemente del formulario
            if request.POST.get('valor') is not None:
                folio = request.POST.get('valor')
            else:        
                folio = request.POST.get('folio')
                
            solicitud, created = Solicitud.objects.get_or_create(id=folio,defaults={'complete': False, 'id':folio,'folio':folio,'solicitante_id':solicitante.id, 'total':0.00})
                    
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
                
            if 'btn_archivos' in request.POST:      
                #Se envian los formularios con datos                   
                requerimientoForm = RequerimientoForm(request.POST, request.FILES)  
                archivos = request.FILES.getlist('url')
                
                #creacion del contexto            
                contexto['solicitudForm'] = solicitudForm
                contexto['bonoSolicitadoForm'] = bonoSolicitadoForm
                contexto['requerimientoForm'] = requerimientoForm
                contexto['lista_archivos'] = lista_archivos
                contexto['datos_bonos_solicitud'] = datos_bonos_solicitud
                contexto['total'] = total
                contexto['folio'] = folio
                
                #validacion     
                if requerimientoForm.is_valid():
                    #Se recorren los archivos para ser almacenados
                    for archivo in archivos:
                        Requerimiento.objects.create(
                            solicitud_id = folio,
                            url = archivo,
                        )
                    solicitud.complete_requerimiento = True
                    solicitud.save()
                    messages.success(request, "Los archivos se subieron correctamente")
                    return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)
                else:
                    return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)
            
            elif 'btn_agregar' in request.POST: 
                    
                solicitudForm = SolicitudForm(request.POST)      
                bonoSolicitadoForm = BonoSolicitadoForm(request.POST)  
                bonoSolicitadoForm.fields["trabajador"].queryset = empleados 
                
                contexto['solicitudForm'] = solicitudForm
                contexto['bonoSolicitadoForm'] = bonoSolicitadoForm
                contexto['requerimientoForm'] = requerimientoForm
                contexto['lista_archivos'] = lista_archivos
                contexto['datos_bonos_solicitud'] = datos_bonos_solicitud
                contexto['total'] = total
                contexto['folio'] = folio
                            
                #validación de los formularios
                if solicitudForm.is_valid() and bonoSolicitadoForm.is_valid():
                    #obtener los datos de los formularios
                    bono = solicitudForm.cleaned_data['bono']
                    trabajador = bonoSolicitadoForm.cleaned_data['trabajador']
                    puesto = bonoSolicitadoForm.cleaned_data['puesto']
                    cantidad = bonoSolicitadoForm.cleaned_data['cantidad']
                    
                    #se agrega el bono a la solicitud
                    solicitud.bono_id = bono
                    solicitud.save()
                    solicitud.complete_bono = True
                    solicitud.save()
                    
                    verificar_puesto = BonoSolicitado.objects.filter(solicitud_id = solicitud.id, puesto_id=puesto).values("puesto_id").first()
                    
                    #no seleccionar el mismo puesto 2 veces
                    if verificar_puesto is None:
                                                
                            BonoSolicitado.objects.create(
                                solicitud_id = solicitud.id,
                                trabajador_id = trabajador.id,
                                puesto_id = puesto.id,
                                distrito_id = usuario.distrito.id,
                                cantidad = cantidad,
                            )
                            
                            #Actuliza la cantidad del total de la solicitud 
                            total = BonoSolicitado.objects.filter(solicitud_id = solicitud.id).values("cantidad").aggregate(total=Sum('cantidad'))['total']                 
                            Solicitud.objects.filter(pk=solicitud.id).values("total").update(total=total)
                        
                            messages.success(request, "El bono se ha agregado a la solicitud correctamente")
                            
                            #se llama el formulario vacio para que pueda agregar mas bonos
                            bonoSolicitadoForm = BonoSolicitadoForm()
                            
                            contexto['bonoSolicitadoForm'] = bonoSolicitadoForm
                            contexto['total'] = total
                            
                    else:
                            messages.error(request, "No se puede agregar el mismo puesto")
                            bonoSolicitadoForm = BonoSolicitadoForm()
                            contexto['bonoSolicitadoForm'] = bonoSolicitadoForm
                                            
                    contexto["bonoSolicitadoForm"].fields["trabajador"].queryset = empleados
                        
                    return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)
                #se muestran los errores de validaciones      
                else:
                                                    
                    return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)
                            
        #Es metodo GET - Carga los formularios
        else:        
            #Genera el número de folio automaticamente
            ultimo_registro = Solicitud.objects.values('id').last()
            
            if ultimo_registro is not None:
                folio = ultimo_registro['id'] + 1 
            else:
                folio = 1
                        
            contexto['folio'] = folio
             
            return render(request,'esquema/bonos_varilleros/crear_solicitud.html',contexto)
    else:
        return render(request, 'revisar/403.html')
    
def verificarSolicitudBonosVarilleros(request,solicitud):
    
    usuario = get_object_or_404(UserDatos,user_id = request.user.id)
    perfil = Perfil.objects.filter(numero_de_trabajador = usuario.numero_de_trabajador).values('id')
    #Solo el mismo usuario que creo la solicitud puede editarla
    permiso = Solicitud.objects.filter(solicitante_id = perfil[0]['id'], folio = solicitud)
    
    if permiso:
        autorizacion = AutorizarSolicitudes.objects.select_related('solicitud').filter(solicitud=solicitud).last()
        requerimientoForm = RequerimientoForm()
        solicitudForm = SolicitudForm(initial={'bono': autorizacion.solicitud.bono.id})
        bonoSolicitadoForm = BonoSolicitadoForm()
        datos_bonos_solicitud = BonoSolicitado.objects.filter(solicitud_id = solicitud)
            
        empleados = Perfil.objects.filter(distrito_id = usuario.distrito.id).exclude(numero_de_trabajador = usuario.numero_de_trabajador).order_by('nombres')
        bonoSolicitadoForm.fields["trabajador"].queryset = empleados 
        lista_archivos = Requerimiento.objects.filter(solicitud_id = solicitud).values("id","url")
        
        if request.method == 'POST':  
            if 'btn_archivos' in request.POST:                 
                
                requerimientoForm = RequerimientoForm(request.POST, request.FILES)  
                archivos = request.FILES.getlist('url')
                
                if requerimientoForm.is_valid():                 
                    for archivo in archivos:
                        Requerimiento.objects.create(
                            solicitud_id = solicitud,
                            url = archivo,
                        )
                    messages.success(request, "Los archivos se han subido correctamente")
                
                    contexto = {
                        'requerimientoForm':requerimientoForm,
                        'solicitudForm':solicitudForm,
                        'bonoSolicitadoForm': bonoSolicitadoForm,
                        'solicitud':solicitud,
                        'solicitante':autorizacion.solicitud,
                        'datos_bonos_solicitud':datos_bonos_solicitud,
                        'total':autorizacion.solicitud.total,
                        'lista_archivos':lista_archivos,
                        'estado':autorizacion
                    }
                
                    return render(request,'esquema/bonos_varilleros/verificar_solicitud.html',contexto)
                
                else:
                    print('error de validaicion del archivo')
                    contexto = {
                        'requerimientoForm':requerimientoForm,
                        'solicitudForm':solicitudForm,
                        'bonoSolicitadoForm': bonoSolicitadoForm,
                        'solicitud':solicitud,
                        'solicitante':autorizacion.solicitud,
                        'datos_bonos_solicitud':datos_bonos_solicitud,
                        'total':autorizacion.solicitud.total,
                        'lista_archivos':lista_archivos,
                        'estado':autorizacion
                    }
                    
                    #return redirect('verificarSolicitudBonosVarilleros', solicitud=solicitud)
                    return render(request,'esquema/bonos_varilleros/verificar_solicitud.html',contexto)
            
            elif 'btn_agregar' in request.POST:
                solicitudForm = SolicitudForm(request.POST)      
                bonoSolicitadoForm = BonoSolicitadoForm(request.POST)
                bonoSolicitadoForm.fields["trabajador"].queryset = empleados
                
                if solicitudForm.is_valid() and bonoSolicitadoForm.is_valid():
                    bono = solicitudForm.cleaned_data['bono']
                    trabajador = bonoSolicitadoForm.cleaned_data['trabajador']
                    puesto = bonoSolicitadoForm.cleaned_data['puesto']
                    cantidad = bonoSolicitadoForm.cleaned_data['cantidad']
                    #actualizar el bono
                    Solicitud.objects.filter(pk=solicitud).update(bono=bono)
                    #verificar el bono para que no se asignen dos veces
                    verificar_puesto = BonoSolicitado.objects.filter(solicitud_id = solicitud, puesto_id=puesto).values("puesto_id").first()
                
                    if verificar_puesto is None:
                        BonoSolicitado.objects.create(
                            solicitud_id = solicitud,
                            trabajador_id = trabajador.id,
                            puesto_id = puesto.id,
                            distrito_id = usuario.distrito.id,
                            cantidad = cantidad,
                        )
                            
                        total = BonoSolicitado.objects.filter(solicitud_id = solicitud).values("cantidad").aggregate(total=Sum('cantidad'))['total']                 
                        Solicitud.objects.filter(pk=solicitud).values("total").update(total=total)
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
                            'solicitante':autorizacion.solicitud,
                            'datos_bonos_solicitud':datos_bonos_solicitud,
                            'total':autorizacion.solicitud.total,
                            'lista_archivos':lista_archivos,
                            'estado':autorizacion
                    }
                    return render(request,'esquema/bonos_varilleros/verificar_solicitud.html',contexto)
                else:
                    contexto = {
                        'requerimientoForm':requerimientoForm,
                        'solicitudForm':solicitudForm,
                        'bonoSolicitadoForm': bonoSolicitadoForm,
                        'solicitud':solicitud,
                        'solicitante':autorizacion.solicitud,
                        'datos_bonos_solicitud':datos_bonos_solicitud,
                        'total':autorizacion.solicitud.total,
                        'lista_archivos':lista_archivos,
                        'estado':autorizacion
                    }
                    return render(request,'esquema/bonos_varilleros/verificar_solicitud.html',contexto)
            
            elif 'btn_actualizar' in request.POST:
                #siempre que haya un cambio se regresa al Supervisor
                autorizar = AutorizarSolicitudes.objects.get(solicitud_id = solicitud, tipo_perfil_id = 6)
                autorizar.estado_id = 3 #pendiente
                autorizar.comentario = autorizacion.comentario
                autorizar.revisar = True
                autorizar.save()
                messages.success(request, "Se ha actualizado la solicitud y se envia al Superintendete")
                return redirect('listarBonosVarilleros')
        
        else:
            contexto = {
                'requerimientoForm':requerimientoForm,
                'solicitudForm':solicitudForm,
                'bonoSolicitadoForm': bonoSolicitadoForm,
                'solicitud':solicitud,
                'solicitante':autorizacion.solicitud,
                'datos_bonos_solicitud':datos_bonos_solicitud,
                'total':autorizacion.solicitud.total,
                'lista_archivos':lista_archivos,
                'estado':autorizacion
            }
            
            #return redirect('verificarSolicitudBonosVarilleros', solicitud=solicitud)
            return render(request,'esquema/bonos_varilleros/verificar_solicitud.html',contexto)    
    else:
        return render(request, 'revisar/403.html')
    
#para ver detalles de la solicitud
@login_required(login_url='user-login')
def verDetallesSolicitud(request,solicitud_id):    
    usuario = get_object_or_404(UserDatos,user_id = request.user.id)
    #los bonos solicitados
    bonos = BonoSolicitado.objects.filter(solicitud_id = solicitud_id)
    #los archivos
    requerimientos = Requerimiento.objects.filter(solicitud_id = solicitud_id)
    
    #busca la ultima solicitud con relacion a sus modelos        
    subconsulta_ultima_fecha = AutorizarSolicitudes.objects.values('solicitud_id').annotate(
        ultima_fecha=Max('created_at')
    ).filter(solicitud_id=OuterRef('solicitud_id')).values('ultima_fecha')[:1]
    
    autorizaciones = AutorizarSolicitudes.objects.filter(
        created_at=Subquery(subconsulta_ultima_fecha)
    ).select_related('solicitud','perfil').filter(
        solicitud__folio=solicitud_id
    ).first()
    
    #se carga el formulario con datos iniciales
    autorizarSolicitudesUpdateForm = AutorizarSolicitudesUpdateForm(initial={'estado':autorizaciones.estado.id,'comentario':autorizaciones.comentario})
    autorizarSolicitudesGerenteUpdateForm = AutorizarSolicitudesGerenteUpdateForm(initial={'estado':autorizaciones.estado.id,'comentario':autorizaciones.comentario})
    
    contexto = {
        "usuario":usuario,
        "autorizaciones":autorizaciones,
        "bonos":bonos,
        "requerimientos": requerimientos,
        "autorizarSolicitudesUpdateForm":autorizarSolicitudesUpdateForm,
        "autorizarSolicitudesGerenteUpdateForm":autorizarSolicitudesGerenteUpdateForm
    }
    
    return render(request,'esquema/bonos_varilleros/detalles_solicitud.html',contexto)
    

#para remover bonos agregados
@login_required(login_url='user-login')
def removerBono(request,bono_id):
    #hacer el complete requerimiento a 0 - contar el numero de archivos cuando es 0
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

#para eliminar los bonos al editar una solicitud
@login_required(login_url='user-login')
def removerBonosEditar(request, solicitud_id):
    if request.method == 'POST':
        try:
            get_object_or_404(Solicitud,pk=solicitud_id)
            BonoSolicitado.objects.filter(solicitud_id = solicitud_id).delete()
            return JsonResponse({'mensaje':'eliminados'},status=200,safe=True)
            
        except:
            return JsonResponse({'mensaje':'error del servidor'},status=500,safe=True)    
        

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

@login_required(login_url='user-login')
def EnviarSolicitudEsquemaBono(request):
    try:
        #se obtiene la solicitud desde el request 
        data = json.loads(request.body)
        #se busca la solicitud en la BD
        solicitud = Solicitud.objects.get(pk=data['solicitud'])
        #se verifica que la solicitud este complete para crear la autorizacion
        if solicitud.complete_bono == True and solicitud.complete_requerimiento == True:
            solicitud.complete = True
            solicitud.save()    
            
            usuario = request.user  
            superintendente = UserDatos.objects.filter(distrito_id=usuario.userdatos.distrito, tipo_id=6).values('numero_de_trabajador').first()
            perfil_superintendente = Perfil.objects.filter(numero_de_trabajador = superintendente['numero_de_trabajador']).values('id').first() 
            
            #se crea la autorizacion
            AutorizarSolicitudes.objects.create(
                solicitud_id = solicitud.id,
                perfil_id =  perfil_superintendente['id'],
                tipo_perfil_id = 6, # superintendente
                estado_id = 3, # pendiente
            )
            
            return JsonResponse({'mensaje':1},status=200,safe=False)
        else:
            #falta subir los requerimientos
            return JsonResponse({"mensaje":0},status=422,safe=False)
        
    except:
        return JsonResponse({'mensaje':'objecto no encontrado'},status=404,safe=False) 

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
            
