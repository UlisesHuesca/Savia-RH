from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from proyecto.models import UserDatos, Perfil, Catorcenas, Costo, TablaFestivos, Vacaciones, Economicos, Economicos_dia_tomado, Vacaciones_dias_tomados, Empresa, Solicitud_vacaciones, Solicitud_economicos, Trabajos_encomendados
from proyecto.models import TablaVacaciones,SalarioDatos,DatosISR

from django.db import models
from django.db.models import Subquery, OuterRef, Q
from revisar.models import AutorizarPrenomina, Estado
from proyecto.filters import CostoFilter
from .models import Prenomina, Retardos, Castigos, Permiso_goce, Permiso_sin, Descanso, Incapacidades, Faltas, Comision, Domingo, Dia_extra
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

from .forms import IncapacidadesForm
from proyecto.models import Variables_imss_patronal
from proyecto.models import SalarioDatos
# Create your views here.

@login_required(login_url='user-login')
def Tabla_prenomina(request):
    user_filter = UserDatos.objects.get(user=request.user)
    revisar_perfil = Perfil.objects.get(distrito=user_filter.distrito,numero_de_trabajador=user_filter.numero_de_trabajador)
    empresa_faxton = Empresa.objects.get(empresa="Faxton")
    if user_filter.tipo.nombre == "RH":
        ahora = datetime.date.today()
        #ahora = datetime.date.today() + timedelta(days=10)
        catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
        if revisar_perfil.empresa == empresa_faxton:
            costo = Costo.objects.filter(complete=True, status__perfil__baja=False,status__perfil__empresa=empresa_faxton).order_by("status__perfil__numero_de_trabajador")
        elif user_filter.distrito.distrito == 'Matriz':
            costo = Costo.objects.filter(complete=True, status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador")
        else:
            costo = Costo.objects.filter(status__perfil__distrito=user_filter.distrito, complete=True,  status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador")

        prenominas = Prenomina.objects.filter(empleado__in=costo,fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])

        #crear las prenominas actuales si es que ya es nueva catorcena
        for empleado in costo:
            #checar si existe prenomina para el empleado en la catorcena actual
            prenomina_existente = prenominas.filter(empleado=empleado).exists()
            #si no existe crear una nueva prenomina
            if not prenomina_existente:
                nueva_prenomina = Prenomina(empleado=empleado, fecha=ahora)
                nueva_prenomina.save()
        #costo_filter = CostoFilter(request.GET, queryset=costo)
        #costo = costo_filter.qs
        prenominas = Prenomina.objects.filter(empleado__in=costo,fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]).order_by("empleado__status__perfil__numero_de_trabajador")
        
        prenomina_filter = PrenominaFilter(request.GET, queryset=prenominas)
        prenominas = prenomina_filter.qs

        for prenomina in prenominas:
            ultima_autorizacion = AutorizarPrenomina.objects.filter(prenomina=prenomina).order_by('-updated_at').first() #Ultimo modificado

            if ultima_autorizacion is not None:
                prenomina.valor = ultima_autorizacion.estado.tipo #Esta bien como agarra el dato de RH arriba que es el primero
            prenomina.estado_general = determinar_estado_general(ultima_autorizacion)

        if request.method =='POST' and 'Autorizar' in request.POST:
            if user_filter.tipo.nombre ==  "RH":
                prenominas_filtradas = [prenom for prenom in prenominas if prenom.estado_general == 'RH pendiente (rechazado por Controles técnicos)' or prenom.estado_general == 'RH pendiente (rechazado por Gerencia)' or prenom.estado_general == 'Sin autorizaciones']
                if prenominas_filtradas:
                    # Llamar a la función Autorizar_gerencia con las prenominas filtradas
                    return Autorizar_general(request,prenominas_filtradas, user_filter)
                else:
                    # Si no hay prenominas que cumplan la condición, manejar según sea necesario
                    messages.error(request,'Ya se han autorizado todas las prenominas pendientes')
        if request.method =='POST' and 'Excel' in request.POST:
            return Excel_estado_prenomina(request,prenominas, user_filter)
        if request.method =='POST' and 'Excel2' in request.POST:
            return Excel_estado_prenomina_formato(prenominas, user_filter)
        


        p = Paginator(prenominas, 50)
        page = request.GET.get('page')
        salidas_list = p.get_page(page)

        context = {
            'prenomina_filter':prenomina_filter,
            'salidas_list': salidas_list,
            'prenominas':prenominas
        }
        return render(request, 'prenomina/Tabla_prenomina.html', context)
    else:
            return render(request, 'revisar/403.html')

@login_required(login_url='user-login')
def Autorizar_general(request,prenominas, user_filter):
    if request.user.is_authenticated:
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
        return redirect('Prenomina')  # Cambia 'ruta_a_redirigir' por la URL a la que deseas redirigir después de autorizar las prenóminas

@login_required(login_url='user-login')
def capturarIncidencias(request, incidencia,fecha_incio,fecha_fin,prenomina,comentario,nombre):
            
            url = request.FILES['url']
            
            if incidencia == '1':
                evento_model = Incapacidades
            elif incidencia == '2':
                evento_model = Castigos
            elif incidencia == '3':
                evento_model = Permiso_goce
            elif incidencia == '4':
                evento_model = Permiso_sin
                
            if evento_model:
                if url:
                    obj, created = evento_model.objects.update_or_create(fecha=fecha_incio, fecha_fin=fecha_fin, prenomina=prenomina, defaults={'comentario': comentario, 'editado': f"E:{nombre.nombres} {nombre.apellidos}"})
                    obj.url = url
                    obj.save()
                else:
                    evento_model.objects.update_or_create(fecha=fecha_incio, fecha_fin=fecha_fin, prenomina=prenomina, defaults={'comentario': comentario, 'editado': f"E:{nombre.nombres} {nombre.apellidos}"})
            else:
                #  donde nuevo_estado no tiene un mapeo en el diccionario
                print(f"Error: nuevo_estado desconocido")
            
            messages.success(request, 'Cambios guardados exitosamente')
            
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='user-login')
def programar_incidencias(request,pk):
    # crea el nuevo dato según el nuevo estado o comentario
    if request.method == 'POST' and 'btn_incidencias' in request.POST:
        
        #saber catorcena
        ahora = datetime.date.today()
        #ahora = datetime.date.today() + timedelta(days=10)
        catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
        
        #RH
        user_filter = UserDatos.objects.get(user=request.user)
        nombre = Perfil.objects.get(numero_de_trabajador = user_filter.numero_de_trabajador, distrito = user_filter.distrito)
        
        #Empleado
        costo = Costo.objects.get(id=pk)
        prenomina = Prenomina.objects.get(empleado=costo,fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])
        
        #Se trae el formulario de las incapacidades para ser validado
        form_incidencias = IncapacidadesForm(request.POST, request.FILES)
        
        if form_incidencias.is_valid():
            incidencia = form_incidencias.cleaned_data.get('incidencias')
            fecha_incio = form_incidencias.cleaned_data['fecha']
            fecha_fin = form_incidencias.cleaned_data['fecha_fin']
            comentario = form_incidencias.cleaned_data['comentario']       
            
            #VALIDACIONES
            if fecha_incio > fecha_fin:
                print("La fecha de inicio es posterior a la fecha final.")
                messages.error(request, 'La fecha de inicio debe ser menor a la fecha final')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            
            if not incidencia:
                messages.error(request, 'Debes seleccionar una incidencia')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            
            if fecha_incio < catorcena_actual.fecha_inicial:
                messages.error(request, 'No puedes agregar una fecha anterior de la catorcena actual')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            
            vacaciones = Vacaciones_dias_tomados.objects.filter(Q(prenomina__status=prenomina.empleado.status, fecha_inicio__range=[fecha_incio, fecha_fin]) | Q(prenomina__status=prenomina.empleado.status, fecha_fin__range=[fecha_incio, fecha_fin]))
            if vacaciones.exists():
                messages.error(request, 'Ya existen vacaciones dentro del rango de fechas especificado')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            
            economicos = Economicos_dia_tomado.objects.filter(prenomina__status=prenomina.empleado.status, fecha__range=[fecha_incio, fecha_fin])
            if economicos.exists():            
                messages.error(request, 'Ya existen economicos dentro del rango de fechas especificado')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            
            festivos = TablaFestivos.objects.filter(dia_festivo__range=[fecha_incio, fecha_fin])
            if festivos.exists():
                messages.error(request, 'Ya existen festivos dentro del rango de fechas especificado')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))        
            
            #VALIDAR INCIDENCIAS - EDITAR UNA INCIDENCIA QUE ESTE DENTRO DEL RANGO DE LA CAT Y VERIFICAR QUE EXISTA EN LA CAT ANTERIOIR
            incapacidades = Incapacidades.objects.filter(
                prenomina__empleado_id=prenomina.empleado.id,
                fecha__lte=fecha_fin,  # La fecha de inicio de la incapacidad debe ser menor o igual a la fecha fin del rango proporcionado
                fecha_fin__gte=fecha_incio,   # La fecha fin de la incapacidad debe ser mayor o igual a la fecha inicio del rango proporcionado
            )
            
            castigos = Castigos.objects.filter(
                prenomina__empleado_id=prenomina.empleado.id,
                fecha__lte=fecha_fin,
                fecha_fin__gte=fecha_incio,
            )
            
            permisos_goce = Permiso_goce.objects.filter(
                prenomina__empleado_id=prenomina.empleado.id,
                fecha__lte=fecha_fin,
                fecha_fin__gte=fecha_incio,
            )
            
            permisos_sin = Permiso_sin.objects.filter(
                prenomina__empleado_id=prenomina.empleado.id,
                fecha__lte=fecha_fin,
                fecha_fin__gte=fecha_incio,
            )
            
            #elimina una incapacidad y es remplazada por otra en caso que sea de la misma catorcena
            if incapacidades.exists():
                if incapacidades.filter(fecha__lt=catorcena_actual.fecha_inicial).exists():
                    messages.error(request, 'Ya existen incapacidades de la catorcena anterior')
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))   
                else:
                    #se elimina el soporte asociado
                    soporte = incapacidades.first()
                    os.remove(soporte.url.path)
                    #se elima la incapacidad de la BD
                    incapacidades.delete()
                    
            if castigos.exists():
                if castigos.filter(fecha__lt=catorcena_actual.fecha_inicial).exists():
                    messages.error(request, 'Ya existen castigos de la catorcena anterior')
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))   
                else:
                    # Se elimina el soporte asociado
                    soporte = castigos.first()
                    os.remove(soporte.url.path)
                    # Se elimina el castigo de la BD
                    castigos.delete()
            
            if permisos_goce.exists():
                if permisos_goce.filter(fecha__lt=catorcena_actual.fecha_inicial).exists():
                    messages.error(request, 'Ya existen permisos de goce de sueldo de la catorcena anterior')
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))   
                else:
                    # Se elimina el soporte asociado
                    soporte = permisos_goce.first()
                    os.remove(soporte.url.path)
                    # Se elimina el permiso de goce de la BD
                    permisos_goce.delete()
            
            if permisos_sin.exists():
                if permisos_sin.filter(fecha__lt=catorcena_actual.fecha_inicial).exists():
                    messages.error(request, 'Ya existen permisos sin goce de sueldo de la catorcena anterior')
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))   
                else:
                    # Se elimina el soporte asociado
                    soporte = permisos_sin.first()
                    os.remove(soporte.url.path)
                    # Se elimina el permiso sin goce de la BD
                    permisos_sin.delete()        
            
            capturarIncidencias(request, incidencia,fecha_incio,fecha_fin,prenomina,comentario,nombre)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
        else:
            for field, errors in form_incidencias.errors.items():
                for error in errors:
                    messages.error(request,error)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                    
            

@login_required(login_url='user-login')
def prenomina_revisar_ajax(request, pk):
    user_filter = UserDatos.objects.get(user=request.user)
    ahora = datetime.date.today()
    #ahora = datetime.date.today() + timedelta(days=10)
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
    #prenomina.castigos = prenomina.castigos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    #prenomina.permiso_goce = prenomina.permiso_goce_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) 
    #prenomina.permiso_sin = prenomina.permiso_sin_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.incapacidades = Incapacidades.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
    prenomina.permiso_goce = Permiso_goce.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
    prenomina.permiso_sin = Permiso_sin.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
    prenomina.castigos = Castigos.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))

    prenomina.descanso = prenomina.descanso_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    #prenomina.incapacidades = prenomina.incapacidades_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    #prenomina.incapacidades = Incapacidades.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
    prenomina.faltas = prenomina.faltas_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.comision = prenomina.comision_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.domingo = prenomina.domingo_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
    prenomina.extra = prenomina.dia_extra_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))

    #fechas con factores
    fechas_con_retardos = [retardo.fecha for retardo in prenomina.retardos]
    #fechas_con_castigos = [castigo.fecha for castigo in prenomina.castigos]
    #fechas_con_permiso_goce = [permiso_goc.fecha for permiso_goc in prenomina.permiso_goce]
    #fechas_con_permiso_sin = [permiso_si.fecha for permiso_si in prenomina.permiso_sin]
    fechas_con_descanso = [descans.fecha for descans in prenomina.descanso]
    #fechas_con_incapacidades = [incapacidade.fecha for incapacidade in prenomina.incapacidades]
    fechas_con_faltas = [falta.fecha for falta in prenomina.faltas]
    fechas_con_comision = [comisio.fecha for comisio in prenomina.comision]
    fechas_con_domingo = [doming.fecha for doming in prenomina.domingo]
    fechas_con_extra = [extra.fecha for extra in prenomina.extra]
    fechas_con_festivos = [festivo.dia_festivo for festivo in festivos]
    fechas_con_economicos = [economico.fecha for economico in economicos]

    # todas las fechas de la catorcena actual
    delta = catorcena_actual.fecha_final - catorcena_actual.fecha_inicial
    dias_entre_fechas = [catorcena_actual.fecha_inicial + timedelta(days=i) for i in range(delta.days + 1)]

    #lista de tuplas con la fecha y su etiqueta
    fechas_con_etiquetas = [(fecha, "retardo", prenomina.retardos.filter(fecha=fecha).first().comentario if fecha in fechas_con_retardos else "") if fecha in fechas_con_retardos
                            else (fecha, "castigo", prenomina.castigos.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario if any(castigos.fecha <= fecha <= castigos.fecha_fin for castigos in prenomina.castigos) else "") if any(castigos.fecha <= fecha <= castigos.fecha_fin for castigos in prenomina.castigos)
                            else (fecha, "permiso con goce de sueldo", prenomina.permiso_goce.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario if any(permiso_goce.fecha <= fecha <= permiso_goce.fecha_fin for permiso_goce in prenomina.permiso_goce) else "") if any(permiso_goce.fecha <= fecha <= permiso_goce.fecha_fin for permiso_goce in prenomina.permiso_goce)
                            else (fecha, "permiso sin goce de sueldo", prenomina.permiso_sin.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario if any(permiso_sin.fecha <= fecha <= permiso_sin.fecha_fin for permiso_sin in prenomina.permiso_sin) else "") if any(permiso_sin.fecha <= fecha <= permiso_sin.fecha_fin for permiso_sin in prenomina.permiso_sin)
                            else (fecha, "incapacidades", prenomina.incapacidades.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario if any(incapacidad.fecha <= fecha <= incapacidad.fecha_fin for incapacidad in prenomina.incapacidades) else "") if any(incapacidad.fecha <= fecha <= incapacidad.fecha_fin for incapacidad in prenomina.incapacidades)
                            
                            else (fecha, "descanso", prenomina.descanso.filter(fecha=fecha).first().comentario if fecha in fechas_con_descanso else "") if fecha in fechas_con_descanso
                            #else (fecha, "incapacidades", prenomina.incapacidades.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario, prenomina.incapacidades.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().url if any(incapacidad.fecha <= fecha <= incapacidad.fecha_fin for incapacidad in prenomina.incapacidades) else "") if any(incapacidad.fecha <= fecha <= incapacidad.fecha_fin for incapacidad in prenomina.incapacidades)
                            else (fecha, "faltas",prenomina.faltas.filter(fecha=fecha).first().comentario if fecha in fechas_con_faltas else "") if fecha in fechas_con_faltas
                            else (fecha, "comision", prenomina.comision.filter(fecha=fecha).first().comentario if fecha in fechas_con_comision else "") if fecha in fechas_con_comision
                            else (fecha, "domingo", prenomina.domingo.filter(fecha=fecha).first().comentario if fecha in fechas_con_domingo else "") if fecha in fechas_con_domingo
                            else (fecha, "día de descanso laborado", prenomina.extra.filter(fecha=fecha).first().comentario if fecha in fechas_con_extra else "") if fecha in fechas_con_extra
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

@login_required(login_url='user-login')
def PrenominaRevisar(request, pk):
    user_filter = UserDatos.objects.get(user=request.user)
    if user_filter.tipo.nombre == "RH":
        ahora = datetime.date.today()
        #ahora = datetime.date.today() + timedelta(days=10)
        incapacidadesform = IncapacidadesForm()
        costo = Costo.objects.get(id=pk)
        catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
        prenomina = Prenomina.objects.get(empleado=costo,fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])
        dato=prenomina
        festivos = TablaFestivos.objects.filter(dia_festivo__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]) #festivos en la catorcena actual
        economicos = Economicos_dia_tomado.objects.filter(prenomina__status=prenomina.empleado.status, fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])
        vacaciones = Vacaciones_dias_tomados.objects.filter(Q(prenomina__status=prenomina.empleado.status, fecha_inicio__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]) | Q(prenomina__status=prenomina.empleado.status, fecha_fin__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])) #Comparar con la fecha final tambien
        #vacaciones = Vacaciones_dias_tomados.objects.filter(prenomina__status=prenomina.empleado.status) #Comparar con la fecha final tambien

        
        autorizacion1 = prenomina.autorizarprenomina_set.filter(tipo_perfil__nombre="Control Tecnico").first()
        autorizacion2 = prenomina.autorizarprenomina_set.filter(tipo_perfil__nombre="Gerencia").first()

        #obtener factores de días asociados a cada prenomina
        prenomina.retardos = prenomina.retardos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
        #prenomina.castigos = prenomina.castigos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
        prenomina.castigos = Castigos.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        #prenomina.permiso_goce = prenomina.permiso_goce_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) 
        prenomina.permiso_goce = Permiso_goce.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        #prenomina.permiso_sin = prenomina.permiso_sin_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
        prenomina.permiso_sin = Permiso_sin.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        #prenomina.descanso = prenomina.descanso_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
        prenomina.descanso = prenomina.descanso_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
        #prenomina.incapacidades = prenomina.incapacidades_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
        prenomina.incapacidades = Incapacidades.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
                    
        prenomina.faltas = prenomina.faltas_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
        prenomina.comision = prenomina.comision_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
        prenomina.domingo = prenomina.domingo_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
        prenomina.extra = prenomina.dia_extra_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))

        #fechas con factores
        fechas_con_retardos = [retardo.fecha for retardo in prenomina.retardos]
        #fechas_con_castigos = [castigo.fecha for castigo in prenomina.castigos]
        #fechas_con_permiso_goce = [permiso_goc.fecha for permiso_goc in prenomina.permiso_goce]
        #fechas_con_permiso_sin = [permiso_si.fecha for permiso_si in prenomina.permiso_sin]
        fechas_con_descanso = [descans.fecha for descans in prenomina.descanso]
        #fechas_con_incapacidades = [incapacidade.fecha for incapacidade in prenomina.incapacidades]
        fechas_con_faltas = [falta.fecha for falta in prenomina.faltas]
        fechas_con_comision = [comisio.fecha for comisio in prenomina.comision]
        fechas_con_domingo = [doming.fecha for doming in prenomina.domingo]
        fechas_con_extra = [extra.fecha for extra in prenomina.extra]
        fechas_con_festivos = [festivo.dia_festivo for festivo in festivos]
        fechas_con_economicos = [economico.fecha for economico in economicos]

        # todas las fechas de la catorcena actual
        delta = catorcena_actual.fecha_final - catorcena_actual.fecha_inicial
        dias_entre_fechas = [catorcena_actual.fecha_inicial + timedelta(days=i) for i in range(delta.days + 1)]

        #lista de tuplas con la fecha y su etiqueta
        fechas_con_etiquetas = [(fecha, "retardo", prenomina.retardos.filter(fecha=fecha).first().comentario if fecha in fechas_con_retardos else "") if fecha in fechas_con_retardos
                                #else (fecha, "castigo", prenomina.castigos.filter(fecha=fecha).first().comentario if fecha in fechas_con_castigos else "") if fecha in fechas_con_castigos
                                else (fecha, "castigo", prenomina.castigos.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario, prenomina.castigos.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().url if any(castigos.fecha <= fecha <= castigos.fecha_fin for castigos in prenomina.castigos) else "") if any(castigos.fecha <= fecha <= castigos.fecha_fin for castigos in prenomina.castigos)
                                #else (fecha, "permiso_goce", prenomina.permiso_goce.filter(fecha=fecha).first().comentario, prenomina.permiso_goce.filter(fecha=fecha).first().url if fecha in fechas_con_permiso_goce and prenomina.permiso_goce.filter(fecha=fecha).first().url else "") if fecha in fechas_con_permiso_goce
                                else (fecha, "permiso con goce de sueldo", prenomina.permiso_goce.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario, prenomina.permiso_goce.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().url if any(permiso_goce.fecha <= fecha <= permiso_goce.fecha_fin for permiso_goce in prenomina.permiso_goce) else "") if any(permiso_goce.fecha <= fecha <= permiso_goce.fecha_fin for permiso_goce in prenomina.permiso_goce)
                                #else (fecha, "permiso_sin", prenomina.permiso_sin.filter(fecha=fecha).first().comentario, prenomina.permiso_sin.filter(fecha=fecha).first().url if fecha in fechas_con_permiso_sin and prenomina.permiso_sin.filter(fecha=fecha).first().url else "") if fecha in fechas_con_permiso_sin
                                else (fecha, "permiso sin goce de sueldo", prenomina.permiso_sin.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario, prenomina.permiso_sin.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().url if any(permiso_sin.fecha <= fecha <= permiso_sin.fecha_fin for permiso_sin in prenomina.permiso_sin) else "") if any(permiso_sin.fecha <= fecha <= permiso_sin.fecha_fin for permiso_sin in prenomina.permiso_sin)
                                #else (fecha, "incapacidades", prenomina.incapacidades.filter(fecha=fecha).first().comentario, prenomina.incapacidades.filter(fecha=fecha).first().url if fecha in fechas_con_incapacidades and prenomina.incapacidades.filter(fecha=fecha).first().url else "") if fecha in fechas_con_incapacidades
                                else (fecha, "descanso", prenomina.descanso.filter(fecha=fecha).first().comentario if fecha in fechas_con_descanso else "") if fecha in fechas_con_descanso
                                else (fecha, "incapacidades", prenomina.incapacidades.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario, prenomina.incapacidades.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().url if any(incapacidad.fecha <= fecha <= incapacidad.fecha_fin for incapacidad in prenomina.incapacidades) else "") if any(incapacidad.fecha <= fecha <= incapacidad.fecha_fin for incapacidad in prenomina.incapacidades)
                                else (fecha, "faltas",prenomina.faltas.filter(fecha=fecha).first().comentario if fecha in fechas_con_faltas else "") if fecha in fechas_con_faltas
                                else (fecha, "comision", prenomina.comision.filter(fecha=fecha).first().comentario, prenomina.comision.filter(fecha=fecha).first().url if fecha in fechas_con_comision and prenomina.comision.filter(fecha=fecha).first().url else "") if fecha in fechas_con_comision
                                else (fecha, "domingo", prenomina.domingo.filter(fecha=fecha).first().comentario if fecha in fechas_con_domingo else "") if fecha in fechas_con_domingo
                                else (fecha, "día extra", prenomina.extra.filter(fecha=fecha).first().comentario, prenomina.extra.filter(fecha=fecha).first().url if fecha in fechas_con_extra and prenomina.extra.filter(fecha=fecha).first().url else "") if fecha in fechas_con_extra
                                #else (fecha, "día extra", prenomina.extra.filter(fecha=fecha).first().comentario, prenomina.extra.filter(fecha=fecha).first().url if fecha in fechas_con_extra and prenomina.extra.filter(fecha=fecha).first().url else "") if fecha in fechas_con_extra
                                else (fecha, "economico", "") if fecha in fechas_con_economicos
                                else (fecha, "festivo", "") if fecha in fechas_con_festivos
                                else (fecha, "vacaciones", "") if any(vacacion.fecha_inicio <= fecha <= vacacion.fecha_fin and fecha != vacacion.dia_inhabil for vacacion in vacaciones)
                                else (fecha, "asistencia", "") for fecha in dias_entre_fechas]
                                        #else (fecha, "día extra", prenomina.extra.filter(fecha=fecha).first().comentario if fecha in fechas_con_extra else "") if fecha in fechas_con_extra

        fechas_con_etiquetas = [
            item + ('',) if len(item) == 3 else item for item in fechas_con_etiquetas
        ]
        if catorcena_actual:
            delta = catorcena_actual.fecha_final - catorcena_actual.fecha_inicial
            dias_entre_fechas = [catorcena_actual.fecha_inicial + timedelta(days=i) for i in range(delta.days + 1)]
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
        if request.method == 'POST' and 'guardar_cambios' in request.POST:
            revisado_rh, created = AutorizarPrenomina.objects.get_or_create(prenomina=prenomina, tipo_perfil=user_filter.tipo)
            estado_verificado = Estado.objects.get(tipo="aprobado")
            revisado_rh.estado=estado_verificado
            nombre = Perfil.objects.get(numero_de_trabajador = user_filter.numero_de_trabajador, distrito = user_filter.distrito)
            revisado_rh.perfil=nombre
            revisado_rh.comentario="Revisado por RH"
            revisado_rh.save()
            for fecha, etiqueta, comentario, archivo in fechas_con_etiquetas:
                fecha_str = fecha.strftime('%Y-%m-%d')
                nuevo_estado = request.POST.get(f'estado_{fecha_str}')
                nuevo_comentario = request.POST.get(f'comentario_{fecha_str}')

                # revisa si el estado ha cambiado
                if nuevo_estado and nuevo_estado != etiqueta:
                    
                    #Funcion para eliminar el soport y la fecha de la incidencia en la BD, se le pasa un queryset
                    def eliminar_soporte_incidencia(queryset):
                        if queryset.exists():
                            archivo = queryset.first()
                            if os.path.isfile(archivo.url.path):
                                os.remove(archivo.url.path)
                            archivo.delete() 
                            
                    # elimina el dato asociado a la fecha
                    prenomina.retardos.filter(fecha=fecha).delete()
                    castigos = prenomina.castigos.filter(fecha__lte=fecha, fecha_fin__gte=fecha).delete()
                    permiso_goce = prenomina.permiso_goce.filter(fecha__lte=fecha, fecha_fin__gte=fecha)
                    eliminar_soporte_incidencia(permiso_goce)
                    permiso_sin = prenomina.permiso_sin.filter(fecha__lte=fecha, fecha_fin__gte=fecha)
                    eliminar_soporte_incidencia(permiso_sin)
                    prenomina.descanso.filter(fecha=fecha).delete()
                    incapacidades = prenomina.incapacidades.filter(fecha__lte=fecha, fecha_fin__gte=fecha)
                    eliminar_soporte_incidencia(incapacidades)
                    prenomina.faltas.filter(fecha=fecha).delete()
                    comision = prenomina.comision.filter(fecha=fecha)
                    eliminar_soporte_incidencia(comision)
                    prenomina.domingo.filter(fecha=fecha).delete()
                    extra = prenomina.extra.filter(fecha=fecha).delete()
                    #eliminar_soporte_incidencia(extra)
                    
                # crea el nuevo dato según el nuevo estado o comentario
                if nuevo_estado and nuevo_estado != 'asistencia':
                    evento_model = {
                        'retardo': Retardos,
                        #'castigo': Castigos,
                        #'permiso_goce': Permiso_goce,  
                        #'permiso_sin': Permiso_sin,  
                        'descanso': Descanso,  
                        #'incapacidades': Incapacidades,  
                        'faltas': Faltas,  
                        'comision': Comision,  
                        'domingo': Domingo,  
                        'día extra': Dia_extra,  
                    }.get(nuevo_estado)

                    if evento_model:
                        archivo = request.FILES.get(f'archivo_{fecha_str}')  # Obtener el archivo de la solicitud
                        if archivo:
                            obj, created = evento_model.objects.update_or_create(fecha=fecha, prenomina=prenomina, defaults={'comentario': nuevo_comentario}, editado=str("E:"+nombre.nombres+" "+nombre.apellidos))
                            if obj.url:  # Verificar si hay un archivo asociado
                                obj.url.delete(save=False)  # Eliminar el archivo asociado

                            # Ahora, si tienes un nuevo archivo (archivo) que deseas asignar a obj.url, puedes hacerlo así:
                            obj.url = archivo
                            obj.save()
                        else:
                            evento_model.objects.update_or_create(fecha=fecha, prenomina=prenomina, defaults={'comentario': nuevo_comentario}, editado=str("E:"+nombre.nombres+" "+nombre.apellidos))
                    else:
                        #  donde nuevo_estado no tiene un mapeo en el diccionario
                        print(f"Error: nuevo_estado desconocido - {nuevo_estado}")

            messages.success(request, 'Cambios guardados exitosamente')
            # redirigir a la misma página para evitar reenvío del formulario al recargar
            return redirect('Prenomina')
        context = {
            'dias_entre_fechas': dias_entre_fechas, #Dias de la catorcena
            'prenomina':prenomina,
            'costo':costo,
            'catorcena_actual':catorcena_actual,
            'fechas_con_etiquetas': fechas_con_etiquetas,
            'autorizacion1':autorizacion1,
            'autorizacion2':autorizacion2,
            'incapacidadesform':incapacidadesform
            
            }

        return render(request, 'prenomina/Actualizar_revisar.html',context)
    else:
        return render(request, 'revisar/403.html')

#@login_required(login_url='user-login')
def determinar_estado_general(ultima_autorizacion):
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
def calcular_aguinaldo(request,salario,prenomina):
    
    if prenomina.empleado.status.fecha_planta is None and prenomina.empleado.status.fecha_planta_anterior is None:
        fecha = None
    elif prenomina.empleado.status.fecha_planta is not None and prenomina.empleado.status.fecha_planta_anterior is not None:
        fecha = prenomina.empleado.status.fecha_planta_anterior
    elif prenomina.empleado.status.fecha_planta:
        fecha = prenomina.empleado.status.fecha_planta
    elif prenomina.empleado.status.fecha_planta_anterior:
        fecha = prenomina.empleado.status.fecha_planta_anterior
        
    if fecha is not None:
        antiguedad = relativedelta(datetime.date.today(),fecha)
        if antiguedad.years > 1:
            dias = Decimal((365) * 15 / 365)
            aguinaldo = Decimal(dias * salario)
            print("aguinaldo completo")
            print(aguinaldo)
            return aguinaldo
        else:
            dias_laborados = antiguedad.days + antiguedad.months * 30            
            dias = Decimal((dias_laborados * 15)/365)
            print("aguinaldo proporcional ")
            aguinaldo = Decimal( dias * salario)
            print(aguinaldo)
            return aguinaldo
        
@login_required(login_url='user-login')
def calcular_prima_dominical(request,dia_extra,salario):
    dato = SalarioDatos.objects.get()
    prima_dominical = salario * Decimal(dato.prima_vacacional)
    prima_dominical = prima_dominical * dia_extra
    print("salario", salario)
    print("prima dominical", Decimal(prima_dominical))
    return Decimal(prima_dominical)

@login_required(login_url='user-login')
def calcular_cuotas_imss(request,sdi_imss):
    variables_patronal = Variables_imss_patronal.objects.get()
    salario_datos = SalarioDatos.objects.get()
    
    #multiplica el sdi * el % de cuatoas / el numero de dias de la catorcena
    invalidez_vida = sdi_imss * Decimal(variables_patronal.iv_obrero / 100) * 14
    cesantia_vejez = sdi_imss * Decimal(variables_patronal.cav_patron/100) * 14
    
    #obtener el salario cotizacion mensual
    salario_cot_men = sdi_imss * Decimal(30.4)
    gastos_medicos = sdi_imss * Decimal(variables_patronal.gmp_obrero/100) * 14
    en_dinero = sdi_imss * Decimal(variables_patronal.pd_obrero/100) * 14 
    
    #calcular cuota fija por cada trabajador hasta por 3 UMAs
    cuota_fija_umas = salario_datos.UMA * Decimal(30.4) * 3
    diferencia_sbc_umas = salario_cot_men - cuota_fija_umas
    cuota_fija = (diferencia_sbc_umas * Decimal(variables_patronal.cf_obrero / 100) / Decimal(30.4)) * 14
    enfermedades_maternidad = gastos_medicos + en_dinero + cuota_fija
    
    #La suma del calculo de cada resultado    
    calculo_imss = invalidez_vida + cesantia_vejez + enfermedades_maternidad
    print("Este es el calculo IMSS: ", calculo_imss)
    return calculo_imss

@login_required(login_url='user-login')
def calcular_isr(request,salario,prima_dominical_isr,calulo_aguinaldo_isr):   
    salario_datos = SalarioDatos.objects.get()
    
    #Salario minino queda exento
    if salario > salario_datos.Salario_minimo:
        #PRIMA DOMINICAL
        if prima_dominical_isr < salario_datos.UMA:
            #exento
            prima_dominical_isr = 0
        else:
            #gravable
            prima_dominical_isr = prima_dominical_isr - Decimal(salario_datos.UMA)

        #AGUINALDO
        if calulo_aguinaldo_isr < (salario_datos.UMA * 30):
            calulo_aguinaldo_isr = 0
        else:
            calulo_aguinaldo_isr - Decimal(salario_datos.UMA * 30)
    else:
        #exento
        prima_dominical_isr = 0
        calulo_aguinaldo_isr = 0
        
    print("esta es la parte gravable o exenta", prima_dominical_isr)
    
    #multiplicar el salario por 30.4
    salario_catorcenal = (salario * Decimal(salario_datos.dias_mes) + prima_dominical_isr) #30.4
        
    #llamar la tabla de IRS
    tabla_irs = DatosISR.objects.all()
    
    #obtener el valor aproximado hacia abajo para obtener las variables
    for datos_irs in tabla_irs:
        if salario_catorcenal >= datos_irs.liminf:
            limite_inferior = datos_irs.liminf
            porcentaje = datos_irs.excedente
            cuota_fija = datos_irs.cuota
            
    #realizar el calculo
    isr_mensual = ((salario_catorcenal - limite_inferior) * porcentaje) + cuota_fija
    
    isr_catorcenal = (isr_mensual / salario_datos.dias_mes) * 14
    
    print("calculo ISR: ", isr_mensual)
    
    return isr_catorcenal

@login_required(login_url='user-login')
def calcular_prima_vacacional(request,salario,prenomina):
    
    tabla_vacaciones = TablaVacaciones.objects.all()
    dato = SalarioDatos.objects.get()
    
    fecha_actual = datetime.date.today()
       
    calcular_prima = True
    if prenomina.empleado.status.tipo_de_contrato_id == 4: #HONORARIOS
        calcular_prima = False
    elif prenomina.empleado.status.tipo_de_contrato_id == 2: #EVENTUAL
        fecha = fecha_actual - timedelta(days=365) # El calculo es 12 dias de vacaciones, siempre para contrato eventual
    elif prenomina.empleado.status.tipo_de_contrato_id == 7: #NR
        calcular_prima = False
    elif prenomina.empleado.status.fecha_planta is None and prenomina.empleado.status.fecha_planta_anterior is None:
        calcular_prima = False
    elif prenomina.empleado.status.fecha_planta is not None and prenomina.empleado.status.fecha_planta_anterior is not None:
        fecha = prenomina.empleado.status.fecha_planta_anterior
    elif prenomina.empleado.status.fecha_planta:
        fecha = prenomina.empleado.status.fecha_planta
    elif prenomina.empleado.status.fecha_planta_anterior:
        fecha = prenomina.empleado.status.fecha_planta_anterior

    prima_vacacional = 0
    if calcular_prima == True:#calcula la prima
        calcular_antiguedad = relativedelta(fecha_actual, fecha)
        antiguedad = calcular_antiguedad.years
        print("esta es la antiguedad ", antiguedad)

        if antiguedad > 0:
            for tabla in tabla_vacaciones:
                if antiguedad >= tabla.years:
                    dias_vacaciones = tabla.days #Se asignan los días para el calculo de la prima vacacional

            vac_reforma_actual = Decimal(dias_vacaciones) * Decimal(salario)
            print("dias vacaciones", dias_vacaciones, "salario", salario)
            print("vacaciones", vac_reforma_actual)
            
            prima_vacacional = vac_reforma_actual*Decimal(dato.prima_vacacional)
            print("esta es la prima ", prima_vacacional)
            return prima_vacacional

        else:#No calcula la prima - No tiene el año de antiguedad o más
            print("esta es la prima ", prima_vacacional)
            return prima_vacacional

    else:#No calcula la prima
        print("esta es la prima ", prima_vacacional)
        return prima_vacacional 
        
    
    
@login_required(login_url='user-login')
def Excel_estado_prenomina(request,prenominas, user_filter):
    from datetime import datetime
    
    response= HttpResponse(content_type = "application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename = Reporte_prenominas_' + str(datetime.now())+'.xlsx'
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
    body_style.font = Font(name ='Calibri', size = 11)
    wb.add_named_style(body_style)
    #Create messages style and adding to workbook
    messages_style = NamedStyle(name = "mensajes_style")
    messages_style.font = Font(name="Arial Narrow", size = 11)
    wb.add_named_style(messages_style)
    #Create date style and adding to workbook
    date_style = NamedStyle(name='date_style', number_format='DD/MM/YYYY')
    date_style.font = Font(name ='Calibri', size = 11)
    wb.add_named_style(date_style)
    money_style = NamedStyle(name='money_style', number_format='$ #,##0.00')
    money_style.font = Font(name ='Calibri', size = 11)
    bold_money_style = NamedStyle(name='bold_money_style', number_format='$#,##0.00', font=Font(bold=True))
    wb.add_named_style(money_style)
    money_resumen_style = NamedStyle(name='money_resumen_style', number_format='$ #,##0.00')
    money_resumen_style.font = Font(name ='Calibri', size = 14, bold = True)
    wb.add_named_style(money_resumen_style)
    dato_style = NamedStyle(name='dato_style',number_format='DD/MM/YYYY')
    dato_style.font = Font(name="Arial Narrow", size = 11)
        
    columns = ['Empleado','#Trabajador','Distrito','#Catorcena','Fecha','Estado general','RH','CT','Gerencia','Autorizada','Retardos','Castigos','Permiso con goce sueldo',
               'Permiso sin goce','Descansos','Incapacidades','Faltas','Comisión','Domingo','Dia de descanso laborado','Festivos','Economicos','Vacaciones','Salario Cartocenal',
               'Previsión social', 'Total bonos','Total percepciones','Prestamo infonavit','IMSS','Fonacot','ISR Retenido','Total deducciones','Neto a pagar en nomina']

    for col_num in range(len(columns)):
        (ws.cell(row = row_num, column = col_num+1, value=columns[col_num])).style = head_style
        if col_num == 1:
            ws.column_dimensions[get_column_letter(col_num + 1)].width = 50
        if col_num < 4:
            ws.column_dimensions[get_column_letter(col_num + 1)].width = 30
        if col_num == 4:
            ws.column_dimensions[get_column_letter(col_num + 1)].width = 30
        else:
            ws.column_dimensions[get_column_letter(col_num + 1)].width = 15


    columna_max = len(columns)+2
    
    ahora = datetime.now()
    #ahora = datetime.now() + timedelta(days=10)
    
    catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()

    (ws.cell(column = columna_max, row = 1, value='{Reporte Creado Automáticamente por Savia RH. JH}')).style = messages_style
    (ws.cell(column = columna_max, row = 2, value='{Software desarrollado por Vordcab S.A. de C.V.}')).style = messages_style
    #(ws.cell(column = columna_max, row = 3, value='Algún dato')).style = messages_style
    #(ws.cell(column = columna_max +1, row=3, value = 'alguna sumatoria')).style = money_resumen_style
    (ws.cell(column = columna_max, row = 4, value=f'Catorcena: {catorcena_actual.catorcena}: {catorcena_actual.fecha_inicial.strftime("%d/%m/%Y")} - {catorcena_actual.fecha_final.strftime("%d/%m/%Y")}')).style = dato_style
    ws.column_dimensions[get_column_letter(columna_max)].width = 50
    ws.column_dimensions[get_column_letter(columna_max + 1)].width = 50

    rows = []

    sub_salario_catorcenal_costo = Decimal(0.00) #Valor de referencia del costo
    sub_salario_catorcenal = Decimal(0.00)
    sub_apoyo_pasajes = Decimal(0.00)
    sub_total_bonos = Decimal(0.00)
    sub_total_percepciones = Decimal(0.00)
    sub_prestamo_infonavit = Decimal(0.00)
    sub_calculo_isr = Decimal(0.00)
    sub_calculo_imss = Decimal(0.00)
    sub_prestamo_fonacot = Decimal(0.00)
    sub_total_deducciones = Decimal(0.00)
    sub_pagar_nomina = Decimal(0.00)
        
    for prenomina in prenominas:
                  
        RH = AutorizarPrenomina.objects.filter(prenomina=prenomina, tipo_perfil__nombre="RH").first()
        CT = AutorizarPrenomina.objects.filter(prenomina=prenomina, tipo_perfil__nombre="Control Tecnico").first()
        G = AutorizarPrenomina.objects.filter(prenomina=prenomina, tipo_perfil__nombre="Gerencia").first()

        if G is not None and G.estado.tipo == 'aprobado':
            estado = 'aprobado'
        elif G is not None and G.estado == 'rechazado':
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
        
        #datos para obtener los calculos de la prenomina dependiendo el empleado
        #salario_catorcenal_costo = (prenomina.empleado.status.costo.neto_catorcenal_sin_deducciones)
        
        #salario = Decimal(prenomina.empleado.status.costo.neto_catorcenal_sin_deducciones) / 14
        salario = Decimal(prenomina.empleado.status.costo.sueldo_diario)
        #neto_catorcenal =  prenomina.empleado.status.costo.neto_catorcenal_sin_deducciones
        apoyo_pasajes = prenomina.empleado.status.costo.apoyo_de_pasajes
        infonavit = prenomina.empleado.status.costo.amortizacion_infonavit
        fonacot = prenomina.empleado.status.costo.fonacot 
        sdi_imss = prenomina.empleado.status.costo.sdi_imss
        
        #imss = prenomina.empleado.status.costo.imms_obrero_patronal
        
        #realiza el calculo de las cuotas imss
        calculo_imss = calcular_cuotas_imss(request,sdi_imss)
        
        #realiza el calculo del ISR
        #calculo_isr = calcular_isr(request,salario)
        
        #realiza el calculo de la prima vacacional
        calulo_prima_vacacional = calcular_prima_vacacional(request,salario,prenomina)
        
        #Fecha para obtener los bonos agregando la hora y la fecha de acuerdo a la catorcena
        fecha_inicial = datetime.combine(catorcena_actual.fecha_inicial, datetime.min.time()) + timedelta(hours=00, minutes=00,seconds=00)
        fecha_final = datetime.combine(catorcena_actual.fecha_final, datetime.min.time()) + timedelta(hours=23, minutes=59,seconds=59)
        
        total_bonos = BonoSolicitado.objects.filter(
            trabajador_id=prenomina.empleado.status.perfil.id,
            solicitud__fecha_autorizacion__isnull=False,
            solicitud__fecha_autorizacion__range=(fecha_inicial, fecha_final)
        ).aggregate(total=Sum('cantidad'))['total'] or 0
           
        #calculo del infonavit
        if infonavit == 0:
            prestamo_infonavit = Decimal(0.00)
        else:
            prestamo_infonavit = Decimal((infonavit / Decimal(30.4) ) * 14 )
                                        
        #calculo del fonacot
        if fonacot == 0:
            prestamo_fonacot = Decimal(0.00)
        else:
            #Se haya la catorcena actual, y cuenta cuantas catorcenas le corresponden al mes actual
            primer_dia_mes = datetime(datetime.now().year, datetime.now().month, 1).date()
            ultimo_dia_mes = datetime(datetime.now().year, datetime.now().month,
                                    calendar.monthrange(datetime.now().year, datetime.now().month)[1]).date()
            numero_catorcenas =  Catorcenas.objects.filter(fecha_final__range=(primer_dia_mes,ultimo_dia_mes)).count()
            prestamo_fonacot = prestamo_fonacot / numero_catorcenas
            
            
        print("infonavit", prestamo_infonavit)
        print("fonacot", prestamo_fonacot)
        #print("ISR", calculo_isr)
        print("IMSS", calculo_imss)
        
        print(prenomina.empleado)
        print("salario: ",salario)
        
        #contar no. de incidencias 
        retardos = prenomina.retardos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        #castigos = prenomina.castigos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        #castigos = prenomina.castigos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
        castigos = Castigos.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        #permiso_goce = prenomina.permiso_goce_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        #permiso_goce = Permiso_goce.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        #permiso_goce = Permiso_goce.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        permiso_goce = Permiso_goce.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        #permiso_sin = prenomina.permiso_sin_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        permiso_sin = Permiso_sin.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        descanso = prenomina.descanso_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        #incapacidades = prenomina.incapacidades_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        #incapacidades = prenomina.incapacidades_set.filter(Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)),Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        incapacidades = Incapacidades.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        
        
        faltas = prenomina.faltas_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        comision = prenomina.comision_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        domingo = prenomina.domingo_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        dia_extra = prenomina.dia_extra_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        festivos = TablaFestivos.objects.filter(dia_festivo__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]).count()
        economicos = Economicos_dia_tomado.objects.filter(prenomina__status=prenomina.empleado.status, fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]).count()
        vacaciones = Vacaciones_dias_tomados.objects.filter(Q(prenomina__status=prenomina.empleado.status, fecha_inicio__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]) | Q(prenomina__status=prenomina.empleado.status, fecha_fin__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])) #Comparar con la fecha final tambien
        
        #calular el numero de permiso con goce de sueldo
        cantidad_dias_castigos = 0
        if permiso_sin.exists():   
            #checar las incapacides de la catorcena
            for goce in permiso_sin:
                goce_fecha = goce.fecha
                goce_fecha_fin = goce.fecha_fin
                
            print("castigo INICIO", goce_fecha, "castigo FIN", goce_fecha_fin)
            
            #se obtiene el numero de catorcenas si esta en otras catorcenas
            catorcenas = Catorcenas.objects.filter(Q(fecha_inicial__range=(goce_fecha, goce_fecha_fin)) |  Q(fecha_final__range=( goce_fecha,  goce_fecha_fin)))
            numero_catorcenas_goce = catorcenas.count()
            print("NUMERO DE CATORCENAS castigos", numero_catorcenas_goce)
            
            if numero_catorcenas_goce > 1:
                print("PERTENECE A MÁS CATORCENAS")    
                #print("INCAPACIDAD INICIO", incapacidad.fecha, "INCAPACIDAD FIN", incapacidad.fecha_fin)
                cat1 = Catorcenas.objects.filter(fecha_inicial__lte=goce.fecha,fecha_final__gte=goce.fecha).first()
                cat2 = Catorcenas.objects.filter(fecha_inicial__lte=goce.fecha_fin,fecha_final__gte=goce.fecha_fin).first()
                
                print("Actual",catorcena_actual)
                
                if cat1.catorcena == catorcena_actual.catorcena:
                    print("Es la cat1 atrasada: ", cat1.catorcena)
                    diferencia = cat1.fecha_final - goce_fecha
                    dias = abs(diferencia.days) + 1
                    #print("dias correspondientes",dias)
                    permiso_sin = dias
                                    
                elif cat2.catorcena == catorcena_actual.catorcena:
                        
                    cat2_diferencia = goce.fecha_fin - cat2.fecha_inicial
                    dias_dos = abs(cat2_diferencia.days) + 1
                    print("dias correspondientes cat 2 Actual",dias_dos)
                    permiso_sin = dias_dos
                                                  
            else:#EL CALCULO LO HACE CORRECTO
                print("AQUI HACE EL BRINCO A LA CATORCENA")
                print("PERTENECE A LA CATORCENA ACTUAL Y CALCULA LOS CASTIGOS")
                for goce in permiso_sin:
                    diferencia = goce.fecha_fin - goce.fecha
                    permiso_sin = diferencia.days + 1
                    
        else: 
            permiso_sin = 0
            print("NO TIENE CASTIGOS: ",castigos)
            
        if permiso_goce.exists():   
            #checar las incapacides de la catorcena
            for goce in permiso_goce:
                goce_fecha = goce.fecha
                goce_fecha_fin = goce.fecha_fin
                
            print("castigo INICIO", goce_fecha, "castigo FIN", goce_fecha_fin)
            
            #se obtiene el numero de catorcenas si esta en otras catorcenas
            catorcenas = Catorcenas.objects.filter(Q(fecha_inicial__range=(goce_fecha, goce_fecha_fin)) |  Q(fecha_final__range=( goce_fecha,  goce_fecha_fin)))
            numero_catorcenas_goce = catorcenas.count()
            print("NUMERO DE CATORCENAS castigos", numero_catorcenas_goce)
            
            if numero_catorcenas_goce > 1:
                print("PERTENECE A MÁS CATORCENAS")    
                #print("INCAPACIDAD INICIO", incapacidad.fecha, "INCAPACIDAD FIN", incapacidad.fecha_fin)
                cat1 = Catorcenas.objects.filter(fecha_inicial__lte=goce.fecha,fecha_final__gte=goce.fecha).first()
                cat2 = Catorcenas.objects.filter(fecha_inicial__lte=goce.fecha_fin,fecha_final__gte=goce.fecha_fin).first()
                
                print("Actual",catorcena_actual)
                
                if cat1.catorcena == catorcena_actual.catorcena:
                    print("Es la cat1 atrasada: ", cat1.catorcena)
                    diferencia = cat1.fecha_final - goce_fecha
                    dias = abs(diferencia.days) + 1
                    #print("dias correspondientes",dias)
                    permiso_goce = dias
                                    
                elif cat2.catorcena == catorcena_actual.catorcena:
                        
                    cat2_diferencia = goce.fecha_fin - cat2.fecha_inicial
                    dias_dos = abs(cat2_diferencia.days) + 1
                    print("dias correspondientes cat 2 Actual",dias_dos)
                    permiso_goce = dias_dos
                                                  
            else:#EL CALCULO LO HACE CORRECTO
                print("AQUI HACE EL BRINCO A LA CATORCENA")
                print("PERTENECE A LA CATORCENA ACTUAL Y CALCULA LOS CASTIGOS")
                for goce in permiso_goce:
                    diferencia = goce.fecha_fin - goce.fecha
                    permiso_goce = diferencia.days + 1
                    
        else: 
            permiso_goce = 0
            print("NO TIENE CASTIGOS: ",castigos)
            
            
        #calular el numero de castigos
        cantidad_dias_castigos = 0
        if castigos.exists():   
            #checar las incapacides de la catorcena
            for castigo in castigos:
                castigo_fecha = castigo.fecha
                castigo_fecha_fin = castigo.fecha_fin
                        
            print("castigo INICIO", castigo_fecha, "castigo FIN", castigo_fecha_fin)
            
            #se obtiene el numero de catorcenas si esta en otras catorcenas
            catorcenas = Catorcenas.objects.filter(Q(fecha_inicial__range=(castigo_fecha, castigo_fecha_fin)) |  Q(fecha_final__range=(castigo_fecha, castigo_fecha_fin)))
            numero_catorcenas_castigos = catorcenas.count()
            print("NUMERO DE CATORCENAS castigos", numero_catorcenas_castigos)
            
            if numero_catorcenas_castigos > 1:
                print("PERTENECE A MÁS CATORCENAS")    
                #print("INCAPACIDAD INICIO", incapacidad.fecha, "INCAPACIDAD FIN", incapacidad.fecha_fin)
                cat1 = Catorcenas.objects.filter(fecha_inicial__lte=castigo.fecha,fecha_final__gte=castigo.fecha).first()
                cat2 = Catorcenas.objects.filter(fecha_inicial__lte=castigo.fecha_fin,fecha_final__gte=castigo.fecha_fin).first()
                
                print("Actual",catorcena_actual)
                
                if cat1.catorcena == catorcena_actual.catorcena:
                    print("Es la cat1 atrasada: ", cat1.catorcena)
                    diferencia = cat1.fecha_final - castigo_fecha
                    dias = abs(diferencia.days) + 1
                    #print("dias correspondientes",dias)
                    castigos = dias
                                    
                elif cat2.catorcena == catorcena_actual.catorcena:
                        
                    cat2_diferencia = castigo.fecha_fin - cat2.fecha_inicial
                    dias_dos = abs(cat2_diferencia.days) + 1
                    print("dias correspondientes cat 2 Actual",dias_dos)
                    castigos = dias_dos
                                                  
            else:#EL CALCULO LO HACE CORRECTO
                print("AQUI HACE EL BRINCO A LA CATORCENA")
                print("PERTENECE A LA CATORCENA ACTUAL Y CALCULA LOS CASTIGOS")
                for castigo in castigos:
                    diferencia = castigo.fecha_fin - castigo.fecha
                    castigos = diferencia.days + 1
                    
        else: 
            castigos = 0
            print("NO TIENE CASTIGOS: ",castigos)
                
        #calular el numero de incapacidades    
        cantidad_dias_incapacides = 0
        incidencias_incapacidades_pasajes = 0
        incidencias_incapacidades = 0
        incapacidades_anterior = 0
        incapacidades_actual = 0
        if incapacidades.exists():   
            #checar las incapacides de la catorcena
            for incapacidad in incapacidades:
                incapacidad_fecha = incapacidad.fecha
                incapacidad_fecha_fin = incapacidad.fecha_fin
            #status y por la fecha, 
            #si se quieren traer las incapacidades que estan en boolean = True, False no se pagan, 
            #en la parte de las incidencias en la primera incapacidad boolean = True 
            #si se hace otra incapacidad se detecta que es la continuacion de una que se paga, esta sera False
                        
            print("INCAPACIDAD INICIO", incapacidad_fecha, "INCAPACIDAD FIN", incapacidad_fecha_fin)
            
            #se obtiene el numero de catorcenas si esta en otras catorcenas
            catorcenas = Catorcenas.objects.filter(Q(fecha_inicial__range=(incapacidad_fecha, incapacidad_fecha_fin)) |  Q(fecha_final__range=(incapacidad_fecha, incapacidad_fecha_fin)))
            numero_catorcenas_incapacidades = catorcenas.count()
            print("NUMERO DE CATORCENAS INCAPACIDADES", numero_catorcenas_incapacidades)
            
            #Pertenece a mas de una catorcena
            if numero_catorcenas_incapacidades > 1:
                print("PERTENECE A MÁS CATORCENAS")    
                #print("INCAPACIDAD INICIO", incapacidad.fecha, "INCAPACIDAD FIN", incapacidad.fecha_fin)
                cat1 = Catorcenas.objects.filter(fecha_inicial__lte=incapacidad.fecha,fecha_final__gte=incapacidad.fecha).first()
                cat2 = Catorcenas.objects.filter(fecha_inicial__lte=incapacidad.fecha_fin,fecha_final__gte=incapacidad.fecha_fin).first()
                
                print("Actual",catorcena_actual)
                
                if cat1.catorcena == catorcena_actual.catorcena:
                    print("Es la cat1 atrasada: ", cat1.catorcena)
                    diferencia = cat1.fecha_final - incapacidad_fecha
                    dias = abs(diferencia.days) + 1
                    #print("dias correspondientes",dias)
                    incapacidades = dias
                    
                    #realiza el calculo de la incapacidad
                    if incapacidades > 0:
                        incidencias_incapacidades_pasajes = incapacidades
                        if incapacidades > 3:
                            incidencias_incapacidades = incidencias_incapacidades + (incapacidades - 3) #3 dias se pagan
                            print("ESTAS SON LAS INCIDENCAS INCAPACIDADES", incidencias_incapacidades)
                    
                    incapacidades_anterior = 0
                    incapacidades_actual = incapacidades
                    
                elif cat2.catorcena == catorcena_actual.catorcena:
                    print("Es la cat2 actual: ", cat2.catorcena)
                
                    cat1_diferencia = cat1.fecha_final - incapacidad.fecha
                    dias_uno = abs(cat1_diferencia.days) + 1
                    print("dias correspondientes cat 1 Atrasada",dias_uno)
                    
                    cat2_diferencia = incapacidad.fecha_fin - cat2.fecha_inicial
                    dias_dos = abs(cat2_diferencia.days) + 1
                    print("dias correspondientes cat 2 Actual",dias_dos)
                    
                    incapacidades = dias_uno + dias_dos
                    #incapacidades = dias_dos

                    incapacidades_anterior = dias_uno
                    incapacidades_actual = dias_dos
                
                    #realiza el calculo de la incapacidad
                    if incapacidades > 0:
                        incidencias_incapacidades_pasajes = incapacidades
                        if incapacidades > 3:
                            incidencias_incapacidades = incidencias_incapacidades + (incapacidades - 3) #3 dias se pagan
                            print("ESTAS SON LAS INCIDENCAS INCAPACIDADES", incidencias_incapacidades)
                                                  
            else:#Pertenece a solo una catorcena
                print("PERTENECE A LA CATORCENA ACTUAL Y CALCULA LAS INCAPACIDADES")
                cont = 0
                for incapacidad in incapacidades:
                    print(incapacidad.fecha, incapacidad.fecha_fin)
                    diferencia = (incapacidad.fecha_fin - incapacidad.fecha).days + 1
                    cont += diferencia  # Acumulando los días de cada incapacidad
                    incapacidades = cont
                    print("incapacidades por iteracion ", incapacidades)
                    
                    if incapacidades > 0:
                        incidencias_incapacidades_pasajes = incapacidades
                    if incapacidades > 3:
                        incidencias_incapacidades = incidencias_incapacidades + (incapacidades - 3) #3 dias se pagan
                        print("ESTAS SON LAS INCIDENCAS INCAPACIDADES", incidencias_incapacidades)
                
                    incapacidades_anterior = 0
                    incapacidades_actual = incapacidades
                    
                    

                    
                print("aqui deberian de arrogar las 6 incapacidades: ", incapacidades)
                    
                #realiza el calculo de la incapacidad
                """
                if incapacidades > 0:
                    incidencias_incapacidades_pasajes = incapacidades
                    if incapacidades > 3:
                        incidencias_incapacidades = incidencias_incapacidades + (incapacidades - 3) #3 dias se pagan
                        print("ESTAS SON LAS INCIDENCAS INCAPACIDADES", incidencias_incapacidades)
                
                incapacidades_anterior = 0
                incapacidades_actual = incapacidades
                """
                
        else: 
            incapacidades = 0
            print("NO TIENE INCAPACIDADES: ",incapacidades)
                
        #calcular el numero de vacaciones
        cantidad_dias_vacacion = 0
        if vacaciones.exists():
            for vacacion in vacaciones:
                diferencia = vacacion.fecha_fin - vacacion.fecha_inicio
                cantidad_dias_vacacion = diferencia.days + 1        
        print("total vacaciones: ", cantidad_dias_vacacion)
        
        #calculo de la prima se manda a llamar
        if cantidad_dias_vacacion > 0:
            calcular_prima_vacacional(cantidad_dias_vacacion)
            
        
        #numero de catorena
        catorcena_num = catorcena_actual.catorcena 
        
        incidencias = 0
        incidencias_retardos = 0
        
        if faltas > 0:
            incidencias = incidencias + faltas
            print("Faltas: ", faltas)
            
        if retardos > 0:
            incidencias_retardos = retardos // 3 #3 retardos se decuenta 1 dia
            
        if castigos > 0:
            incidencias = incidencias + castigos
            print("Castigos incidencias contadas", castigos)
        
        if permiso_sin > 0:
            incidencias = incidencias + permiso_sin
            
        prima_dominical = 0
        pago_doble = 0  
        if dia_extra > 0:
            pago_doble = Decimal(dia_extra * (salario * 2))
            prima_dominical = calcular_prima_dominical(request,dia_extra,salario)
            
        #calcular aguinaldo
        calulo_aguinaldo = calcular_aguinaldo(request,salario,prenomina)
        
        #incapacidad = str("")   
        #realiza el calculo del ISR
        calculo_isr = calcular_isr(request,salario,prima_dominical,calulo_aguinaldo)
            
        #calculo de la prenomina - regla de tres   
        dias_de_pago = 12
        print("incidencias", incidencias, "incidencias_retarods", incidencias_retardos, "incidencias_inca", incidencias_incapacidades)
        dias_laborados = dias_de_pago - (incidencias + incidencias_retardos + incidencias_incapacidades)
        proporcion_septimos_dias = Decimal((dias_laborados * 2) / 12)
        proporcion_laborados = proporcion_septimos_dias + dias_laborados
        salario_catorcenal = (proporcion_laborados * salario) + pago_doble
        
        print("las incidencias incapacidades", incidencias_incapacidades)
        if incidencias_incapacidades_pasajes > 0:
            apoyo_pasajes = (apoyo_pasajes / 12 * (12 - (incidencias + incidencias_incapacidades_pasajes))) #12 son los dias trabajados
            print("Aqui es donde se ejecuta el codigo")
        else:
            apoyo_pasajes = (apoyo_pasajes / 12 * (12 - (incidencias))) #12 son los dias trabajados
            print("Aqui no se deberia ejecutar el codigo")
        
        print("apoyos pasajes: ", apoyo_pasajes)
        print("total: ", salario_catorcenal)
        print("pagar nomina: ", apoyo_pasajes + salario_catorcenal)
        print("DEBE TENER PRIMA DOMINICAL: ", prima_dominical)
        total_percepciones = salario_catorcenal + apoyo_pasajes + total_bonos + prima_dominical
        #¿aqui deberia ir el IMSS y el ISR en total deducciones?
        total_deducciones = prestamo_infonavit + prestamo_fonacot + calculo_isr + calculo_imss
        pagar_nomina = (total_percepciones - total_deducciones)
        
        if retardos == 0: 
            retardos = ''
        
        if castigos == 0:
            castigos = ''
            
        if permiso_goce == 0:
            permiso_goce = ''
            
        if permiso_sin == 0:
            permiso_sin = ''
            
        if descanso == 0:
            descanso = ''

        if dia_extra == 0:
            dia_extra = ''
                    
        if incapacidades == 0:
            incapacidades = ''
        
        if faltas == 0:
            faltas = ''
        
        if comision == 0:
            comision = ''
            
        if domingo == 0:
            domingo = ''
            
        if festivos == 0:
            festivos = ''
            
        if economicos == 0:
            economicos = ''
            
        if cantidad_dias_vacacion == 0:
            cantidad_dias_vacacion = ''
            
        
            
        
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
            str("Días anteriores: ")+str(incapacidades_anterior)+str(" Días actual: ")+str(incapacidades_actual),
            faltas,
            comision,
            domingo,
            dia_extra,
            festivos,
            economicos,
            cantidad_dias_vacacion,
            salario_catorcenal,
            apoyo_pasajes,
            total_bonos,
            total_percepciones,
            prestamo_infonavit,
            calculo_imss,
            prestamo_fonacot,
            calculo_isr,
            #
            #
            total_deducciones,
            pagar_nomina,
        )
        rows.append(row)
        
        #sub_salario_catorcenal_costo = sub_salario_catorcenal_costo + salario_catorcenal_costo
        sub_salario_catorcenal = sub_salario_catorcenal + salario_catorcenal
        sub_apoyo_pasajes = sub_apoyo_pasajes + apoyo_pasajes
        sub_total_bonos = sub_total_bonos + total_bonos
        sub_total_percepciones = sub_total_percepciones + total_percepciones
        sub_prestamo_infonavit = sub_prestamo_infonavit + prestamo_infonavit
        sub_calculo_imss = sub_calculo_imss + calculo_imss
        sub_prestamo_fonacot = sub_prestamo_fonacot + prestamo_fonacot
        sub_calculo_isr = sub_calculo_isr + calculo_isr
        sub_total_deducciones = sub_total_deducciones + total_deducciones
        sub_pagar_nomina = sub_pagar_nomina + pagar_nomina
        
        
                 
    # Ahora puedes usar la lista rows como lo estás haciendo actualmente en tu código
    for row_num, row in enumerate(rows, start=2):
        for col_num, value in enumerate(row, start=1):
            if col_num < 4:
                ws.cell(row=row_num, column=col_num, value=value).style = body_style
            elif col_num == 5:
                ws.cell(row=row_num, column=col_num, value=value).style = date_style
            elif col_num > 5 and col_num < 24:
                ws.cell(row=row_num, column=col_num, value=value).style = body_style
            elif col_num >= 24:
                ws.cell(row=row_num, column=col_num, value=value).style = money_style
            else:
                ws.cell(row=row_num, column=col_num, value=value).style = body_style

    #sumar las columnas
    
    #print("Salario neto cartocelnal", salario_catorcenal)
    #sub_salario_catorcenal = sub_salario_catorcenal + salario_catorcenal
    #print("subtotal catorcenal",sub_salario_catorcenal)
    #sub_apoyo_pasajes = Decimal(sub_apoyo_pasajes) + apoyo_pasajes
    #sub_total_bonos = sub_total_bonos + total_bonos
    #sub_total_percepciones = sub_total_percepciones + total_percepciones
    #sub_prestamo_infonavit = sub_prestamo_infonavit + prestamo_infonavit
    #sub_prestamo_fonacot = sub_prestamo_fonacot + prestamo_fonacot
    #sub_total_deducciones = sub_total_deducciones + total_deducciones
    #sub_pagar_nomina = sub_pagar_nomina + pagar_nomina
    
    
    add_last_row = ['Total','','','','','','','','','','','','','','','','','','','','','','',
                    #sub_salario_catorcenal_costo,
                    sub_salario_catorcenal,
                    sub_apoyo_pasajes,
                    sub_total_bonos,
                    sub_total_percepciones,
                    sub_prestamo_infonavit,
                    sub_calculo_imss,
                    sub_prestamo_fonacot,
                    sub_calculo_isr,
                    sub_total_deducciones,
                    sub_pagar_nomina
                    ]
    ws.append(add_last_row) 
    
    # Aplicar el estilo money_style a cada celda de la fila
    for row in ws.iter_rows(min_row=ws.max_row, max_row=ws.max_row):
        for cell in row:
            cell.style = bold_money_style

    
    #referencia_celda = f'{"x"}{"24"}'
    #celda = ws[referencia_celda]
    #celda.value = 'Laravel'
    
    sheet = wb['Sheet']
    wb.remove(sheet)
    wb.save(response)

    return(response)

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

#@login_required(login_url='user-login')
def Excel_estado_prenomina_formato(prenominas, user_filter):
    from datetime import datetime
    
    response= HttpResponse(content_type = "application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename = Reporte_prenomina_días_' + str(datetime.now())+'.xlsx'
    wb = Workbook()
    ws = wb.create_sheet(title='Reporte')
    #Comenzar en la fila 1
    row_num = 3

    #Create heading style and adding to workbook | Crear el estilo del encabezado y agregarlo al Workbook
    head_style = NamedStyle(name = "head_style")
    head_style.font = Font(name = 'Arial', color = '00FFFFFF', bold = True, size = 11)
    head_style.fill = PatternFill("solid", fgColor = '00003366')
    wb.add_named_style(head_style)
    #Create body style and adding to workbook
    body_style = NamedStyle(name = "body_style")
    body_style.font = Font(name ='Calibri', size = 11)
    wb.add_named_style(body_style)
    #Create messages style and adding to workbook
    messages_style = NamedStyle(name = "mensajes_style")
    messages_style.font = Font(name="Arial Narrow", size = 11)
    wb.add_named_style(messages_style)
    #Create date style and adding to workbook
    date_style = NamedStyle(name='date_style', number_format='DD/MM/YYYY')
    date_style.font = Font(name ='Calibri', size = 11)
    wb.add_named_style(date_style)
    money_style = NamedStyle(name='money_style', number_format='$ #,##0.00')
    money_style.font = Font(name ='Calibri', size = 11)
    bold_money_style = NamedStyle(name='bold_money_style', number_format='$#,##0.00', font=Font(bold=True))
    wb.add_named_style(money_style)
    money_resumen_style = NamedStyle(name='money_resumen_style', number_format='$ #,##0.00')
    money_resumen_style.font = Font(name ='Calibri', size = 14, bold = True)
    wb.add_named_style(money_resumen_style)
    dato_style = NamedStyle(name='dato_style',number_format='DD/MM/YYYY')
    dato_style.font = Font(name="Arial Narrow", size = 11)
    ahora = datetime.now()
    #ahora = datetime.now() + timedelta(days=10)
    # todas las fechas de la catorcena actual
    catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
    delta = catorcena_actual.fecha_final - catorcena_actual.fecha_inicial
    dias_entre_fechas = [catorcena_actual.fecha_inicial + timedelta(days=i) for i in range(delta.days + 1)]
    # Generar los nombres de las columnas de los días
    dias_columnas = [str(fecha.day) for fecha in dias_entre_fechas]
        
    columns = ['No.','NOMBRE DE EMPLEADO','PUESTO','PROYECTO','SUBPROYECTO'] + dias_columnas + ['Salario Catorcenal','Salario Catorcenal',
               'Previsión social', 'Total bonos','Total percepciones','Prestamo infonavit','Fonacot','Total deducciones','Neto a pagar en nomina','Salario','Salario Domingo',]
    
    for col_num in range(len(columns)):
        (ws.cell(row = row_num, column = col_num+1, value=columns[col_num])).style = head_style
        if col_num == 1:
            ws.column_dimensions[get_column_letter(col_num + 1)].width = 50
        if col_num < 4:
            ws.column_dimensions[get_column_letter(col_num + 1)].width = 30
        if col_num == 4:
            ws.column_dimensions[get_column_letter(col_num + 1)].width = 30
        else:
            ws.column_dimensions[get_column_letter(col_num + 1)].width = 15


    columna_max = len(columns)+2
    
    ahora = datetime.now()
    #ahora = datetime.now() + timedelta(days=10)
    
    catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
    (ws.cell(column = 1, row = 1, value='Reporte Prenomina SAVIA RH')).style = messages_style
    (ws.cell(column = 1, row = 2, value=f'Catorcena: {catorcena_actual.catorcena}: {catorcena_actual.fecha_inicial.strftime("%d/%m/%Y")} - {catorcena_actual.fecha_final.strftime("%d/%m/%Y")}')).style = dato_style
    ws.column_dimensions[get_column_letter(columna_max)].width = 50
    ws.column_dimensions[get_column_letter(columna_max + 1)].width = 50

    rows = []

    sub_salario_catorcenal_costo = Decimal(0.00) #Valor de referencia del costo
    sub_salario_catorcenal = Decimal(0.00)
    sub_apoyo_pasajes = Decimal(0.00)
    sub_total_bonos = Decimal(0.00)
    sub_total_percepciones = Decimal(0.00)
    sub_prestamo_infonavit = Decimal(0.00)
    sub_prestamo_fonacot = Decimal(0.00)
    sub_total_deducciones = Decimal(0.00)
    sub_pagar_nomina = Decimal(0.00)
        
    for prenomina in prenominas:
        #datos para obtener los calculos de la prenomina dependiendo el empleado
        salario_catorcenal_costo = (prenomina.empleado.status.costo.neto_catorcenal_sin_deducciones)
        
        salario = Decimal(prenomina.empleado.status.costo.neto_catorcenal_sin_deducciones) / 14
        neto_catorcenal =  prenomina.empleado.status.costo.neto_catorcenal_sin_deducciones
        apoyo_pasajes = prenomina.empleado.status.costo.apoyo_de_pasajes
        infonavit = prenomina.empleado.status.costo.amortizacion_infonavit
        fonacot = prenomina.empleado.status.costo.fonacot 
        
        #Fecha para obtener los bonos agregando la hora y la fecha de acuerdo a la catorcena
        fecha_inicial = datetime.combine(catorcena_actual.fecha_inicial, datetime.min.time()) + timedelta(hours=00, minutes=00,seconds=00)
        fecha_final = datetime.combine(catorcena_actual.fecha_final, datetime.min.time()) + timedelta(hours=23, minutes=59,seconds=59)
        
        total_bonos = BonoSolicitado.objects.filter(
            trabajador_id=prenomina.empleado.status.perfil.id,
            solicitud__fecha_autorizacion__isnull=False,
            solicitud__fecha_autorizacion__range=(fecha_inicial, fecha_final)
        ).aggregate(total=Sum('cantidad'))['total'] or 0

        print("Total Bonos:", total_bonos)
           
        #calculo del infonavit
        if infonavit == 0:
            prestamo_infonavit = Decimal(0.00)
        else:
            prestamo_infonavit = Decimal((infonavit / Decimal(30.4) ) * 14 )
       
        #calculo del fonacot
        if fonacot == 0:
            prestamo_fonacot = Decimal(0.00)
        else:
            #Se haya la catorcena actual, y cuenta cuantas catorcenas le corresponden al mes actual
            primer_dia_mes = datetime(datetime.now().year, datetime.now().month, 1).date()
            ultimo_dia_mes = datetime(datetime.now().year, datetime.now().month,
                                    calendar.monthrange(datetime.now().year, datetime.now().month)[1]).date()
            numero_catorcenas =  Catorcenas.objects.filter(fecha_final__range=(primer_dia_mes,ultimo_dia_mes)).count()
            prestamo_fonacot = prestamo_fonacot / numero_catorcenas
            
        
        #contar no. de incidencias 
        retardos = prenomina.retardos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        #castigos = prenomina.castigos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        #castigos = prenomina.castigos_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
        castigos = Castigos.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        #permiso_goce = prenomina.permiso_goce_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        #permiso_goce = Permiso_goce.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        #permiso_goce = Permiso_goce.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        permiso_goce = Permiso_goce.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        #permiso_sin = prenomina.permiso_sin_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        permiso_sin = Permiso_sin.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        descanso = prenomina.descanso_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        #incapacidades = prenomina.incapacidades_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        #incapacidades = prenomina.incapacidades_set.filter(Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)),Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        incapacidades = Incapacidades.objects.filter(Q(prenomina__empleado_id=prenomina.empleado.id),Q(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)) | Q(fecha_fin__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)))
        faltas = prenomina.faltas_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        comision = prenomina.comision_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        domingo = prenomina.domingo_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        dia_extra = prenomina.dia_extra_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final)).count()
        festivos = TablaFestivos.objects.filter(dia_festivo__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]).count()
        economicos = Economicos_dia_tomado.objects.filter(prenomina__status=prenomina.empleado.status, fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]).count()
        vacaciones = Vacaciones_dias_tomados.objects.filter(Q(prenomina__status=prenomina.empleado.status, fecha_inicio__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]) | Q(prenomina__status=prenomina.empleado.status, fecha_fin__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])) #Comparar con la fecha final tambien
        
        
        
        
        
        
        
        
        
        #calular el numero de permiso con goce de sueldo
        cantidad_dias_castigos = 0
        if permiso_sin.exists():   
            #checar las incapacides de la catorcena
            for goce in permiso_sin:
                goce_fecha = goce.fecha
                goce_fecha_fin = goce.fecha_fin
                
            print("castigo INICIO", goce_fecha, "castigo FIN", goce_fecha_fin)
            
            #se obtiene el numero de catorcenas si esta en otras catorcenas
            catorcenas = Catorcenas.objects.filter(Q(fecha_inicial__range=(goce_fecha, goce_fecha_fin)) |  Q(fecha_final__range=( goce_fecha,  goce_fecha_fin)))
            numero_catorcenas_goce = catorcenas.count()
            print("NUMERO DE CATORCENAS castigos", numero_catorcenas_goce)
            
            if numero_catorcenas_goce > 1:
                print("PERTENECE A MÁS CATORCENAS")    
                #print("INCAPACIDAD INICIO", incapacidad.fecha, "INCAPACIDAD FIN", incapacidad.fecha_fin)
                cat1 = Catorcenas.objects.filter(fecha_inicial__lte=goce.fecha,fecha_final__gte=goce.fecha).first()
                cat2 = Catorcenas.objects.filter(fecha_inicial__lte=goce.fecha_fin,fecha_final__gte=goce.fecha_fin).first()
                
                print("Actual",catorcena_actual)
                
                if cat1.catorcena == catorcena_actual.catorcena:
                    print("Es la cat1 atrasada: ", cat1.catorcena)
                    diferencia = cat1.fecha_final - goce_fecha
                    dias = abs(diferencia.days) + 1
                    #print("dias correspondientes",dias)
                    permiso_sin = dias
                                    
                elif cat2.catorcena == catorcena_actual.catorcena:
                        
                    cat2_diferencia = goce.fecha_fin - cat2.fecha_inicial
                    dias_dos = abs(cat2_diferencia.days) + 1
                    print("dias correspondientes cat 2 Actual",dias_dos)
                    permiso_sin = dias_dos
                                                  
            else:#EL CALCULO LO HACE CORRECTO
                print("AQUI HACE EL BRINCO A LA CATORCENA")
                print("PERTENECE A LA CATORCENA ACTUAL Y CALCULA LOS CASTIGOS")
                for goce in permiso_sin:
                    diferencia = goce.fecha_fin - goce.fecha
                    permiso_sin = diferencia.days + 1
                    
        else: 
            permiso_sin = 0
            print("NO TIENE CASTIGOS: ",castigos)
        
        """
        if permiso_sin.exists():
            for goce in permiso_sin:
                diferencia = goce.fecha_fin - goce.fecha
                permiso_sin = diferencia.days + 1
        else:
            permiso_sin = 0
        """
        
        #calular el numero de permiso con goce de sueldo
        cantidad_dias_castigos = 0
        """
        if permiso_goce.exists():
            for goce in permiso_goce:
                diferencia = goce.fecha_fin - goce.fecha
                permiso_goce = diferencia.days + 1
        else:
            permiso_goce = 0
        """
        if permiso_goce.exists():   
            #checar las incapacides de la catorcena
            for goce in permiso_goce:
                goce_fecha = goce.fecha
                goce_fecha_fin = goce.fecha_fin
                
            print("castigo INICIO", goce_fecha, "castigo FIN", goce_fecha_fin)
            
            #se obtiene el numero de catorcenas si esta en otras catorcenas
            catorcenas = Catorcenas.objects.filter(Q(fecha_inicial__range=(goce_fecha, goce_fecha_fin)) |  Q(fecha_final__range=( goce_fecha,  goce_fecha_fin)))
            numero_catorcenas_goce = catorcenas.count()
            print("NUMERO DE CATORCENAS castigos", numero_catorcenas_goce)
            
            if numero_catorcenas_goce > 1:
                print("PERTENECE A MÁS CATORCENAS")    
                #print("INCAPACIDAD INICIO", incapacidad.fecha, "INCAPACIDAD FIN", incapacidad.fecha_fin)
                cat1 = Catorcenas.objects.filter(fecha_inicial__lte=goce.fecha,fecha_final__gte=goce.fecha).first()
                cat2 = Catorcenas.objects.filter(fecha_inicial__lte=goce.fecha_fin,fecha_final__gte=goce.fecha_fin).first()
                
                print("Actual",catorcena_actual)
                
                if cat1.catorcena == catorcena_actual.catorcena:
                    print("Es la cat1 atrasada: ", cat1.catorcena)
                    diferencia = cat1.fecha_final - goce_fecha
                    dias = abs(diferencia.days) + 1
                    #print("dias correspondientes",dias)
                    permiso_goce = dias
                                    
                elif cat2.catorcena == catorcena_actual.catorcena:
                        
                    cat2_diferencia = goce.fecha_fin - cat2.fecha_inicial
                    dias_dos = abs(cat2_diferencia.days) + 1
                    print("dias correspondientes cat 2 Actual",dias_dos)
                    permiso_goce = dias_dos
                                                  
            else:#EL CALCULO LO HACE CORRECTO
                print("AQUI HACE EL BRINCO A LA CATORCENA")
                print("PERTENECE A LA CATORCENA ACTUAL Y CALCULA LOS CASTIGOS")
                for goce in permiso_goce:
                    diferencia = goce.fecha_fin - goce.fecha
                    permiso_goce = diferencia.days + 1
                    
        else: 
            permiso_goce = 0
            print("NO TIENE CASTIGOS: ",castigos)
            
            
        #calular el numero de castigos
        cantidad_dias_castigos = 0
        if castigos.exists():   
            #checar las incapacides de la catorcena
            for castigo in castigos:
                castigo_fecha = castigo.fecha
                castigo_fecha_fin = castigo.fecha_fin
                        
            print("castigo INICIO", castigo_fecha, "castigo FIN", castigo_fecha_fin)
            
            #se obtiene el numero de catorcenas si esta en otras catorcenas
            catorcenas = Catorcenas.objects.filter(Q(fecha_inicial__range=(castigo_fecha, castigo_fecha_fin)) |  Q(fecha_final__range=(castigo_fecha, castigo_fecha_fin)))
            numero_catorcenas_castigos = catorcenas.count()
            print("NUMERO DE CATORCENAS castigos", numero_catorcenas_castigos)
            
            if numero_catorcenas_castigos > 1:
                print("PERTENECE A MÁS CATORCENAS")    
                #print("INCAPACIDAD INICIO", incapacidad.fecha, "INCAPACIDAD FIN", incapacidad.fecha_fin)
                cat1 = Catorcenas.objects.filter(fecha_inicial__lte=castigo.fecha,fecha_final__gte=castigo.fecha).first()
                cat2 = Catorcenas.objects.filter(fecha_inicial__lte=castigo.fecha_fin,fecha_final__gte=castigo.fecha_fin).first()
                
                print("Actual",catorcena_actual)
                
                if cat1.catorcena == catorcena_actual.catorcena:
                    print("Es la cat1 atrasada: ", cat1.catorcena)
                    diferencia = cat1.fecha_final - castigo_fecha
                    dias = abs(diferencia.days) + 1
                    #print("dias correspondientes",dias)
                    castigos = dias
                                    
                elif cat2.catorcena == catorcena_actual.catorcena:
                        
                    cat2_diferencia = castigo.fecha_fin - cat2.fecha_inicial
                    dias_dos = abs(cat2_diferencia.days) + 1
                    print("dias correspondientes cat 2 Actual",dias_dos)
                    castigos = dias_dos
                                                  
            else:#EL CALCULO LO HACE CORRECTO
                print("AQUI HACE EL BRINCO A LA CATORCENA")
                print("PERTENECE A LA CATORCENA ACTUAL Y CALCULA LOS CASTIGOS")
                for castigo in castigos:
                    diferencia = castigo.fecha_fin - castigo.fecha
                    castigos = diferencia.days + 1
                    
        else: 
            castigos = 0
            print("NO TIENE CASTIGOS: ",castigos)
                
        #calular el numero de incapacidades    
        cantidad_dias_incapacides = 0
        incidencias_incapacidades_pasajes = 0
        incidencias_incapacidades = 0
        incapacidades_anterior = 0
        incapacidades_actual = 0
        if incapacidades.exists():   
            
            print("estas son las incapacidades: ", incapacidades)
            
            
            #checar las incapacides de la catorcena
            for incapacidad in incapacidades:
                incapacidad_fecha = incapacidad.fecha
                incapacidad_fecha_fin = incapacidad.fecha_fin
            #status y por la fecha, 
            #si se quieren traer las incapacidades que estan en boolean = True, False no se pagan, 
            #en la parte de las incidencias en la primera incapacidad boolean = True 
            #si se hace otra incapacidad se detecta que es la continuacion de una que se paga, esta sera False
                        
            print("INCAPACIDAD INICIO", incapacidad_fecha, "INCAPACIDAD FIN", incapacidad_fecha_fin)
            
            #se obtiene el numero de catorcenas si esta en otras catorcenas
            catorcenas = Catorcenas.objects.filter(Q(fecha_inicial__range=(incapacidad_fecha, incapacidad_fecha_fin)) |  Q(fecha_final__range=(incapacidad_fecha, incapacidad_fecha_fin)))
            numero_catorcenas_incapacidades = catorcenas.count()
            print("NUMERO DE CATORCENAS INCAPACIDADES", numero_catorcenas_incapacidades)
            
            #Pertenece a mas de una catorcena
            if numero_catorcenas_incapacidades > 1:
                print("PERTENECE A MÁS CATORCENAS")    
                #print("INCAPACIDAD INICIO", incapacidad.fecha, "INCAPACIDAD FIN", incapacidad.fecha_fin)
                cat1 = Catorcenas.objects.filter(fecha_inicial__lte=incapacidad.fecha,fecha_final__gte=incapacidad.fecha).first()
                cat2 = Catorcenas.objects.filter(fecha_inicial__lte=incapacidad.fecha_fin,fecha_final__gte=incapacidad.fecha_fin).first()
                
                print("Actual",catorcena_actual)
                
                if cat1.catorcena == catorcena_actual.catorcena:
                    print("Es la cat1 atrasada: ", cat1.catorcena)
                    diferencia = cat1.fecha_final - incapacidad_fecha
                    dias = abs(diferencia.days) + 1
                    #print("dias correspondientes",dias)
                    incapacidades = dias
                    
                    #realiza el calculo de la incapacidad
                    if incapacidades > 0:
                        incidencias_incapacidades_pasajes = incapacidades
                        if incapacidades > 3:
                            incidencias_incapacidades = incidencias_incapacidades + (incapacidades - 3) #3 dias se pagan
                            print("ESTAS SON LAS INCIDENCAS INCAPACIDADES", incidencias_incapacidades)
                    
                    incapacidades_anterior = 0
                    incapacidades_actual = incapacidades
                    
                elif cat2.catorcena == catorcena_actual.catorcena:
                    print("Es la cat2 actual: ", cat2.catorcena)
                
                    cat1_diferencia = cat1.fecha_final - incapacidad.fecha
                    dias_uno = abs(cat1_diferencia.days) + 1
                    print("dias correspondientes cat 1 Atrasada",dias_uno)
                    
                    cat2_diferencia = incapacidad.fecha_fin - cat2.fecha_inicial
                    dias_dos = abs(cat2_diferencia.days) + 1
                    print("dias correspondientes cat 2 Actual",dias_dos)
                    
                    incapacidades = dias_uno + dias_dos
                    #incapacidades = dias_dos

                    incapacidades_anterior = dias_uno
                    incapacidades_actual = dias_dos
                
                    #realiza el calculo de la incapacidad
                    if incapacidades > 0:
                        incidencias_incapacidades_pasajes = incapacidades
                        if incapacidades > 3:
                            incidencias_incapacidades = incidencias_incapacidades + (incapacidades - 3) #3 dias se pagan
                            print("ESTAS SON LAS INCIDENCAS INCAPACIDADES", incidencias_incapacidades)
                                                  
            else:#Pertenece a solo una catorcena
                print("PERTENECE A LA CATORCENA ACTUAL Y CALCULA LAS INCAPACIDADES")
                for incapacidad in incapacidades:
                    diferencia = incapacidad.fecha_fin - incapacidad.fecha
                    incapacidades = diferencia.days + 1
                    
                #realiza el calculo de la incapacidad
                if incapacidades > 0:
                    incidencias_incapacidades_pasajes = incapacidades
                    if incapacidades > 3:
                        incidencias_incapacidades = incidencias_incapacidades + (incapacidades - 3) #3 dias se pagan
                        print("ESTAS SON LAS INCIDENCAS INCAPACIDADES", incidencias_incapacidades)
                
                incapacidades_anterior = 0
                incapacidades_actual = incapacidades
                
        else: 
            incapacidades = 0
            print("NO TIENE INCAPACIDADES: ",incapacidades)
                
        #calcular el numero de vacaciones
        cantidad_dias_vacacion = 0
        if vacaciones.exists():
            for vacacion in vacaciones:
                diferencia = vacacion.fecha_fin - vacacion.fecha_inicio
                cantidad_dias_vacacion = diferencia.days + 1
                
        print("total vacaciones: ", cantidad_dias_vacacion)
        
        #numero de catorena
        catorcena_num = catorcena_actual.catorcena 
        
        incidencias = 0
        incidencias_retardos = 0
        
        if faltas > 0:
            incidencias = incidencias + faltas
            print("Faltas: ", faltas)
            
        if retardos > 0:
            incidencias_retardos = retardos // 3 #3 retardos se decuenta 1 dia
            
        if castigos > 0:
            incidencias = incidencias + castigos
            print("Castigos incidencias contadas", castigos)
        
        if permiso_sin > 0:
            incidencias = incidencias + permiso_sin
        
        pago_doble = 0  
        if dia_extra > 0:
            pago_doble = Decimal(dia_extra * salario)
        
        incapacidad = str("")   
                            
        #calculo de la prenomina - regla de tres   
        dias_de_pago = 12
        print("incidencias", incidencias, "incidencias_retarods", incidencias_retardos, "incidencias_inca", incidencias_incapacidades)
        dias_laborados = dias_de_pago - (incidencias + incidencias_retardos + incidencias_incapacidades)
        proporcion_septimos_dias = Decimal((dias_laborados * 2) / 12)
        proporcion_laborados = proporcion_septimos_dias + dias_laborados
        salario_catorcenal = (proporcion_laborados * salario) + pago_doble
        
        print("las incidencias incapacidades", incidencias_incapacidades)
        if incidencias_incapacidades_pasajes > 0:
            apoyo_pasajes = (apoyo_pasajes / 12 * (12 - (incidencias + incidencias_incapacidades_pasajes))) #12 son los dias trabajados
            print("Aqui es donde se ejecuta el codigo")
        else:
            apoyo_pasajes = (apoyo_pasajes / 12 * (12 - (incidencias))) #12 son los dias trabajados
            print("Aqui no se deberia ejecutar el codigo")
        
        print("apoyos pasajes: ", apoyo_pasajes)
        print("total: ", salario_catorcenal)
        print("pagar nomina: ", apoyo_pasajes + salario_catorcenal)
        
        total_percepciones = salario_catorcenal + apoyo_pasajes + total_bonos
        total_deducciones = prestamo_infonavit + prestamo_fonacot
        pagar_nomina = total_percepciones - total_deducciones
        
        if retardos == 0: 
            retardos = ''
        
        if castigos == 0:
            castigos = ''
            
        if permiso_goce == 0:
            permiso_goce = ''
            
        if permiso_sin == 0:
            permiso_sin = ''
            
        if descanso == 0:
            descanso = ''

        if dia_extra == 0:
            dia_extra = ''
                    
        if incapacidades == 0:
            incapacidades = ''
        
        if faltas == 0:
            faltas = ''
        
        if comision == 0:
            comision = ''
            
        if domingo == 0:
            domingo = ''
            
        if festivos == 0:
            festivos = ''
            
        if economicos == 0:
            economicos = ''
            
        if cantidad_dias_vacacion == 0:
            cantidad_dias_vacacion = ''
        
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
        prenomina.extra = prenomina.dia_extra_set.filter(fecha__range=(catorcena_actual.fecha_inicial, catorcena_actual.fecha_final))
        #fechas con factores
        fechas_con_retardos = [retardo.fecha for retardo in prenomina.retardos]
        fechas_con_descanso = [descans.fecha for descans in prenomina.descanso]
        fechas_con_faltas = [falta.fecha for falta in prenomina.faltas]
        fechas_con_comision = [comisio.fecha for comisio in prenomina.comision]
        fechas_con_domingo = [doming.fecha for doming in prenomina.domingo]
        fechas_con_extra = [extra.fecha for extra in prenomina.extra]
        fechas_con_festivos = [festivo.dia_festivo for festivo in festivos]
        fechas_con_economicos = [economico.fecha for economico in economicos]
        #lista de tuplas con la fecha y su etiqueta
        fechas_con_etiquetas = [(fecha, "retardo", prenomina.retardos.filter(fecha=fecha).first().comentario if fecha in fechas_con_retardos else "") if fecha in fechas_con_retardos
                                else (fecha, "castigo", prenomina.castigos.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario if any(castigos.fecha <= fecha <= castigos.fecha_fin for castigos in prenomina.castigos) else "") if any(castigos.fecha <= fecha <= castigos.fecha_fin for castigos in prenomina.castigos)
                                else (fecha, "permiso_goce", prenomina.permiso_goce.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario if any(permiso_goce.fecha <= fecha <= permiso_goce.fecha_fin for permiso_goce in prenomina.permiso_goce) else "") if any(permiso_goce.fecha <= fecha <= permiso_goce.fecha_fin for permiso_goce in prenomina.permiso_goce)
                                else (fecha, "permiso_sin", prenomina.permiso_sin.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario if any(permiso_sin.fecha <= fecha <= permiso_sin.fecha_fin for permiso_sin in prenomina.permiso_sin) else "") if any(permiso_sin.fecha <= fecha <= permiso_sin.fecha_fin for permiso_sin in prenomina.permiso_sin)
                                else (fecha, "incapacidades", prenomina.incapacidades.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario if any(incapacidad.fecha <= fecha <= incapacidad.fecha_fin for incapacidad in prenomina.incapacidades) else "") if any(incapacidad.fecha <= fecha <= incapacidad.fecha_fin for incapacidad in prenomina.incapacidades)
                                else (fecha, "descanso", prenomina.descanso.filter(fecha=fecha).first().comentario if fecha in fechas_con_descanso else "") if fecha in fechas_con_descanso
                                #else (fecha, "incapacidades", prenomina.incapacidades.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().comentario, prenomina.incapacidades.filter(fecha__lte=fecha, fecha_fin__gte=fecha).first().url if any(incapacidad.fecha <= fecha <= incapacidad.fecha_fin for incapacidad in prenomina.incapacidades) else "") if any(incapacidad.fecha <= fecha <= incapacidad.fecha_fin for incapacidad in prenomina.incapacidades)
                                else (fecha, "faltas",prenomina.faltas.filter(fecha=fecha).first().comentario if fecha in fechas_con_faltas else "") if fecha in fechas_con_faltas
                                else (fecha, "comision", prenomina.comision.filter(fecha=fecha).first().comentario if fecha in fechas_con_comision else "") if fecha in fechas_con_comision
                                else (fecha, "domingo", prenomina.domingo.filter(fecha=fecha).first().comentario if fecha in fechas_con_domingo else "") if fecha in fechas_con_domingo
                                else (fecha, "día extra", prenomina.extra.filter(fecha=fecha).first().comentario if fecha in fechas_con_extra else "") if fecha in fechas_con_extra
                                else (fecha, "economico", "") if fecha in fechas_con_economicos
                                else (fecha, "festivo", "") if fecha in fechas_con_festivos
                                else (fecha, "vacaciones", "") if any(vacacion.fecha_inicio <= fecha <= vacacion.fecha_fin and fecha != vacacion.dia_inhabil for vacacion in vacaciones)
                                else (fecha, "asistencia", "") for fecha in dias_entre_fechas]
        abreviaciones = {
            "economico": "D/E",
            "castigo": "CAS",
            "retardo": "R",
            "vacaciones": "V",
            "comision": "C",
            "faltas": "F",
            "permiso_goce": "PGS",
            "festivo": "FE",
            "incapacidades": "I",
            "permiso_sin": "PSS",
            "descanso": "DEZ",
            "asistencia": "x"
        }
        abreviaciones_colores_cortas = {
            "D/E": "FF92d050",    # Verde claro
            "CAS": "FF948a54",    # Marrón
            "R": "FFe26b0a",      # Naranja
            "V": "FF00b0f0",      # Azul claro
            "C": "FF538dd5",      # Azul
            "F": "FFFF0000",      # Rojo
            "PGS": "FFfcd5b4",    # Beige
            "FE": "FFb1a0c7",     # Púrpura claro
            "I": "FF963634",      # Rojo oscuro
            "PSS": "FFc00000",    # Rojo oscuro
            "DEZ": "FF00b050",     # Verde
            "x": "FFFFFF"       # Blanco
        }
        #estados_por_dia = [estado for _, estado, _ in fechas_con_etiquetas]
        estados_por_dia = [abreviaciones.get(estado, estado) for _, estado, _ in fechas_con_etiquetas]
        # Agregar los valores a la lista rows para cada prenomina
        row = (
            prenomina.empleado.status.perfil.numero_de_trabajador,
            prenomina.empleado.status.perfil.nombres + ' ' + prenomina.empleado.status.perfil.apellidos,
            prenomina.empleado.status.puesto.puesto,
            prenomina.empleado.status.perfil.proyecto.proyecto,
            prenomina.empleado.status.perfil.subproyecto.subproyecto,
            *estados_por_dia,  # Desempaquetar estados_por_dia aquí
            salario_catorcenal_costo,
            salario_catorcenal,
            apoyo_pasajes, #Prevision social pasajes
            total_bonos,
            total_percepciones,
            prestamo_infonavit,
            prestamo_fonacot,
            total_deducciones,
            pagar_nomina,
            salario,
            ((proporcion_septimos_dias*salario)/2)
        )
        rows.append(row)
        
        sub_salario_catorcenal_costo = sub_salario_catorcenal_costo + salario_catorcenal_costo
        sub_salario_catorcenal = sub_salario_catorcenal + salario_catorcenal
        sub_apoyo_pasajes = sub_apoyo_pasajes + apoyo_pasajes
        sub_total_bonos = sub_total_bonos + total_bonos
        sub_total_percepciones = sub_total_percepciones + total_percepciones
        sub_prestamo_infonavit = sub_prestamo_infonavit + prestamo_infonavit
        sub_prestamo_fonacot = sub_prestamo_fonacot + prestamo_fonacot
        sub_total_deducciones = sub_total_deducciones + total_deducciones
        sub_pagar_nomina = sub_pagar_nomina + pagar_nomina
        
        
                 
    # Ahora puedes usar la lista rows como lo estás haciendo actualmente en tu código
    for row_num, row in enumerate(rows, start=4):
        for col_num, value in enumerate(row, start=1):
            if col_num < 4:
                ws.cell(row=row_num, column=col_num, value=value).style = body_style
            elif col_num == 5:
                ws.cell(row=row_num, column=col_num, value=value).style = date_style
            elif 5 < col_num < 24:
                ws.cell(row=row_num, column=col_num, value=value).style = body_style
                # Verificar si el valor está en la lista de abreviaciones
                if value in abreviaciones_colores_cortas:
                    color_hex = abreviaciones_colores_cortas[value]
                    fill = PatternFill(start_color=color_hex, end_color=color_hex, fill_type="solid")
                    ws.cell(row=row_num, column=col_num).fill = fill
            elif col_num >= 24:
                ws.cell(row=row_num, column=col_num, value=value).style = money_style
            else:
                ws.cell(row=row_num, column=col_num, value=value).style = body_style

    add_last_row = ['Total','','','','','','','','','','','','','','','','','','',
                    sub_salario_catorcenal_costo,
                    sub_salario_catorcenal,
                    sub_apoyo_pasajes,
                    sub_total_bonos,
                    sub_total_percepciones,
                    sub_prestamo_infonavit,
                    sub_prestamo_fonacot,
                    sub_total_deducciones,
                    sub_pagar_nomina
                    ]
    ws.append(add_last_row) 

    # Agregar las abreviaciones como una tabla de dos columnas
    for key, value in abreviaciones.items():
        ws.append([key, value])

    # Aplicar el estilo a cada celda de la tabla de abreviaciones cortas con colores de fondo
    for row_num, row in enumerate(ws.iter_rows(min_row=ws.max_row - len(abreviaciones) + 1, max_row=ws.max_row), start=ws.max_row - len(abreviaciones) + 1):
        for col_num, cell in enumerate(row, start=1):
            cell.style = bold_money_style
            if cell.value is not None:
                # Obtener el color correspondiente para la abreviación corta actual
                color = abreviaciones_colores_cortas.get(cell.value, "FFFFFF")  # Por defecto, color blanco
                cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
    
    sheet = wb['Sheet']
    wb.remove(sheet)
    wb.save(response)

    return(response)