from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from esquema.forms import AutorizarSolicitudesUpdateForm
from .models import AutorizarSolicitudes
from esquema.models import BonoSolicitado
from proyecto.models import UserDatos,Perfil,Status,Costo,Catorcenas
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from datetime import date
import datetime

def asignarBonoCosto(solicitud):
    #una lista que lleva cada cantidad del bono
    cantidad = []
    #la lista de los perfiles que recibiran los bonos
    lista_perfiles = []
       
    #trae los empleados con sus respectivos bonos
    empleados = BonoSolicitado.objects.filter(solicitud_id = solicitud).values("trabajador_id","cantidad")
    
    for item in empleados:
        trabajador_id = item['trabajador_id']
        cantidad_obtenida = item['cantidad']
        lista_perfiles.append(trabajador_id)
        cantidad.append(cantidad_obtenida)
            
    #se asigna cada empleado con su respectivo bono        
    for index,perfil in enumerate(lista_perfiles):
        costo = Costo.objects.get(status__perfil_id = perfil)
        costo.bono_total = cantidad[index]
        
        
      
    
    
    
        
        
@login_required(login_url='user-login')
def autorizarSolicitud(request,solicitud):
    if request.method == "POST": 
        autorizarSolicitudesUpdateForm = AutorizarSolicitudesUpdateForm(request.POST)
                
        if autorizarSolicitudesUpdateForm.is_valid():
            usuario = request.user  
            rol = UserDatos.objects.get(user_id = usuario.id)
            
            #VERIFICAR CATORCENA
            fecha_actual = datetime.date.today()
            catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=fecha_actual, fecha_final__gte=fecha_actual).first()
            autorizar = AutorizarSolicitudes.objects.filter(solicitud_id = solicitud, tipo_perfil_id = rol.tipo_id, updated_at__range=(catorcena_actual.fecha_inicial,catorcena_actual.fecha_final)).first()
            
            #verifica si la autorizacion del bono esta en la catorcena actual
            if autorizar is not None:
                estadoDato = autorizarSolicitudesUpdateForm.cleaned_data['estado']
                comentarioDato = autorizarSolicitudesUpdateForm.cleaned_data['comentario']
                if estadoDato.id == 1:#aprobado                    
                    if rol.tipo_id == 6:#superintendente -> control tecnico   
                            
                            #se guardan los datos de la autorizacion en el superintendente
                            autorizar.estado_id = estadoDato.id
                            autorizar.comentario = comentarioDato
                            autorizar.save()
                            
                            #se busca el perfil del control tecnico corresponsiente al distrito
                            rol = UserDatos.objects.filter(distrito_id=usuario.userdatos.distrito, tipo_id=7).values('numero_de_trabajador').first()
                            perfil_control_tecnico = Perfil.objects.filter(numero_de_trabajador = rol['numero_de_trabajador']).values('id').first() 

                            #buscar o crea la autorizacion para el control tecnico
                            control_tecnico, created = AutorizarSolicitudes.objects.get_or_create(
                                solicitud_id=solicitud,
                                tipo_perfil_id=7,
                                perfil_id = perfil_control_tecnico['id'],
                                defaults={'estado_id': 3}  # Pendiente
                            )
                            
                            #entra en el flujo de verifica o cambios
                            if autorizar.revisar and not created:
                                control_tecnico.estado_id = 3
                                control_tecnico.save()
                                
                            messages.success(request, "La solicitud se aprobó por el Superintendente, pasa a revisión a Control Técnico")
                            return redirect('listarBonosVarilleros')
                        
                    elif rol.tipo_id == 7: #control tecnico -> gerente
                            #se guardan los datos de la autorizacion del control tecnico
                            autorizar.estado_id = estadoDato.id
                            autorizar.comentario = comentarioDato
                            autorizar.save()
                            
                            #se busca el perfil del gerente corresponsiente al distrito
                            rol = UserDatos.objects.filter(distrito_id=usuario.userdatos.distrito, tipo_id=8).values('numero_de_trabajador').first()
                            perfil_gerente = Perfil.objects.filter(numero_de_trabajador = rol['numero_de_trabajador']).values('id').first() 
                            
                            #buscar o crea la autorizacion para el gerente
                            gerente, created = AutorizarSolicitudes.objects.get_or_create(
                                solicitud_id=solicitud,
                                tipo_perfil_id=8,
                                perfil_id = perfil_gerente['id'],
                                defaults={'estado_id': 3}  # Pendiente
                            )
                            
                            #entra en el flujo de verifica o cambios
                            if autorizar.revisar and not created:
                                gerente.estado_id = 3
                                gerente.save()
                                
                            messages.success(request, "La solicitud se aprobó por Control Técnico, pasa a revisión al Gerente")
                            return redirect('listarBonosVarilleros')
                    elif rol.tipo_id == 8:# gerente
                            #autorizar - asignar el estado de la solicitud
                            autorizar.estado_id = estadoDato.id
                            autorizar.comentario = comentarioDato
                            autorizar.save() 
                                                        
                            #IMPLEMENTAR COSTO
                            asignarBonoCosto(solicitud) 
                            
                            messages.success(request, "La solicitud se aprobó por el Gerente")
                            return redirect('listarBonosVarilleros')
                        
                    
                elif estadoDato.id == 2:#rechazado 
                    #autorizar - asignar el estado de la solicitud
                    autorizar.estado_id = estadoDato.id
                    autorizar.comentario = comentarioDato
                    autorizar.save()  
                    
                    messages.error(request, "La solicitud fue rechazada")
                    return redirect('listarBonosVarilleros')
                
                elif estadoDato.id == 3:#pendiente
                    messages.error(request, "Debes seleccionar un estado de la lista")
                    return redirect('verDetalleSolicitud', solicitud_id=solicitud)
                
                elif estadoDato.id == 4:#revisar
                    autorizar.estado_id = 4
                    autorizar.comentario = comentarioDato
                    autorizar.revisar = True
                    autorizar.save()
                            
                    messages.success(request, "El supervisor verificará la solicitud emitida")
                    return redirect('verDetalleSolicitud', solicitud_id=solicitud)
                
            else:
                messages.error(request, "El bono no esta dentro de la fecha de la catorcena actual")
                return redirect('verDetalleSolicitud',solicitud)
                    
        else:
            messages.error(request, "Debes seleccionar un estado de la lista")
           
            
            
            
            
            
            

