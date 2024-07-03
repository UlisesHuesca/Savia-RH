from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from proyecto.models import UserDatos, Perfil, Catorcenas, Costo, TablaFestivos, Vacaciones, Economicos, Economicos_dia_tomado, Vacaciones_dias_tomados, Empresa, Solicitud_vacaciones, Solicitud_economicos, Trabajos_encomendados
from proyecto.models import TablaVacaciones,SalarioDatos,DatosISR

from django.db import models
from django.db.models import Subquery, OuterRef, Q
from revisar.models import AutorizarPrenomina, Estado
from proyecto.filters import CostoFilter
from .models import Prenomina,PrenominaIncidencias, IncidenciaRango
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
import datetime 
from dateutil import parser
from dateutil.relativedelta import relativedelta
import os

from datetime import timedelta, date
from .filters import PrenominaFilter
import math

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

from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import letter,A4,landscape
import io
from reportlab.lib import colors
from reportlab.lib.colors import Color, black, blue, red, white
from reportlab.platypus import BaseDocTemplate, Frame, Paragraph, NextPageTemplate, PageBreak, PageTemplate,Table, SimpleDocTemplate,TableStyle, KeepInFrame, Spacer
import textwrap
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from django.http import FileResponse
from django.core.files.base import ContentFile

from decimal import Decimal 
import calendar
from esquema.models import BonoSolicitado
from django.db.models import Sum

from proyecto.models import Variables_imss_patronal
from proyecto.models import SalarioDatos

from .forms import PrenominaIncidenciasFormSet,IncidenciaRangoForm
import time

from calculos.utils import excel_estado_prenomina, excel_estado_prenomina_formato, calcular_aguinaldo_eventual, calcular_aguinaldo

# Create your views here.

#funcion para obtener la catorcena actual
def obtener_catorcena():
    fecha_actual = datetime.date.today()
    catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=fecha_actual, fecha_final__gte=fecha_actual).first()
    return catorcena_actual

def registrar_rango_incidencias(request,pk):    
    if request.method == 'POST':
        #catorcena
        catorcena_actual = obtener_catorcena()
        #RH
        user_filter = UserDatos.objects.get(user=request.user)
        #nombre = Perfil.objects.get(numero_de_trabajador = user_filter.numero_de_trabajador, distrito = user_filter.distrito)
        #Empleado
        #costo = Costo.objects.get(id=pk)
        prenomina = Prenomina.objects.get(empleado=pk,catorcena = catorcena_actual.id)
        #Se trae el formulario de las incapacidades para ser validado
        incidencias_form = IncidenciaRangoForm(request.POST, request.FILES)
        if incidencias_form.is_valid():
            #validaciones a partir de la fecha de inicio y fecha fin
            fecha_start = incidencias_form.cleaned_data['fecha_inicio']
            fecha_end = incidencias_form.cleaned_data['fecha_fin']
            
            if fecha_start > fecha_end:
                 return JsonResponse({'poscondicion': 'La fecha de inicio debe ser menor a la fecha final'}, status=422)
            
            if fecha_start < catorcena_actual.fecha_inicial:
                return JsonResponse({'poscondicion': 'No puedes agregar una fecha anterior de la catorcena actual'}, status=422)
            
            if fecha_start > catorcena_actual.fecha_final:
                return JsonResponse({'poscondicion': 'No puedes agregar una fecha de inicio despues de la fecha de termino de la catorcena actual'}, status=422)
            
            #Busca si existe al menos una vacacion en el rango de fechas: inicio - fin y valida
            vacaciones = Vacaciones_dias_tomados.objects.filter(
                prenomina__status=prenomina.empleado.status,
                fecha_inicio__lte=fecha_end,
                fecha_fin__gte=fecha_start
            ).values('id').exists()
            
            #validacion de vacaciones
            if vacaciones:
                return JsonResponse({'poscondicion': 'Ya existen vacaciones dentro del rango de fechas especificado'}, status=422)
            
            #Busca si existe al menos un dia festivo en el rango de fechas: inicio - fin y valida
            festivos = TablaFestivos.objects.filter(dia_festivo__range=[fecha_start, fecha_end]).values('id').exists()  
            if festivos:
                return JsonResponse({'poscondicion': 'Ya existen dias festivos dentro del rango de fechas especificado'}, status=422) 
            
            #Busca si existe al menos un dia economico en el rango de fechas: inicio - fin y valida
            economicos = Economicos_dia_tomado.objects.filter(prenomina__status=prenomina.empleado.status,fecha__range=[fecha_start, fecha_end]).values('id').exists()  
            if economicos:
                return JsonResponse({'poscondicion': 'Ya existen economicos dentro del rango de fechas especificado'}, status=422)
            
            #Busca si existe al menos una incidencia de rango en las fechas: inicio - fin y valida
            incidencias = PrenominaIncidencias.objects.filter(prenomina__empleado_id=pk,fecha__range=[fecha_start, fecha_end]).exclude(incidencia_id__in = (5,2)).values('id').exists()   
            if incidencias:
                return JsonResponse({'poscondicion': 'Ya existen incidencias dentro del rango de fechas especificado'}, status=422)
            
            #Cumple la validacion - Se guarda el rango de incidencia
            incidencia_rango = incidencias_form.save(commit=False)
            incidencia_rango.soporte = request.FILES['soporte'] 
            incidencia_rango.empleado_id = pk #este es el id del costo del empleado
            incidencia_rango.save()  
            
            fecha_actual = incidencia_rango.fecha_inicio #punto de inicio
            fecha_fin = min(incidencia_rango.fecha_fin, prenomina.catorcena.fecha_final) #toma la fecha fin mas chica entre las dos fechas para que solo se registren las que caen en la cat
            
            contador = 0
            estado = None
            #se empieza a extraer los datos de IncidenciaRango para almacenarlos en el modelo PrenominaIncidencias
            contador = 0
            estado = None
            while fecha_actual <= fecha_fin:
                incidencia = incidencia_rango.incidencia_id
                comentario = incidencia_rango.comentario
                soporte = incidencia_rango.soporte
                #Para agregar el complete para saber si se paga el día de enfermedad
                if incidencia == 10 and incidencia_rango.subsecuente != True:  # Enfermedad general y que sea subsecuente 
                    if contador < 3:
                        estado = True
                    else:
                        estado = False
                    contador += 1
                    

                if fecha_actual.weekday() == (incidencia_rango.dia_inhabil_id - 1): 
                    if (incidencia_rango.dia_inhabil_id - 1) == 6:# se resta 1 para obtener el dia domingo
                        incidencia = 5 #domingo
                        comentario = None
                        soporte = None
                    else:
                        incidencia = 2 #descanso
                        comentario = None
                        soporte = None
                        
                registro_prenomina, creado = PrenominaIncidencias.objects.update_or_create(
                    prenomina=prenomina,
                    fecha=fecha_actual,
                    defaults={
                        'comentario': comentario, 
                        'soporte': soporte,
                        'incidencia_id': incidencia,
                        'incidencia_rango':incidencia_rango,   
                        'complete': estado,                     
                    }
                )
                fecha_actual += timedelta(days=1)
                
            return JsonResponse({'success': 'Agregado correctamente'}, status=200)
        
        #validaciones del formulario
        else:
            validacion = None
            #se obtienen los valores de validaicones uno por uno
            errores = dict(incidencias_form.errors.items())
            for field, error_list in errores.items():
                  for error in error_list:
                      print(error)
                      validacion = error
                      
            # Prepara la respuesta JSON con los errores de validacion
            response_data = {
                'validaciones': validacion,
            }
            
            #Se envia los errores de validaciones al cliente
            return JsonResponse(response_data, status=422)
        
@login_required(login_url='user-login')
def Tabla_prenomina(request):
    start_time = time.time()  # Registrar el tiempo de inicio
    user_filter = UserDatos.objects.get(user=request.user)
    
    print("este es el filtro del usuario: ",user_filter.distrito)
    
    revisar_perfil = Perfil.objects.get(distrito=user_filter.distrito,numero_de_trabajador=user_filter.numero_de_trabajador)
    if user_filter.tipo.nombre == "RH":
        
        #llamar la fucion para obtener la catorcena actual
        catorcena_actual = obtener_catorcena()
        #para traer los empleados segun el filtro
        if user_filter.distrito.distrito == 'Matriz':
            costo = Costo.objects.filter(complete=True, status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador").values_list('id',flat=True)
           
        else:
            costo = Costo.objects.filter(status__perfil__distrito=user_filter.distrito, complete=True,  status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador").values_list('id',flat=True)
            print(costo)
        prenominas = Prenomina.objects.filter(empleado__in=costo,catorcena=catorcena_actual.id).order_by("empleado__status__perfil__numero_de_trabajador")
    
        festivos = TablaFestivos.objects.filter(dia_festivo__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
        #crear las prenominas actuales si es que ya es nueva catorcena
        nuevas_prenominas = []
        for empleado in costo:
            #checar si existe prenomina para el empleado en la catorcena actual
            prenomina_existente = prenominas.filter(empleado=empleado).exists()
            #si no existe crear una nueva prenomina
            if not prenomina_existente:
                nueva_prenomina = Prenomina(empleado_id=empleado, catorcena=catorcena_actual)
                nuevas_prenominas.append(nueva_prenomina) 
        if nuevas_prenominas:
            Prenomina.objects.bulk_create(nuevas_prenominas)              
        #costo_filter = CostoFilter(request.GET, queryset=costo)
        #costo = costo_filter.qs
        #prenominas = Prenomina.objects.filter(empleado__in=costo,catorcena = catorcena_actual.id).order_by("empleado__status__perfil__numero_de_trabajador").prefetch_related('incidencias')
        
        prenomina_filter = PrenominaFilter(request.GET, queryset=prenominas)
        prenominas = prenomina_filter.qs

        #para verificar las autotizaciones
        for prenomina in prenominas:
            ultima_autorizacion = AutorizarPrenomina.objects.filter(prenomina=prenomina).order_by('-updated_at').first() #Ultimo modificado

            if ultima_autorizacion is not None:
                prenomina.valor = ultima_autorizacion.estado.tipo #Esta bien como agarra el dato de RH arriba que es el primero
            prenomina.estado_general = determinar_estado_general(request,ultima_autorizacion)

        if request.method =='POST' and 'Autorizar' in request.POST:
            if user_filter.tipo.nombre ==  "RH":
                prenominas_filtradas = [prenom for prenom in prenominas if prenom.estado_general == 'RH pendiente (rechazado por Controles técnicos)' or prenom.estado_general == 'RH pendiente (rechazado por Gerencia)' or prenom.estado_general == 'Sin autorizaciones']
                if prenominas_filtradas:
                    # Llamar a la función Autorizar_gerencia con las prenominas filtradas
                    return Autorizar_general(request,prenominas_filtradas, user_filter,catorcena_actual)
                else:
                    # Si no hay prenominas que cumplan la condición, manejar según sea necesario
                    messages.error(request,'Ya se han autorizado todas las prenominas pendientes')
        
        if request.method =='POST' and 'Excel' in request.POST:
            filtro = False
            return excel_estado_prenomina(request,prenominas,filtro,user_filter)
        if request.method =='POST' and 'Excel2' in request.POST:
            reporte = False
            return excel_estado_prenomina_formato(request,prenominas, user_filter, reporte)
        
        p = Paginator(prenominas, 50)
        page = request.GET.get('page')
        salidas_list = p.get_page(page)

        context = {
            'user_filter':user_filter,
            'prenomina_filter':prenomina_filter,
            'salidas_list': salidas_list,
            'prenominas':prenominas
        }
        end_time = time.time()  # Registrar el tiempo de finalización
        print(f"Tiempo total de carga de la página: {end_time - start_time} segundos")
        return render(request, 'prenomina/Tabla_prenomina.html', context)
    else:
        return render(request, 'revisar/403.html')

@login_required(login_url='user-login')
def Autorizar_general(request,prenominas, user_filter, catorcena_actual):
    if request.user.is_authenticated:
        nombre = Perfil.objects.get(numero_de_trabajador=user_filter.numero_de_trabajador, distrito=user_filter.distrito) #persno que autoriza
        festivos = TablaFestivos.objects.filter(dia_festivo__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]) #festivos en la catorcena actual
        for prenomina in prenominas:    
            incidencias = PrenominaIncidencias.objects.filter(
                    prenomina__empleado_id = prenomina.empleado_id, 
                    fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
            if not incidencias.exists(): 
                #obtener los queries para su posterior llenado
                incidencias_rango = IncidenciaRango.objects.filter(empleado_id=prenomina.empleado_id,fecha_inicio__lte=catorcena_actual.fecha_final,fecha_fin__gte=catorcena_actual.fecha_inicial)

                if incidencias_rango:
                    #si te das cuenta siempre al brincar a una catorcena simpre sera de una incidencia es decir que si de castigo se brinca a la otra cat, solo habra de castigo y no puedes registrar dos rangos en una
                    for incidencia_rango in incidencias_rango:
                        fecha_actual = incidencia_rango.fecha_fin
                        fecha_fin = incidencia_rango.fecha_fin
                               
                    fecha_actual = max(incidencia_rango.fecha_inicio,prenomina.catorcena.fecha_inicial) #punto de inicio
                    fecha_fin = min(incidencia_rango.fecha_fin, prenomina.catorcena.fecha_final)#toma la fecha mas chica entre las dos fechas
                    
                    while fecha_actual <= fecha_fin:
                        incidencia = incidencia_rango.incidencia_id
                        comentario = incidencia_rango.comentario
                        soporte = incidencia_rango.soporte
                        
                        if fecha_actual.weekday() == (incidencia_rango.dia_inhabil_id - 1): 
                            #print(fecha_actual.weekday())
                            if (incidencia_rango.dia_inhabil_id - 1) == 6:# se resta 1 para obtener el dia domingo
                                incidencia = 5 #domingo
                                comentario = None
                                soporte = None
                            else:
                                incidencia = 2 #descanso
                                comentario = None
                                soporte = None
                                
                        registro_prenomina, creado = PrenominaIncidencias.objects.update_or_create(
                        prenomina=prenomina,
                            fecha=fecha_actual,
                            defaults={
                                'comentario': comentario, 
                                'soporte': soporte,
                                'incidencia_id': incidencia,
                                'incidencia_rango':incidencia_rango,                        
                            }
                        )
                        fecha_actual += timedelta(days=1)
                for festivo in festivos:
                    registro, created = PrenominaIncidencias.objects.update_or_create(
                        prenomina_id=prenomina.id,
                        fecha=festivo.dia_festivo,
                        defaults={
                            'incidencia_id': 13 #festivo
                        }
                    )
            economicos = Economicos_dia_tomado.objects.filter(prenomina__status=prenomina.empleado.status, fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final], complete = False)
            vacaciones = Vacaciones_dias_tomados.objects.filter(prenomina__status=prenomina.empleado.status,fecha_inicio__lte=catorcena_actual.fecha_final,fecha_fin__gte=catorcena_actual.fecha_inicial) 
            for economico in economicos:
                registro, created = PrenominaIncidencias.objects.update_or_create(
                    prenomina_id=prenomina.id,
                    fecha=economico.fecha,
                    defaults={
                        'incidencia_id': 14 # economico
                    }
                )

            for vacacion in vacaciones:
                    #se ajusta la fecha de acuerdo a la catorcena
                    fecha_inicio = max(vacacion.fecha_inicio, prenomina.catorcena.fecha_inicial)
                    fecha_fin = min(vacacion.fecha_fin, prenomina.catorcena.fecha_final)
                    #se considera el dia inhabil (descanso)       
                    dia_inhabil = vacacion.dia_inhabil_id
                    
                    fecha = fecha_inicio
                    incidencia = 0
                    #sacar las fechas
                    while fecha_inicio <= fecha_fin:
                        if fecha_inicio <= fecha <= fecha_fin:
                            incidencia = 15 # vacacion
                            #verifica si es domingo o descanso
                            if fecha_inicio.weekday() == (dia_inhabil - 1): 
                                if (dia_inhabil - 1) == 6:# se resta 1 para obtener el dia domingo
                                    incidencia = 5 #domingo
                                else:
                                    incidencia = 2 #descanso
                            elif fecha_inicio in [festivo.dia_festivo for festivo in festivos]:
                                incidencia = 13 #festivo:
                        registro, created = PrenominaIncidencias.objects.update_or_create(
                            prenomina_id=prenomina.id,
                            fecha=fecha,
                            defaults={
                            'incidencia_id': incidencia
                            }
                        )  
                        
                        #se agregar un dia para realizar el recorrido de la fecha          
                        fecha_inicio += timedelta(days=1)
                        fecha +=   timedelta(days=1)
                        
            descansos = PrenominaIncidencias.objects.filter(
                prenomina__empleado_id=prenomina.empleado_id, 
                incidencia__id__in=[6, 5, 2],
                fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
            
            if not descansos.exists():
                domingos = []
                fecha = catorcena_actual.fecha_inicial
                while fecha <= catorcena_actual.fecha_final:
                    if fecha.weekday() == 6:  # Domingo
                        domingos.append(fecha)
                    fecha += timedelta(days=1)

                for domingo in domingos[:2]:  #dos domingos
                    PrenominaIncidencias.objects.create(
                        prenomina=prenomina,
                        fecha=domingo,
                        incidencia_id=5,  # Domingo
                        comentario=None,
                        soporte=None,
                        incidencia_rango=None
                    )
            else:
                if descansos.count() == 1:
                    descanso = descansos.first()
                    dia_semana = descanso.fecha.weekday()

                    for i in range((catorcena_actual.fecha_final - catorcena_actual.fecha_inicial).days + 1):
                        fecha = catorcena_actual.fecha_inicial + timedelta(days=i)
                        if fecha.weekday() == dia_semana and fecha != descanso.fecha:
                            PrenominaIncidencias.objects.create(
                                prenomina=prenomina,
                                fecha=fecha,
                                incidencia_id=descanso.incidencia_id,  # Mismo tipo de incidencia
                                comentario=None,
                                soporte=None,
                                incidencia_rango=None
                            )
                            break


                

            revisado, created = AutorizarPrenomina.objects.get_or_create(prenomina=prenomina, tipo_perfil=user_filter.tipo) #Checa si existe autorización de su perfil y si no lo crea 
            revisado.estado = Estado.objects.get(tipo="aprobado")
            nombre = Perfil.objects.get(numero_de_trabajador=user_filter.numero_de_trabajador, distrito=user_filter.distrito)
            revisado.perfil = nombre
            revisado.comentario = 'Aprobación general'
            revisado.save()
            #Se ejecutan los aguinaldos
            calcular_aguinaldo_eventual(prenomina)
            calcular_aguinaldo(prenomina)
        messages.success(request, 'Prenominas pendientes autorizadas automaticamente')
        return redirect('Prenomina')  # Cambia 'ruta_a_redirigir' por la URL a la que deseas redirigir después de autorizar las prenóminas
    
@login_required(login_url='user-login')
def PrenominaRevisar(request, pk):
    user_filter = UserDatos.objects.get(user=request.user)
    if user_filter.tipo.id == 4: #Perfil RH
        start_time = time.time()  # Registrar el tiempo de inicio
        #llamar la fucion para obtener la catorcena actual
        catorcena_actual = obtener_catorcena()
        
        #obtener el empleado respecto a su prenomina     
        costo = Costo.objects.get(id=pk)
        prenomina = Prenomina.objects.get(empleado=costo,catorcena = catorcena_actual.id)
        
        #flujo de las autorizaciones
        autorizacion1 = prenomina.autorizarprenomina_set.filter(tipo_perfil__nombre="Control Tecnico").first()
        autorizacion2 = prenomina.autorizarprenomina_set.filter(tipo_perfil__nombre="Gerencia").first()
        
        if request.method == 'POST':
            #Para guardar los datos en la prenomina
            if 'guardar_cambios' in request.POST:
                prenomina_form = PrenominaIncidenciasFormSet(request.POST) #se obtienen instacias de formularios (14)
                if prenomina_form.is_valid():
                    for form in prenomina_form:
                        #se extren los datos 
                        asistencia = form.cleaned_data['incidencia']
                        if asistencia.id != 16: #no se registrar el 16 - asistencias
                            fecha = form.cleaned_data['fecha']
                            comentario = form.cleaned_data['comentario']
                            incidencia = form.cleaned_data['incidencia']
                            
                            registro_prenomina, creado = PrenominaIncidencias.objects.update_or_create(
                                prenomina=prenomina,
                                fecha=fecha,
                                defaults={
                                    'comentario': comentario, 
                                    'incidencia': incidencia
                                }
                            )   
                messages.success(request,"Se ha guardado la prenomina")         
                return redirect(request.META.get('HTTP_REFERER'))
            
            #Para eliminar los datos en la prenomina
            if 'eliminar_cambios' in request.POST:
                prenomina_form = PrenominaIncidenciasFormSet(request.POST) #se obtienen instacias de formularios (14)
                if prenomina_form.is_valid():
                    for form in prenomina_form:
                        if form.cleaned_data.get('DELETE'):
                            id = form.cleaned_data['id']
                            rango = form.cleaned_data['id_rango']
                            
                            # Si el formulario está marcado para eliminación, eliminar el registro
                            if id and rango is not None:
                                buscar_rango = IncidenciaRango.objects.filter(pk=rango)
                                for rango in buscar_rango:
                                    rango_fecha_inicio = rango.fecha_inicio
                                    archivo = rango.soporte.path

                                if rango_fecha_inicio >= catorcena_actual.fecha_inicial:
                                    PrenominaIncidencias.objects.filter(incidencia_rango_id=rango).delete()
                                    # Eliminar el archivo si existe
                                    if os.path.exists(archivo):
                                        os.remove(archivo)
                                    buscar_rango.delete()
                                else:
                                    messages.info(request,"No se puede eliminar estas incidencias, se registraron desde la prenomina anterior")         
                                    return redirect(request.META.get('HTTP_REFERER'))
                                    
                            else:
                                PrenominaIncidencias.objects.filter(pk=id).delete()
                                
                messages.success(request,"Se han eliminado incidencias de la prenomina")         
                return redirect(request.META.get('HTTP_REFERER'))
            
            #es para guardar la autorizacion - enviar la prenomina para revisión
            if 'enviar_prenomina' in request.POST:
                
                #Se ejecutan los aguinaldos
                calcular_aguinaldo_eventual(prenomina)
                calcular_aguinaldo(prenomina)
                
                revisado_rh, created = AutorizarPrenomina.objects.get_or_create(prenomina=prenomina, tipo_perfil=user_filter.tipo)
                revisado_rh.estado =  Estado.objects.get(pk=1) #aprobado
                perfil_rh = Perfil.objects.get(numero_de_trabajador = user_filter.numero_de_trabajador, distrito = user_filter.distrito)
                revisado_rh.perfil=perfil_rh
                revisado_rh.comentario="Revisado por RH"
                revisado_rh.save()
                
                messages.success(request, 'Se ha enviado la prenomina para revisión')  
                return redirect("Prenomina")
            
            if request.method =='POST' and 'economico_pdf' in request.POST:
                fecha_economico = request.POST['economico_pdf']
                fecha_economico = parser.parse(fecha_economico).date()
                solicitud= Solicitud_economicos.objects.get(status=costo.status,fecha=fecha_economico)
                return PdfFormatoEconomicos(request, solicitud)
            
            if request.method =='POST' and 'vacaciones_pdf' in request.POST:
                fecha_vacaciones = request.POST['vacaciones_pdf']
                fecha_vacaciones = parser.parse(fecha_vacaciones).date()
                solicitud = Solicitud_vacaciones.objects.filter(status=costo.status, fecha_inicio__lte=fecha_vacaciones, fecha_fin__gte=fecha_vacaciones).first()
                return PdfFormatoVacaciones(request, solicitud)
            
        else:
            
            #EJEUCUTA LOS QUERIES FESTIVOS, ECONOMICOS, FESTIVOS, RANGOS Y GUARDA LOS DATOS
            catorcena = obtener_catorcena()
            #obtener los queries para su posterior llenado
            festivos = TablaFestivos.objects.filter(dia_festivo__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]) #festivos en la catorcena actual
            economicos = Economicos_dia_tomado.objects.filter(prenomina__status=prenomina.empleado.status, fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final], complete = False)
            vacaciones = Vacaciones_dias_tomados.objects.filter(prenomina__status=prenomina.empleado.status,fecha_inicio__lte=catorcena.fecha_final,fecha_fin__gte=catorcena.fecha_inicial)
            incidencias_rango = IncidenciaRango.objects.filter(empleado_id=prenomina.empleado_id,fecha_inicio__lte=catorcena.fecha_final,fecha_fin__gte=catorcena.fecha_inicial)
            festivos_laborados = PrenominaIncidencias.objects.filter(prenomina__empleado_id=prenomina.empleado_id,incidencia_id = 17,fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).exists()
                            
            #se ejecuta el rango de incidencia en primer lugar - Siempre se tendra un rango de incidencia para la siguiente catorcena
            if incidencias_rango:
                for incidencia_rango in incidencias_rango:
                    fecha_actual = incidencia_rango.fecha_fin
                    fecha_fin = incidencia_rango.fecha_fin
                                
                fecha_actual = max(incidencia_rango.fecha_inicio,prenomina.catorcena.fecha_inicial) #punto de inicio
                fecha_fin = min(incidencia_rango.fecha_fin, prenomina.catorcena.fecha_final)#toma la fecha mas chica entre las dos fechas
                
                #empieza la extracion del rango de incidencia para ubicarlar una por una en el modelo PrenominaIncidencias
                while fecha_actual <= fecha_fin:
                    incidencia = incidencia_rango.incidencia_id
                    comentario = incidencia_rango.comentario
                    soporte = incidencia_rango.soporte
                    
                    #Registra ya sea domingo o descanso
                    if fecha_actual.weekday() == (incidencia_rango.dia_inhabil_id - 1): 
                        if (incidencia_rango.dia_inhabil_id - 1) == 6:# se resta 1 para obtener el dia domingo
                            incidencia = 5 #domingo
                            comentario = None
                            soporte = None
                        else:
                            incidencia = 2 #descanso
                            comentario = None
                            soporte = None
                    
                    #actuliza o crea - es para que solo se creen las necesearias
                    registro_prenomina, creado = PrenominaIncidencias.objects.update_or_create(
                    prenomina=prenomina,
                        fecha=fecha_actual,
                        defaults={
                            'comentario': comentario, 
                            'soporte': soporte,
                            'incidencia_id': incidencia,
                            'incidencia_rango':incidencia_rango,                        
                        }
                    )
                    fecha_actual += timedelta(days=1)
                    
            if festivos_laborados == False:
                #para obtenter los festivos          
                for festivo in festivos:
                    registro, created = PrenominaIncidencias.objects.update_or_create(
                        prenomina_id=prenomina.id,
                        fecha=festivo.dia_festivo,
                        defaults={
                            'incidencia_id': 13 #festivo
                        }
                    )
                    
            #para obtener los economicos
            for economico in economicos:
                registro, created = PrenominaIncidencias.objects.update_or_create(
                    prenomina_id=prenomina.id,
                    fecha=economico.fecha,
                    defaults={
                        'incidencia_id': 14 # economico
                    }
                )
                
            #para obtener las vacaciones
            for vacacion in vacaciones:
                    #se ajusta la fecha de acuerdo a la catorcena
                    fecha_inicio = max(vacacion.fecha_inicio, prenomina.catorcena.fecha_inicial)
                    fecha_fin = min(vacacion.fecha_fin, prenomina.catorcena.fecha_final)
                    #se considera el dia inhabil (descanso)       
                    dia_inhabil = vacacion.dia_inhabil_id
                    
                    fecha = fecha_inicio
                    incidencia = 0
                    #sacar las fechas
                    while fecha_inicio <= fecha_fin:
                        if fecha_inicio <= fecha <= fecha_fin:
                            incidencia = 15 # vacacion
                            #verifica si es domingo o descanso
                            if fecha_inicio.weekday() == (dia_inhabil - 1): 
                                if (dia_inhabil - 1) == 6:# se resta 1 para obtener el dia domingo
                                    incidencia = 5 #domingo
                                else:
                                    incidencia = 2 #descanso
                            elif fecha_inicio in [festivo.dia_festivo for festivo in festivos]:
                                incidencia = 13 #festivo:
                        #registra la incidencia
                        registro, created = PrenominaIncidencias.objects.update_or_create(
                            prenomina_id=prenomina.id,
                            fecha=fecha,
                            defaults={
                             'incidencia_id': incidencia
                            }
                        )  
                           
                        #se agregar un dia para realizar el recorrido de la fecha          
                        fecha_inicio += timedelta(days=1)
                        fecha +=   timedelta(days=1)

            #PREPARA LOS FORMULARIOS PARA SER MOSTRADOS CON LAS INCIDENCIAS
            fecha_inicial = catorcena_actual.fecha_inicial  # Fecha inicial
            # 5 domingo, 16 asistencia, 6 y 13 domingo calendario
            datos_iniciales = [{'fecha': fecha_inicial + timedelta(days=i),'incidencia':5 if i == 6 or i == 13 else 16} for i in range(14)] # se preparan los 14 forms con su fecha, 12 asistencias, 2 domingos
            #se filtra las incidencias por la prenomina es decir por el empleado
            incidencias = PrenominaIncidencias.objects.filter(prenomina = prenomina)
            
            if incidencias.exclude(incidencia_id = 13):
                fecha_inicial = catorcena_actual.fecha_inicial  # Fecha inicial
                #16 asistencia
                datos_iniciales = [{'fecha': fecha_inicial + timedelta(days=i),'incidencia':16} for i in range(14)] # se preparan los 14 forms con su fecha, 12 asistencias, 2 domingos
                
            # Iterar sobre las incidencias y actualizar los datos iniciales si coinciden con la fecha - volcar el query incidencias a los formularios
            for incidencia in incidencias:
                for data in datos_iniciales:
                    if incidencia.fecha == data['fecha']:
                        data['soporte'] = incidencia.soporte
                        data['comentario'] = incidencia.comentario
                        data['incidencia'] = incidencia.incidencia_id
                        data['id'] = incidencia.id  
                        data['id_rango'] = incidencia.incidencia_rango_id
                        
            prenomina_incidencias_form = PrenominaIncidenciasFormSet(initial=datos_iniciales)
            incidencia_rango_form = IncidenciaRangoForm()
            context = {
                'prenomina':prenomina,
                'costo':costo,
                'catorcena_actual':catorcena_actual,
                'autorizacion1':autorizacion1,
                'autorizacion2':autorizacion2,
                'catorcena_actual':catorcena_actual,
                'prenomina_incidencias_form': prenomina_incidencias_form,
                'incidencia_rango_form':incidencia_rango_form
                
            }
            end_time = time.time()  # Registrar el tiempo de finalización
            print(f"Tiempo total de carga de la página: {end_time - start_time} segundos")
            return render(request, 'prenomina/Actualizar_revisar.html',context)
    else:
        return render(request, 'revisar/403.html')

@login_required(login_url='user-login')
def determinar_estado_general(request, ultima_autorizacion):
    if ultima_autorizacion is None:
        return "Sin autorizaciones"

    tipo_perfil = ultima_autorizacion.tipo_perfil.nombre.lower()
    estado_tipo = ultima_autorizacion.estado.tipo.lower()

    if tipo_perfil == 'rh' and estado_tipo == 'aprobado': #Ultimo upd rh y fue aprobado
        return 'Controles técnicos pendiente'              #Solo puede editarlo ct

    if tipo_perfil == 'control tecnico' and estado_tipo == 'aprobado': #Ultimo upd ct y fue aprobado
        return 'Gerente pendiente'                         
    
    if tipo_perfil == 'gerencia' and estado_tipo == 'aprobado': #Ultimo upd gerencia y fue aprobado
        return 'Gerente aprobado (Prenomina aprobada)'

    if tipo_perfil == 'control tecnico' and estado_tipo == 'rechazado': #Ultimo upd ct y fue rechazado
        return 'RH pendiente (rechazado por Controles técnicos)'
    
    if tipo_perfil == 'gerencia' and estado_tipo == 'rechazado': #Ultimo upd gerencia y fue rechazado
        return 'RH pendiente (rechazado por Gerencia)'

    return 'Estado no reconocido'

@login_required(login_url='user-login')
def filtrar_prenominas(request, pk):
    user_filter = UserDatos.objects.get(user=request.user)
    if user_filter.tipo.nombre == "Gerencia" or "Control Tecnico":
        prenomina = Prenomina.objects.get(id = pk)
        verificado_rh = AutorizarPrenomina.objects.filter(prenomina_id=prenomina).first()
        
        #Se crean las fechas para ser mostradas en el template
        fecha_inicio = prenomina.catorcena.fecha_inicial
        fecha_fin = prenomina.catorcena.fecha_final

        # Generamos la lista de fechas
        fechas = []
        while fecha_inicio <= fecha_fin:
            fechas.append(fecha_inicio)
            fecha_inicio += timedelta(days=1)

        # Obtenemos las incidencias
        get_incidencias = PrenominaIncidencias.objects.filter(prenomina_id=prenomina.id)
        
        # Creamos un diccionario de incidencias indexado por fecha
        incidencias_dict = {incidencia.fecha: incidencia for incidencia in get_incidencias}
        
        # Preparamos los datos para el template
        incidencias = []
        for fecha in fechas:
            if fecha in incidencias_dict:
                incidencia = incidencias_dict[fecha]
                incidencias.append({
                    'fecha': incidencia.fecha,
                    'incidencia': incidencia.incidencia,
                    'comentario': incidencia.comentario,
                    'soporte': incidencia.soporte
                })
            else:
                incidencias.append({
                    'fecha': fecha,
                    'incidencia': 'Asistencia',
                    'comentario':None,
                    'soporte': None
                })
        
           
        autorizacion1 = prenomina.autorizarprenomina_set.filter(tipo_perfil__nombre="Control Tecnico").first()
        autorizacion2 = prenomina.autorizarprenomina_set.filter(tipo_perfil__nombre="Gerencia").first()

        if request.method =='POST' and 'economico_pdf' in request.POST:
            fecha_economico = request.POST['economico_pdf']
            fecha_economico = parser.parse(fecha_economico).date()
            solicitud= Solicitud_economicos.objects.get(status=prenomina.empleado.status,fecha=fecha_economico)
            return PdfFormatoEconomicos(request, solicitud)
        
        if request.method =='POST' and 'vacaciones_pdf' in request.POST:
            fecha_vacaciones = request.POST['vacaciones_pdf']
            fecha_vacaciones = parser.parse(fecha_vacaciones).date()
            solicitud = Solicitud_vacaciones.objects.filter(status=prenomina.empleado.status, fecha_inicio__lte=fecha_vacaciones, fecha_fin__gte=fecha_vacaciones).first()
            return PdfFormatoVacaciones(request, solicitud)
        
        #Enviar autorizacion
        if request.method == 'POST' and 'aprobar' or request.method == 'POST' and 'rechazar' in request.POST:
            if 'aprobar' in request.POST:
                estado = 'aprobado'
            elif 'rechazar' in request.POST:
                estado = 'rechazado'
            else:
                estado = None
            if estado:
                revisado, created = AutorizarPrenomina.objects.get_or_create(prenomina=prenomina, tipo_perfil=user_filter.tipo)
                revisado.tipo_perfil=user_filter.tipo
                revisado.estado = Estado.objects.get(tipo=estado)
                nombre = Perfil.objects.get(numero_de_trabajador = user_filter.numero_de_trabajador, distrito = user_filter.distrito)
                revisado.perfil=nombre
                comentario = request.POST.get('comentario')
                revisado.comentario=comentario
                revisado.save()
                messages.success(request, 'Cambios guardados exitosamente')
                return redirect('Prenominas_solicitudes')
            else:
                messages.error(request,'No se pudo procesar el estado intentalo de nuevo')
        context = {
            'prenomina':prenomina,
            'verificado_rh':verificado_rh,
            'autorizacion1':autorizacion1,
            'autorizacion2':autorizacion2,
            'incidencias':incidencias,
            'fechas':fechas,
            }

        return render(request, 'prenomina/filtrar_prenominas.html',context)
    else:
        return render(request, 'revisar/403.html')
    
    
    

@login_required(login_url='user-login')
def PdfFormatoEconomicos(request, solicitud):
    solicitud= Solicitud_economicos.objects.get(id=solicitud.id)
    now = date.today()
    fecha = solicitud.fecha
    periodo = str(fecha.year)
    economico = 0
    if not Economicos.objects.filter(status=solicitud.status):
        economico = 0
    else:
        last_economico = Economicos.objects.filter(status=solicitud.status).last()
        economico = last_economico.dias_disfrutados
    #Para ubicar el dia de regreso en un dia habil (Puede caer en día festivo)
    #if status.regimen.regimen == 'L-V':
    #    inhabil1 = 6
    #    inhabil2 = 7
    #elif status.regimen.regimen == 'L-S':
    #    inhabil1 = 7
    #    inhabil2 = None
    regreso = fecha + timedelta(days=1)
    #if regreso.isoweekday() == inhabil1:
    #    regreso = regreso + timedelta(days=1)
    #if regreso.isoweekday() == inhabil2:
    #    regreso = regreso + timedelta(days=1)


    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)

    #Colores utilizados
    azul = Color(0.16015625,0.5,0.72265625)
    rojo = Color(0.59375, 0.05859375, 0.05859375)

    c.setFillColor(black)
    c.setLineWidth(.2)
    c.setFont('Helvetica-Bold',16)
    c.drawCentredString(305,765,'GRUPO VORCAB SA DE CV')
    c.setFont('Helvetica-Bold',11)
    c.drawCentredString(305,750,'SOLICITUD DE DIA ECONOMICO')
    if solicitud.autorizar == False:
        c.setFillColor(rojo)
        c.setFont('Helvetica-Bold',16)
        c.drawCentredString(305,725,'SOLICITUD NO AUTORIZADA')
    c.setFillColor(black)
    c.setFont('Helvetica-Bold',11)
    c.drawString(40,690,'NOMBRE:')
    c.line(95,688,325,688)
    espacio = ' '
    nombre_completo = str(solicitud.status.perfil.nombres + espacio + solicitud.status.perfil.apellidos)
    c.drawString(100,690,nombre_completo)
    c.drawString(40,670,'PUESTO:')
    c.line(95,668,325,668)
    c.drawString(100,670,solicitud.status.puesto.puesto)
    c.drawString(335,670,'TELEFONO PARTICULAR:')
    c.line(475,668,580,668)
    c.drawString(485,670,solicitud.status.telefono)
    c.drawString(40,620,'FECHA DE PLANTA:')
    if solicitud.status.fecha_planta != None:
        dia = str(solicitud.status.fecha_planta.day)
        mes = str(solicitud.status.fecha_planta.month)
        año = str(solicitud.status.fecha_planta.year)
    else:
        dia = "NR"
        mes = "NR"
        año = "NR"
    #rect(x, y, alto, ancho, stroke=1, fill=0)
    c.rect(185,600, 150, 50)
    c.line(185,618,335,618)
    c.line(185,638,335,638)
    c.line(230,650,230,600)
    c.line(290,650,290,600)
    c.drawCentredString(210,620,dia)
    c.drawCentredString(260,620,mes)
    c.drawCentredString(310,620,año)
    c.drawString(40,600,'FECHA DE SOLICITUD:')
    c.drawCentredString(210,605,str(now.day))
    c.drawCentredString(260,605,str(now.month))
    c.drawCentredString(310,605,str(now.year))
    c.drawString(200,640,'DIA')
    c.drawString(250,640,'MES')
    c.drawString(300,640,'AÑO')
    c.drawString(400,600,'FIRMA DEL SOLICITANTE')
    c.rect(390,598, 155, 50)
    c.line(390,610,545,610)
    c.drawString(40,540,'PERIODO CORRESPONDIENTE:')
    c.drawCentredString(450,540, periodo)
    c.rect(35,538, 255, 12)
    c.rect(360,538, 190, 12)
    c.drawCentredString(385,520,'1')
    c.drawCentredString(435,520,'2')
    c.drawCentredString(485,520,'3')

    c.drawString(40,500,'NO. DE DIA ECONOMICO:')
    c.rect(35,498, 175, 12)
    c.rect(360,498, 150, 12)
    c.line(410,510,410,498)
    c.line(460,510,460,498)
    c.setFillColorRGB(0.8, 0.8, 0.8)  # Color de relleno
    if economico == 1:
        c.rect(360,498, 50, 12, stroke = 1, fill = 1)
    elif economico == 2:
        c.rect(410,498, 50, 12, stroke = 1, fill = 1)
    elif economico == 3:
        c.rect(460,498, 50, 12, stroke = 1, fill = 1)
    c.setFillColor(black)
    c.drawString(40,480,'CON GOCE DE SUELDO:')
    c.rect(35,478, 140, 12)
    c.drawString(380,480,'SI')
    c.rect(360,478, 50, 12)
    c.drawString(425,480,'NO')
    c.rect(410,478, 50, 12)
    c.drawString(40,460,'FECHA QUE DESEA SALIR DEL PERMISO:')
    c.drawCentredString(450,460,str(fecha))
    c.rect(35,458, 250, 12)
    c.rect(360,458, 190, 12)
    c.drawString(40,440,'FECHA DE REGRESO A LABORES:')
    c.drawCentredString(450,440,str(regreso))
    c.rect(35,438, 195, 12)
    c.rect(360,438, 190, 12)
    #c.drawCentredString(305,370,'OBSERVACIONES')
    text = solicitud.comentario
    x = 40
    y = 385
    c.setFillColor(black)
    c.setFont('Helvetica-Bold',12)
    c.drawCentredString(310, y - 15, 'OBSERVACIONES')
    c.setFont('Helvetica', 9)
    lines = textwrap.wrap(text, width=100)
    for line in lines:
        c.drawString(x + 10, y - 30, line)
        y -= 25
    c.rect(40,368, 530, 12)
    c.rect(40,300, 530, 68)
    c.drawCentredString(170,125,'FIRMA GERENCIA')
    c.rect(70,123, 200, 12)
    c.rect(70,135, 200, 50)
    c.drawCentredString(440,125,'FIRMA DE JEFE INMEDIATO')
    c.rect(330,123, 210, 12)
    c.rect(330,135, 210, 50)
    c.save()
    c.showPage()
    buf.seek(0)

    return FileResponse(buf, as_attachment=True, filename='Formato_Economico.pdf')

@login_required(login_url='user-login')
def PdfFormatoVacaciones(request, solicitud):
    solicitud= Solicitud_vacaciones.objects.get(id=solicitud.id)
    inicio = solicitud.fecha_inicio
    fin = solicitud.fecha_fin
    dia_inhabil = solicitud.dia_inhabil
    ######
    tabla_festivos = TablaFestivos.objects.all()
    delta = timedelta(days=1)
    day_count = (fin - inicio + delta ).days
    cuenta = day_count
    inhabil = dia_inhabil.numero
    for fecha in (inicio + timedelta(n) for n in range(day_count)):
        if fecha.isoweekday() == inhabil:
            cuenta -= 1
        else:
            for dia in tabla_festivos:
                if fecha == dia.dia_festivo:
                    cuenta -= 1
    diferencia = str(cuenta)
    #Para ubicar el dia de regreso en un dia habil (Puede caer en día festivo)
    fin = fin + timedelta(days=1)
    if fin.isoweekday() == inhabil:
        fin = fin + timedelta(days=1)
    now = date.today()
    año1 = str(inicio.year)
    año2= str(fin.year)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)

    #Colores utilizados
    azul = Color(0.16015625,0.5,0.72265625)
    rojo = Color(0.59375, 0.05859375, 0.05859375)

    c.setFillColor(azul)
    c.setLineWidth(.2)
    c.setFont('Helvetica-Bold',16)
    c.drawCentredString(305,765,'GRUPO VORCAB SA DE CV')
    c.drawCentredString(305,750,'SOLICITUD DE VACACIONES')
    c.drawInlineImage('static/images/vordcab.png',50,720, 4 * cm, 2 * cm) #Imagen Savia
    if solicitud.autorizar == False:
        c.setFillColor(rojo)
        c.setFont('Helvetica-Bold',16)
        c.drawCentredString(305,725,'SOLICITUD NO AUTORIZADA')
    c.setFillColor(black)
    c.setFont('Helvetica-Bold',11)
    c.drawString(40,690,'NOMBRE:')
    c.line(95,688,325,688)
    espacio = ' '
    nombre_completo = str(solicitud.status.perfil.nombres + espacio + solicitud.status.perfil.apellidos)
    c.drawString(100,690,nombre_completo)
    c.drawString(40,670,'PUESTO:')
    c.line(95,668,325,668)
    c.drawString(100,670,solicitud.status.puesto.puesto)

    c.drawString(335,670,'TELEFONO PARTICULAR:')
    c.line(475,668,580,668)
    c.drawString(485,670,solicitud.status.telefono)

    if cuenta < 3:
        altura=200
        margen=20
        c.drawCentredString(305,502,'OBSERVACIONES')
        if solicitud.comentario_rh:
            c.drawString(55,490,solicitud.comentario_rh)
        else:
            c.drawString(55,490,'ninguna')
        c.rect(50,500, 510, 12)
        c.rect(50,435, 510, 65)
    else:
        altura=0
        margen=0
    c.drawString(40,620-margen,'FECHA DE PLANTA:')
    if solicitud.status.fecha_planta != None:
        dia = str(solicitud.status.fecha_planta.day)
        mes = str(solicitud.status.fecha_planta.month)
        año = str(solicitud.status.fecha_planta.year)
    else:
        dia = "NR"
        mes = "NR"
        año = "NR"

    c.rect(185,598-margen, 150, 55)
    c.line(185,618-margen,335,618-margen)
    c.line(185,638-margen,335,638-margen)
    c.line(230,650-margen,230,598-margen)
    c.line(290,650-margen,290,598-margen)
    c.drawCentredString(210,620-margen,dia)
    c.drawCentredString(260,620-margen,mes)
    c.drawCentredString(310,620-margen,año)
    c.drawString(40,600-margen,'FECHA DE SOLICITUD:')
    c.drawCentredString(210,600-margen,str(now.day))
    c.drawCentredString(260,600-margen,str(now.month))
    c.drawCentredString(310,600-margen,str(now.year))
    c.drawString(200,640-margen,'DIA')
    c.drawString(250,640-margen,'MES')
    c.drawString(300,640-margen,'AÑO')
    c.drawString(400,600-margen,'FIRMA DEL SOLICITANTE')
    c.rect(390,598-margen, 155, 55)
    c.line(390,610-margen,545,610-margen)

    c.drawString(40,560-altura,'PERIODO VACACIONAL CORRESPONDIENTE:')
    c.drawCentredString(425,560-altura, año1)
    c.drawCentredString(450,560-altura, '/')
    c.drawCentredString(475,560-altura, año2)
    c.rect(35,558-altura, 255, 12)
    c.rect(360,558-altura, 190, 12)
    #form = VacacionesFormato(request.POST,)
    c.drawString(40,540-altura,'NO. DE DIAS DE VACACIONES:')
    c.drawCentredString(450,540-altura,diferencia)
    c.rect(35,538-altura, 175, 12)
    c.rect(360,538-altura, 190, 12)
    c.drawString(40,520-altura,'CON GOCE DE SUELDO:')
    c.rect(35,518-altura, 140, 12)
    c.drawString(380,520-altura,'SI')
    c.rect(360,518-altura, 50, 12)
    c.drawString(425,520-altura,'NO')
    c.rect(410,518-altura, 50, 12)
    c.drawString(40,500-altura,'FECHA QUE DESEA SALIR DE VACACIONES:')
    c.drawCentredString(450,500-altura,str(inicio))
    c.rect(35,498-altura, 250, 12)
    c.rect(360,498-altura, 190, 12)
    c.drawString(40,480-altura,'FECHA DE REGRESO A LABORES:')
    c.drawCentredString(450,480-altura,str(fin))
    c.rect(35,478-altura, 195, 12)
    c.rect(360,478-altura, 190, 12)
    if cuenta >= 3: ########### Para formatos largos
        c.drawCentredString(300,440,'Entrega-Recepción')
        c.setFont('Helvetica',11)
        c.drawString(40,400,'DATOS DE QUIEN RECIBE:')
        c.drawString(40,380,'Nombre:')
        if solicitud.recibe_nombre:
            c.drawString(100,380,solicitud.recibe_nombre)
        c.line(90,378,375,378)
        c.drawString(385,380,'Area:')
        if solicitud.recibe_area:
            c.drawString(435,380,solicitud.recibe_area)
        c.line(420,378,560,378)
        c.drawString(40,360,'Puesto:')
        if solicitud.recibe_puesto:
            c.drawString(100,360,solicitud.recibe_puesto)
        c.line(90,358,375,358)
        c.drawString(40,340,'Sector:')
        if solicitud.recibe_sector:
            c.drawString(100,340,solicitud.recibe_sector)
        c.line(90,338,375,338)
        c.setFont('Helvetica-Bold',14)
        c.drawString(40,300,'SITUACIÓN DE TRABAJOS ENCOMENDADOS:')
        c.setFillColor(black)
        c.setFont('Helvetica',11)

        # Estilo de párrafo para los datos en la tabla
        styleSheet = getSampleStyleSheet()
        paragraphStyle = styleSheet['Normal']
        paragraphStyle.fontSize = 8
        #Tabla y altura guia
        high = 130
        trabajos = Trabajos_encomendados.objects.filter(solicitud_vacaciones__id=solicitud.id)
        data = []
        data.append(['No.', 'DENOMINACIÓN ASUNTO', 'ESTADO'])

        numero = 1  # Inicializar el número

        for index, trabajo in enumerate(trabajos, start=1):
            trabajo_data = []
            for i in range(1, 11):
                asunto = getattr(trabajo, f'asunto{i}', '')
                estado = getattr(trabajo, f'estado{i}', '')
                trabajo_data.append((numero, asunto, estado))
                numero += 1  # Incrementar el número
            data.extend(trabajo_data)
        high = high - 20

        #Propiedades de la tabla
        width, height = landscape(letter)
        table_style = TableStyle([ #estilos de la tabla
            #ENCABEZADO
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TEXTCOLOR',(0,0),(-1,0), colors.black),
            ('FONTSIZE',(0,0),(-1,0), 12),
            ('BACKGROUND',(0,0),(-1,0), colors.white),
            #CUERPO
            ('TEXTCOLOR',(0,1),(-1,-1), colors.black),
            ('FONTSIZE',(0,1),(-1,-1), 12),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ])

        # Definir variables para el salto de página
        rows_per_page = 7
        total_rows = len(data) - 1  # Excluye el encabezado
        current_row = 1  # Comenzar desde la primera fila (excluyendo el encabezado)

        # Generar páginas con el contenido restante
        while current_row <= total_rows:
            # Calcular el espacio disponible en la página actual
            available_height = height - 70 - 20  # Ajustar según el espaciado

            # Calcular cuántas filas caben en la página actual
            if current_row == 1:
                rows_on_page = min(rows_per_page, math.floor((available_height - 20) / 20))  # Para la primera página
            else:
                rows_on_page = min(20, math.floor((available_height - 20) / 20))  # Para las páginas restantes

            # Obtener los datos para la página actual
            end_row = int(current_row + rows_on_page) if current_row + rows_on_page <= total_rows else total_rows + 1
            page_data = data[current_row:end_row]

            # Reemplazar valores None con un espacio en blanco
            page_data = [[cell if cell is not None else " " for cell in row] for row in page_data]

            # Calcular la altura para dibujar la tabla
            table_height = len(page_data) * 20

            # Calcular la posición vertical para la tabla
            if current_row == 1:
                # Ajustar el margen superior para la primera tabla
                table_y = height - 130 - table_height - 275  # Usar la altura específica para la primera tabla
            else:
                # Calcular el margen desde la parte superior de la página
                margin_top = 40
                table_y = height - table_height - margin_top

            # Dentro del bucle para crear la tabla de cada página
            table_data = []
            for row in page_data:
                table_row = []
                for cell_data in row:
                    if isinstance(cell_data, str) and len(cell_data) > 30:
                        # Aplicar estilo CSS para dividir palabras largas
                        cell_data = cell_data.replace(' ', '<br/>')
                        cell_data = f'<font size="12">{cell_data}</font>'
                        cell = Paragraph(cell_data, paragraphStyle)
                    else:
                        cell = cell_data
                    table_row.append(cell)
                table_data.append(table_row)

            # Crear la tabla para la página actual
            table = Table([data[0]] + table_data, colWidths=[1.5 * cm, 8 * cm, 10 * cm], repeatRows=1)
            table.setStyle(table_style)

            # Dibujar la tabla en la página actual
            table.wrapOn(c, width, height)
            table.drawOn(c, 25, table_y)

            # Avanzar al siguiente conjunto de filas
            current_row += rows_on_page

            # Cambiar la cantidad de filas por página después de la primera página
            if current_row == 1:
                rows_per_page = 20

            # Agregar una nueva página si quedan más filas por dibujar
            if current_row <= total_rows:
                c.showPage()
        c.showPage()
        c.setFont('Helvetica-Bold',12)
        #Parrafo con salto de linea automatica si el texto es muy largo
        text = " "
        if solicitud.informacion_adicional:
            text = solicitud.informacion_adicional
        x = 40
        y = 750
        c.setFillColor(black)
        c.setFont('Helvetica', 12)
        c.drawString(x + 5, y - 15, 'INFORMACIÓN ADICIONAL:')
        c.setFont('Helvetica', 9)
        lines = textwrap.wrap(text, width=100)
        for line in lines:
            c.drawString(x + 10, y - 35, line)
            y -= 15

        # Estilo de párrafo para los comentarios
        styleSheet = getSampleStyleSheet()
        commentStyle = styleSheet['Normal']
        commentStyle.fontSize = 8

        def format_comment(comment):
            if comment is None:
                return ""
            return Paragraph(comment, commentStyle)

        # Datos y ajustes de la tabla
        data2 = []
        high = 465
        data2.append(['No.', 'TEMAS', 'COMENTARIO'])
        data2.append(["1", "Información sobre personal a su cargo", format_comment(solicitud.temas.comentario1)])
        data2.append(["2", "Documentos", format_comment(solicitud.temas.comentario2)])
        data2.append(["3", Paragraph("Arqueo de caja o cuenta bancaria a su cargo (cuando aplique)"), format_comment(solicitud.temas.comentario3)])
        data2.append(["4", "Proyectos pendientes", format_comment(solicitud.temas.comentario4)])
        data2.append(["5", "Estado de las operaciones a su cargo", format_comment(solicitud.temas.comentario5)])
        data2.append(["6", "Deudas con la empresa", format_comment(solicitud.temas.comentario6)])
        data2.append(["7", "Saldos por comprobar a contabilidad", format_comment(solicitud.temas.comentario7)])
        data2.append(["8", "Activos asignados", format_comment(solicitud.temas.comentario8)])
        data2.append(["9", "Otros", format_comment(solicitud.temas.comentario9)])

        table = Table(data2, colWidths=[1.5 * cm, 8 * cm, 11 * cm,], repeatRows=1)
        table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TEXTCOLOR',(0,0),(-1,0), colors.black),
            ('FONTSIZE',(0,0),(-1,0), 13),
            ('BACKGROUND',(0,0),(-1,0), colors.white),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ]))

        # Dibujar la tabla en el lienzo
        table.wrapOn(c, width, height)
        table.drawOn(c, 25, high)

        #c.drawString(40,375,'ANEXOS:')
        text = " "
        if solicitud.anexos:
            text = solicitud.anexos
        x = 40
        y = 380
        c.setFillColor(black)
        c.setFont('Helvetica', 12)
        c.drawString(x + 5, y - 15, 'Anexos:')
        c.setFont('Helvetica', 9)
        lines = textwrap.wrap(text, width=100)
        for line in lines:
            c.drawString(x + 10, y - 30, line)
            y -= 25
        c.line(40,345,570,345)
        c.line(40,320,570,320)
        c.line(40,293,570,293)
        c.line(40,270,570,270)
        c.drawCentredString(200,170,'ENTREGUE (NOMBRE Y FIRMA)')
        c.drawCentredString(200,190,nombre_completo)
        c.line(105,185,295,185)
        c.drawCentredString(400,170,'RECIBI (NOMBRE Y FIRMA)')
        c.drawCentredString(400,190,solicitud.recibe_nombre)
        c.line(320,185,480,185)

    c.drawCentredString(200,70,'FIRMA DE GERENCIA')
    c.rect(120,68, 160, 70)
    c.line(120,80,280,80)
    c.drawCentredString(400,70,'FIRMA DE JEFE INMEDIATO')
    c.rect(300,68, 195, 70)
    c.line(300,80,495,80)
    c.save()
    c.showPage()
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename='Formato_Vacaciones.pdf')



