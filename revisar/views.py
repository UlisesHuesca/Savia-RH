#Bonos
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from esquema.forms import AutorizarSolicitudesUpdateForm
from .models import AutorizarSolicitudes
from esquema.models import BonoSolicitado
from proyecto.models import UserDatos,Perfil,Status,Costo,Catorcenas,SalarioDatos
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from datetime import date
import datetime
from decimal import Decimal
from django.db.models import F

#Prenomina
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from proyecto.models import UserDatos, Perfil, Catorcenas, Costo, TablaFestivos, Vacaciones, Economicos, Economicos_dia_tomado, Vacaciones_dias_tomados
from .models import AutorizarPrenomina, Estado
from django.db.models import Q
from proyecto.filters import CostoFilter
from prenomina.models import Prenomina, Retardos, Castigos, Permiso_goce, Permiso_sin, Descanso, Incapacidades, Faltas, Comision, Domingo
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
import datetime 
from datetime import timedelta, date


from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
#Excel
from openpyxl import Workbook
import openpyxl
from openpyxl.chart import PieChart, Reference
from openpyxl.chart.series import DataPoint
from openpyxl.chart.label import DataLabelList
from openpyxl.drawing.image import Image
from openpyxl.styles import NamedStyle, Font, PatternFill
from openpyxl.utils import get_column_letter
from django.db.models.functions import Concat
from django.db.models import Value
from django.db.models import Sum
from django.db.models import Count
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.http import HttpResponseRedirect

#BONOS
def asignarBonoCosto(solicitud):
    #una lista que lleva cada cantidad del bono
    cantidad = []
    #la lista de los perfiles que recibiran los bonos
    lista_perfiles = []
       
    #trae los empleados con sus respectivos bonos
    empleados = BonoSolicitado.objects.filter(solicitud_id = solicitud).values("trabajador_id","cantidad")
    porcentaje = SalarioDatos.objects.get(pk = 1)

    print(porcentaje.comision_bonos)

    for item in empleados:
        trabajador_id = item['trabajador_id']
        cantidad_obtenida = item['cantidad']
        lista_perfiles.append(trabajador_id)
        cantidad.append(cantidad_obtenida)
            
    #se asigna cada empleado con su respectivo bono        
    for index,perfil in enumerate(lista_perfiles):
        costo = Costo.objects.get(status__perfil_id = perfil)
        costo.bono_total = cantidad[index]
        #costo.save()
        
        #realizar calculo bono - costo 
        costo.total_apoyosbonos_agregcomis = costo.campamento + costo.bono_total #bien
        costo.comision_complemeto_salario_bonos= ((costo.campamento + costo.bono_total)/Decimal(porcentaje.comision_bonos/10)) - costo.total_apoyosbonos_agregcomis #bien
        costo.total_costo_empresa = costo.sueldo_mensual_neto + costo.complemento_salario_mensual + costo.apoyo_de_pasajes + costo.impuesto_estatal + costo.imms_obrero_patronal + costo.sar + costo.cesantia + costo.infonavit + costo.isr + costo.total_apoyosbonos_empleadocomp + costo.total_apoyosbonos_agregcomis + costo.comision_complemeto_salario_bonos #18221.5
        costo.total_costo_empresa = costo.total_costo_empresa + costo.total_prima_vacacional
        costo.ingreso_mensual_neto_empleado= costo.sueldo_mensual_neto + costo.complemento_salario_mensual + costo.apoyo_de_pasajes + costo.total_apoyosbonos_empleadocomp + costo.total_apoyosbonos_agregcomis
        costo.save()
    
        print("bonos: ",costo.total_apoyosbonos_agregcomis)
        print("comision: ",costo.comision_complemeto_salario_bonos)
        print("costo total empresa: ",costo.total_costo_empresa)
        print("costo total empleado: ",costo.ingreso_mensual_neto_empleado)
        
    
        """
        costo.total_apoyosbonos_agregcomis = costo.campamento #Modificar falta suma
        costo.comision_complemeto_salario_bonos= (costo.complemento_salario_mensual + costo.campamento)*Decimal(dato.comision_bonos/100) #Falta suma dentro de la multiplicacion
        costo.total_costo_empresa = costo.sueldo_mensual_neto + costo.complemento_salario_mensual + costo.apoyo_de_pasajes + costo.impuesto_estatal + costo.imms_obrero_patronal + costo.sar + costo.cesantia + costo.infonavit + costo.isr + costo.total_apoyosbonos_empleadocomp #18221.5
        costo.total_costo_empresa = costo.total_costo_empresa + costo.total_prima_vacacional
        costo.ingreso_mensual_neto_empleado= costo.sueldo_mensual_neto + costo.complemento_salario_mensual + costo.apoyo_de_pasajes + costo.total_apoyosbonos_empleadocomp # + costo.total_apoyosbonos_agregcomis
        """
        
        
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
                            autorizar.save(update_fields=['estado_id', 'comentario'])
                            
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
                            autorizar.save(update_fields=['estado_id', 'comentario'])
                            
                            
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
                            
                    messages.success(request, "El supervisor hará cambios en la solicitud emitida")
                    return redirect('verDetalleSolicitud', solicitud_id=solicitud)
                
            else:
                messages.error(request, "El bono no esta dentro de la fecha de la catorcena actual")
                return redirect('verDetalleSolicitud',solicitud)
                    
        else:
            messages.error(request, "Debes seleccionar un estado de la lista")
              
#PRENOMINA
@login_required(login_url='user-login')
def Tabla_solicitudes_prenomina(request):
    user_filter = UserDatos.objects.get(user=request.user)
    ahora = datetime.date.today()
    catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
    if user_filter.distrito.distrito == 'Matriz':
        costo = Costo.objects.filter(complete=True, status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador")
    else:
        costo = Costo.objects.filter(distrito=user_filter.distrito, complete=True,  status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador")

    costo_filter = CostoFilter(request.GET, queryset=costo)
    costo = costo_filter.qs
    #Trae las prenominas que le toca a cada perfil
    if user_filter.tipo.nombre ==  "Control Tecnico": #1er perfil
        prenominas_verificadas = Prenomina.objects.filter(empleado__in=costo,autorizarprenomina__tipo_perfil__nombre="RH",fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]).distinct()
        rh = prenominas = Prenomina.objects.filter(empleado__in=costo, fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]).order_by("empleado__status__perfil__numero_de_trabajador") #Estas son todas las que deben haber en la catorcena
        rh = rh.count()
        ct = prenominas_verificadas.count()
        if ct < rh:
            mensaje_gerencia="Aún no estan listas las prenominas, pendientes por autorizar por RH= "+ str(rh-ct)
        elif ct == rh:
            mensaje_gerencia = "Todas revisadas por RH"
    elif user_filter.tipo.nombre ==  "Gerencia":  #2do perfil
        prenominas_verificadas = Prenomina.objects.filter(empleado__in=costo,autorizarprenomina__tipo_perfil__nombre="Control Tecnico",fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]).distinct()    
        rh = prenominas = Prenomina.objects.filter(empleado__in=costo, fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]).order_by("empleado__status__perfil__numero_de_trabajador") #Estas son todas las que deben haber en la catorcena
        rh = rh.count()
        ct = prenominas_verificadas.count()
        if ct < rh:
            mensaje_gerencia="Aún no estan listas las prenominas, pendientes por autorizar entre RH y CT= "+ str(rh-ct)
        elif ct == rh:
            mensaje_gerencia = "Todas revisadas por RH y CT"
    #Las ordena por numero de trabajador
    prenominas = prenominas_verificadas.order_by("empleado__status__perfil__numero_de_trabajador")
    #Asigna el estado
    for prenomina in prenominas:
        ultima_autorizacion = AutorizarPrenomina.objects.filter(prenomina=prenomina).order_by('-updated_at').first()
        ultima_rechazada = AutorizarPrenomina.objects.filter(prenomina=prenomina, estado__tipo="Rechazado").last()
        if user_filter.tipo.nombre ==  "Control Tecnico": 
            valor = AutorizarPrenomina.objects.filter(prenomina=prenomina, tipo_perfil__nombre="Control Tecnico").first()
  
        elif user_filter.tipo.nombre ==  "Gerencia": 
            valor = AutorizarPrenomina.objects.filter(prenomina=prenomina, tipo_perfil__nombre="Gerencia").first()

        if valor is not None:
            prenomina.valor = valor.estado.tipo
        if ultima_rechazada is not None:
            prenomina.ultima = ultima_rechazada.tipo_perfil.nombre
        prenomina.estado_general = determinar_estado_general(ultima_autorizacion)

    if request.method =='POST' and 'Excel' in request.POST:
        return Excel_estado_prenomina(prenominas, user_filter)
    
    if request.method =='POST' and 'Autorizar' in request.POST:
        if user_filter.tipo.nombre ==  "Control Tecnico":
            prenominas_filtradas = [prenom for prenom in prenominas if prenom.estado_general == 'Controles técnicos pendiente']
            if prenominas_filtradas:
                # Llamar a la función Autorizar_gerencia con las prenominas filtradas
                return Autorizar_gerencia(prenominas_filtradas, user_filter,request)
            else:
                # Si no hay prenominas que cumplan la condición, manejar según sea necesario
                messages.error(request,'Ya se han autorizado todas las prenominas pendientes')
        if user_filter.tipo.nombre ==  "Gerencia": 
            prenominas_filtradas = [prenom for prenom in prenominas if prenom.estado_general == 'Gerente pendiente']
            if prenominas_filtradas:
                # Llamar a la función Autorizar_gerencia con las prenominas filtradas
                return Autorizar_gerencia(prenominas_filtradas, user_filter,request)
            else:
                # Si no hay prenominas que cumplan la condición, manejar según sea necesario
                messages.error(request,'Ya se han autorizado todas las prenominas pendientes')

        


    p = Paginator(prenominas, 50)
    page = request.GET.get('page')
    salidas_list = p.get_page(page)

    context = {
        'costo_filter':costo_filter,
        'salidas_list': salidas_list,
        'user_filter':user_filter,
        'mensaje_gerencia':mensaje_gerencia,
    }
    return render(request, 'revisar/prenominas_solicitudes.html', context)

@login_required(login_url='user-login')
def Prenomina_Solicitud_Revisar(request, pk):
    user_filter = UserDatos.objects.get(user=request.user)
    ahora = datetime.date.today()
    costo = Costo.objects.get(id=pk)
    catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
    prenomina = Prenomina.objects.get(empleado=costo,fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])
    verificado_rh = AutorizarPrenomina.objects.filter(prenomina=prenomina).first()

    festivos = TablaFestivos.objects.filter(dia_festivo__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]) #festivos en la catorcena actual
    economicos = Economicos_dia_tomado.objects.filter(prenomina__status=prenomina.empleado.status, fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])
    vacaciones = Vacaciones_dias_tomados.objects.filter(Q(prenomina__status=prenomina.empleado.status, fecha_inicio__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]) | Q(prenomina__status=prenomina.empleado.status, fecha_fin__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])) #Comparar con la fecha final tambien
    autorizacion1 = prenomina.autorizarprenomina_set.filter(tipo_perfil__nombre="Control Tecnico").first()
    autorizacion2 = prenomina.autorizarprenomina_set.filter(tipo_perfil__nombre="Gerencia").first()

    #obtener factores de días asociados a cada prenomina
    prenomina.retardos = prenomina.retardos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.castigos = prenomina.castigos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.permiso_goce = prenomina.permiso_goce_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) 
    prenomina.permiso_sin = prenomina.permiso_sin_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.descanso = prenomina.descanso_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.incapacidades = prenomina.incapacidades_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.faltas = prenomina.faltas_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.comision = prenomina.comision_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.domingo = prenomina.domingo_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    fechas_con_economicos = [economico.fecha for economico in economicos]

    #fechas con factores
    fechas_con_retardos = [retardo.fecha for retardo in prenomina.retardos]
    fechas_con_castigos = [castigo.fecha for castigo in prenomina.castigos]
    fechas_con_permiso_goce = [permiso_goc.fecha for permiso_goc in prenomina.permiso_goce]
    fechas_con_permiso_sin = [permiso_si.fecha for permiso_si in prenomina.permiso_sin]
    fechas_con_descanso = [descans.fecha for descans in prenomina.descanso]
    fechas_con_incapacidades = [incapacidade.fecha for incapacidade in prenomina.incapacidades]
    fechas_con_faltas = [falta.fecha for falta in prenomina.faltas]
    fechas_con_comision = [comisio.fecha for comisio in prenomina.comision]
    fechas_con_domingo = [doming.fecha for doming in prenomina.domingo]
    fechas_con_festivos = [festivo.dia_festivo for festivo in festivos]
    fechas_con_economicos = [economico.fecha for economico in economicos]
    
    # todas las fechas de la catorcena actual
    delta = catorcena_actual.fecha_final - catorcena_actual.fecha_inicial
    dias_entre_fechas = [catorcena_actual.fecha_inicial + timedelta(days=i) for i in range(delta.days + 1)]

    #lista de tuplas con la fecha y su etiqueta
    fechas_con_etiquetas = [(fecha, "retardo", prenomina.retardos.filter(fecha=fecha).first().comentario if fecha in fechas_con_retardos else "") if fecha in fechas_con_retardos
                            else (fecha, "castigo", prenomina.castigos.filter(fecha=fecha).first().comentario if fecha in fechas_con_castigos else "") if fecha in fechas_con_castigos
                            else (fecha, "permiso_goce", prenomina.permiso_goce.filter(fecha=fecha).first().comentario if fecha in fechas_con_permiso_goce else "") if fecha in fechas_con_permiso_goce
                            else (fecha, "permiso_sin", prenomina.permiso_sin.filter(fecha=fecha).first().comentario if fecha in fechas_con_permiso_sin else "") if fecha in fechas_con_permiso_sin
                            else (fecha, "descanso", prenomina.descanso.filter(fecha=fecha).first().comentario if fecha in fechas_con_descanso else "") if fecha in fechas_con_descanso
                            else (fecha, "incapacidades", prenomina.incapacidades.filter(fecha=fecha).first().comentario if fecha in fechas_con_incapacidades else "") if fecha in fechas_con_incapacidades
                            else (fecha, "faltas",prenomina.faltas.filter(fecha=fecha).first().comentario if fecha in fechas_con_faltas else "") if fecha in fechas_con_faltas
                            else (fecha, "comision", prenomina.comision.filter(fecha=fecha).first().comentario if fecha in fechas_con_comision else "") if fecha in fechas_con_comision
                            else (fecha, "domingo", prenomina.domingo.filter(fecha=fecha).first().comentario if fecha in fechas_con_domingo else "") if fecha in fechas_con_domingo
                            else (fecha, "economico", "") if fecha in fechas_con_economicos
                            else (fecha, "festivo", "") if fecha in fechas_con_festivos
                            else (fecha, "vacaciones", "") if any(vacacion.fecha_inicio <= fecha <= vacacion.fecha_fin and fecha != vacacion.dia_inhabil for vacacion in vacaciones)
                            else (fecha, "asistencia", "") for fecha in dias_entre_fechas]

    if catorcena_actual:
        delta = catorcena_actual.fecha_final - catorcena_actual.fecha_inicial
        dias_entre_fechas = [catorcena_actual.fecha_inicial + timedelta(days=i) for i in range(delta.days + 1)]

    if request.method == 'POST' and 'guardar_cambios' in request.POST:
        revisado, created = AutorizarPrenomina.objects.get_or_create(prenomina=prenomina, tipo_perfil=user_filter.tipo)
        revisado.tipo_perfil=user_filter.tipo
        autorizar_valor = request.POST.get('autorizar')
        revisado.estado = Estado.objects.get(tipo=autorizar_valor)
        nombre = Perfil.objects.get(numero_de_trabajador = user_filter.numero_de_trabajador, distrito = user_filter.distrito)
        revisado.perfil=nombre
        comentario = request.POST.get('comentario')
        revisado.comentario=comentario
        revisado.save()
        messages.success(request, 'Cambios guardados exitosamente')
        return redirect('Prenominas_solicitudes')
    context = {
        'dias_entre_fechas': dias_entre_fechas, #Dias de la catorcena
        'prenomina':prenomina,
        'verificado_rh':verificado_rh,
        'costo':costo,
        'autorizacion1':autorizacion1,
        'autorizacion2':autorizacion2,
        'catorcena_actual':catorcena_actual,
        'fechas_con_etiquetas': fechas_con_etiquetas,
        }

    return render(request, 'revisar/Prenomina_solicitud_revisar.html',context)

def prenomina_solicitudes_revisar_ajax(request, pk):
    user_filter = UserDatos.objects.get(user=request.user)
    ahora = datetime.date.today()
    costo = Costo.objects.get(id=pk)
    catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
    prenomina = Prenomina.objects.get(empleado=costo,fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])
    festivos = TablaFestivos.objects.filter(dia_festivo__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]) #festivos en la catorcena actual
    economicos = Economicos_dia_tomado.objects.filter(prenomina__status=prenomina.empleado.status, fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])
    vacaciones = Vacaciones_dias_tomados.objects.filter(Q(prenomina__status=prenomina.empleado.status, fecha_inicio__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]) | Q(prenomina__status=prenomina.empleado.status, fecha_fin__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])) #Comparar con la fecha final tambien
    autorizacion = prenomina.autorizarprenomina_set.filter(tipo_perfil__nombre="RH").first()
    autorizacion1 = prenomina.autorizarprenomina_set.filter(tipo_perfil__nombre="Control Tecnico").first()
    autorizacion2 = prenomina.autorizarprenomina_set.filter(tipo_perfil__nombre="Gerencia").first()
    #obtener factores de días asociados a cada prenomina
    prenomina.retardos = prenomina.retardos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.castigos = prenomina.castigos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.permiso_goce = prenomina.permiso_goce_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) 
    prenomina.permiso_sin = prenomina.permiso_sin_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.descanso = prenomina.descanso_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.incapacidades = prenomina.incapacidades_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.faltas = prenomina.faltas_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.comision = prenomina.comision_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.domingo = prenomina.domingo_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))

    #fechas con factores
    fechas_con_retardos = [retardo.fecha for retardo in prenomina.retardos]
    fechas_con_castigos = [castigo.fecha for castigo in prenomina.castigos]
    fechas_con_permiso_goce = [permiso_goc.fecha for permiso_goc in prenomina.permiso_goce]
    fechas_con_permiso_sin = [permiso_si.fecha for permiso_si in prenomina.permiso_sin]
    fechas_con_descanso = [descans.fecha for descans in prenomina.descanso]
    fechas_con_incapacidades = [incapacidade.fecha for incapacidade in prenomina.incapacidades]
    fechas_con_faltas = [falta.fecha for falta in prenomina.faltas]
    fechas_con_comision = [comisio.fecha for comisio in prenomina.comision]
    fechas_con_domingo = [doming.fecha for doming in prenomina.domingo]
    fechas_con_festivos = [festivo.dia_festivo for festivo in festivos]
    fechas_con_economicos = [economico.fecha for economico in economicos]

    # todas las fechas de la catorcena actual
    delta = catorcena_actual.fecha_final - catorcena_actual.fecha_inicial
    dias_entre_fechas = [catorcena_actual.fecha_inicial + timedelta(days=i) for i in range(delta.days + 1)]

    #lista de tuplas con la fecha y su etiqueta
    fechas_con_etiquetas = [(fecha, "retardo", prenomina.retardos.filter(fecha=fecha).first().comentario if fecha in fechas_con_retardos else "") if fecha in fechas_con_retardos
                            else (fecha, "castigo", prenomina.castigos.filter(fecha=fecha).first().comentario if fecha in fechas_con_castigos else "") if fecha in fechas_con_castigos
                            else (fecha, "permiso_goce", prenomina.permiso_goce.filter(fecha=fecha).first().comentario if fecha in fechas_con_permiso_goce else "") if fecha in fechas_con_permiso_goce
                            else (fecha, "permiso_sin", prenomina.permiso_sin.filter(fecha=fecha).first().comentario if fecha in fechas_con_permiso_sin else "") if fecha in fechas_con_permiso_sin
                            else (fecha, "descanso", prenomina.descanso.filter(fecha=fecha).first().comentario if fecha in fechas_con_descanso else "") if fecha in fechas_con_descanso
                            else (fecha, "incapacidades", prenomina.incapacidades.filter(fecha=fecha).first().comentario if fecha in fechas_con_incapacidades else "") if fecha in fechas_con_incapacidades
                            else (fecha, "faltas",prenomina.faltas.filter(fecha=fecha).first().comentario if fecha in fechas_con_faltas else "") if fecha in fechas_con_faltas
                            else (fecha, "comision", prenomina.comision.filter(fecha=fecha).first().comentario if fecha in fechas_con_comision else "") if fecha in fechas_con_comision
                            else (fecha, "domingo", prenomina.domingo.filter(fecha=fecha).first().comentario if fecha in fechas_con_domingo else "") if fecha in fechas_con_domingo
                            else (fecha, "economico", "") if fecha in fechas_con_economicos
                            else (fecha, "festivo", "") if fecha in fechas_con_festivos
                            else (fecha, "vacaciones", "") if any(vacacion.fecha_inicio <= fecha <= vacacion.fecha_fin and fecha != vacacion.dia_inhabil for vacacion in vacaciones)
                            else (fecha, "asistencia", "") for fecha in dias_entre_fechas]

    response_data = {
        'fechas_con_etiquetas': fechas_con_etiquetas,
        'autorizacion': {
            'nombre': autorizacion.perfil.nombres if autorizacion else None,
            'apellido': autorizacion.perfil.apellidos if autorizacion else None,
            'tipo_perfil': autorizacion.tipo_perfil.nombre if autorizacion else None,
            'estado': autorizacion.estado.tipo if autorizacion else None,
            'comentario': autorizacion.comentario if autorizacion else None,
            'fecha': autorizacion.updated_at.strftime('%Y-%m-%d') if autorizacion and autorizacion.updated_at else None,
        },
        'autorizacion1': {
            'nombre': autorizacion1.perfil.nombres if autorizacion1 else None,
            'apellido': autorizacion1.perfil.apellidos if autorizacion1 else None,
            'tipo_perfil': autorizacion1.tipo_perfil.nombre if autorizacion1 else None,
            'estado': autorizacion1.estado.tipo if autorizacion1 else None,
            'comentario': autorizacion1.comentario if autorizacion1 else None,
            'fecha': autorizacion1.updated_at.strftime('%Y-%m-%d') if autorizacion1 and autorizacion1.updated_at else None,

        },
        'autorizacion2': {
            'nombre': autorizacion2.perfil.nombres if autorizacion2 else None,
            'apellido': autorizacion2.perfil.apellidos if autorizacion2 else None,
            'tipo_perfil': autorizacion2.tipo_perfil.nombre if autorizacion2 else None,
            'estado': autorizacion2.estado.tipo if autorizacion2 else None,
            'comentario': autorizacion2.comentario if autorizacion2 else None,
            'fecha': autorizacion2.updated_at.strftime('%Y-%m-%d') if autorizacion2 and autorizacion2.updated_at else None,
        },
    }

    # Devolver la respuesta en formato JSON
    return JsonResponse(response_data)

def determinar_estado_general(ultima_autorizacion):
    if ultima_autorizacion is None:
        return "Sin autorizaciones"

    tipo_perfil = ultima_autorizacion.tipo_perfil.nombre.lower()
    estado_tipo = ultima_autorizacion.estado.tipo.lower()

    if tipo_perfil == 'rh' and estado_tipo == 'aprobado':
        return 'Controles técnicos pendiente'

    if tipo_perfil == 'control tecnico' and estado_tipo == 'aprobado':
        return 'Gerente pendiente'
    
    if tipo_perfil == 'gerencia' and estado_tipo == 'aprobado':
        return 'Gerente aprobado (Prenomina aprobada)'

    if tipo_perfil == 'control tecnico' and estado_tipo == 'rechazado':
        return 'RH pendiente (rechazado por Controles técnicos)'
    
    if tipo_perfil == 'gerencia' and estado_tipo == 'rechazado':
        return 'RH pendiente (rechazado por Gerencia)'

    return 'Estado no reconocido'

def Autorizar_gerencia(prenominas, user_filter,request):
    nombre = Perfil.objects.get(numero_de_trabajador=user_filter.numero_de_trabajador, distrito=user_filter.distrito)
    aprobado = Estado.objects.get(tipo="aprobado")
    for prenomina in prenominas:
        revisado, created = AutorizarPrenomina.objects.get_or_create(prenomina=prenomina, tipo_perfil=user_filter.tipo) #Checa si existe autorización de su perfil y si no lo crea 
        revisado.estado = Estado.objects.get(tipo="aprobado")
        nombre = Perfil.objects.get(numero_de_trabajador=user_filter.numero_de_trabajador, distrito=user_filter.distrito)
        revisado.perfil = nombre
        revisado.comentario = 'Aprobación general'
        revisado.save()
        messages.success(request, 'Prenominas pendientes autorizadas automaticamente')
    return redirect('Prenominas_solicitudes')  # Cambia 'ruta_a_redirigir' por la URL a la que deseas redirigir después de autorizar las prenóminas

def Excel_estado_prenomina(prenominas, user_filter):
    response= HttpResponse(content_type = "application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename = Reporte_prenominas_' + str(datetime.date.today())+'.xlsx'
    wb = Workbook()
    ws = wb.create_sheet(title='Reporte')
    #Comenzar en la fila 1
    row_num = 1

    #Create heading style and adding to workbook | Crear el estilo del encabezado y agregarlo al Workbook
    head_style = NamedStyle(name = "head_style")
    head_style.font = Font(name = 'Arial', color = '00FFFFFF', bold = True, size = 11)
    head_style.fill = PatternFill("solid", fgColor = '00003366')
    wb.add_named_style(head_style)
    #Create body style and adding to workbook
    body_style = NamedStyle(name = "body_style")
    body_style.font = Font(name ='Calibri', size = 10)
    wb.add_named_style(body_style)
    #Create messages style and adding to workbook
    messages_style = NamedStyle(name = "mensajes_style")
    messages_style.font = Font(name="Arial Narrow", size = 11)
    wb.add_named_style(messages_style)
    #Create date style and adding to workbook
    date_style = NamedStyle(name='date_style', number_format='DD/MM/YYYY')
    date_style.font = Font(name ='Calibri', size = 10)
    wb.add_named_style(date_style)
    money_style = NamedStyle(name='money_style', number_format='$ #,##0.00')
    money_style.font = Font(name ='Calibri', size = 10)
    wb.add_named_style(money_style)
    money_resumen_style = NamedStyle(name='money_resumen_style', number_format='$ #,##0.00')
    money_resumen_style.font = Font(name ='Calibri', size = 14, bold = True)
    wb.add_named_style(money_resumen_style)

    columns = ['Empleado','#Trabajador','Distrito','#Catorcena','Fecha','Estado general','RH','CT','Gerencia','Autorizada','Retardos','Castigos','Permiso con goce sueldo',
               'Permiso sin goce','Descansos','Incapacidades','Faltas','Comisión','Domingo']

    for col_num in range(len(columns)):
        (ws.cell(row = row_num, column = col_num+1, value=columns[col_num])).style = head_style
        if col_num < 4:
            ws.column_dimensions[get_column_letter(col_num + 1)].width = 10
        if col_num == 4:
            ws.column_dimensions[get_column_letter(col_num + 1)].width = 30
        else:
            ws.column_dimensions[get_column_letter(col_num + 1)].width = 15


    columna_max = len(columns)+2

    (ws.cell(column = columna_max, row = 1, value='{Reporte Creado Automáticamente por Savia RH. JH}')).style = messages_style
    (ws.cell(column = columna_max, row = 2, value='{Software desarrollado por Vordcab S.A. de C.V.}')).style = messages_style
    (ws.cell(column = columna_max, row = 3, value='Algún dato')).style = messages_style
    (ws.cell(column = columna_max +1, row=3, value = 'alguna sumatoria')).style = money_resumen_style
    ws.column_dimensions[get_column_letter(columna_max)].width = 20
    ws.column_dimensions[get_column_letter(columna_max + 1)].width = 20
    ahora = datetime.date.today()
    catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
    rows = []

    for prenomina in prenominas:
        RH = AutorizarPrenomina.objects.filter(prenomina=prenomina, tipo_perfil__nombre="RH").first()
        CT = AutorizarPrenomina.objects.filter(prenomina=prenomina, tipo_perfil__nombre="Control Tecnico").first()
        G = AutorizarPrenomina.objects.filter(prenomina=prenomina, tipo_perfil__nombre="Gerencia").first()

        if G is not None and G.estado.tipo == 'aprobado':
            estado = 'aprobado'
        elif G is not None and G.estado.tipo == 'rechazado':
            estado = 'rechazado'
        else:
            estado = 'pendiente'

        if RH is None:
            RH ="Ninguno"   
        else:
            RH = str(RH.perfil.nombres)+(" ")+str(RH.perfil.apellidos)
        if CT is None:
            CT ="Ninguno"
        else:
            CT = str(CT.perfil.nombres)+(" ")+str(CT.perfil.apellidos)
        if G is None:
            G ="Ninguno"
        else:
            G = str(G.perfil.nombres)+(" ")+str(G.perfil.apellidos)
        retardos = prenomina.retardos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        castigos = prenomina.castigos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        permiso_goce = prenomina.permiso_goce_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        permiso_sin = prenomina.permiso_sin_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        descanso = prenomina.descanso_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        incapacidades = prenomina.incapacidades_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        faltas = prenomina.faltas_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        comision = prenomina.comision_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        domingo = prenomina.domingo_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        catorcena_num = catorcena_actual.catorcena

        # Agregar los valores a la lista rows para cada prenomina
        row = (
            prenomina.empleado.status.perfil.nombres + ' ' + prenomina.empleado.status.perfil.apellidos,
            prenomina.empleado.status.perfil.numero_de_trabajador,
            prenomina.empleado.status.perfil.distrito.distrito,
            catorcena_num,
            prenomina.fecha,
            prenomina.estado_general,
            str(RH),
            str(CT),
            str(G),
            estado,
            retardos,
            castigos,
            permiso_goce,
            permiso_sin,
            descanso,
            incapacidades,
            faltas,
            comision,
            domingo
        )
        rows.append(row)

    # Ahora puedes usar la lista rows como lo estás haciendo actualmente en tu código
    for row_num, row in enumerate(rows, start=2):
        for col_num, value in enumerate(row, start=1):
            if col_num < 4:
                ws.cell(row=row_num, column=col_num, value=value).style = body_style
            elif col_num == 5:
                ws.cell(row=row_num, column=col_num, value=value).style = date_style
            else:
                ws.cell(row=row_num, column=col_num, value=value).style = body_style


    sheet = wb['Sheet']
    wb.remove(sheet)
    wb.save(response)

    return(response)
            
            
            

