from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from proyecto.models import UserDatos, Perfil, Catorcenas, Costo, TablaFestivos, Vacaciones, Economicos, Economicos_dia_tomado, Vacaciones_dias_tomados
from django.db import models
from django.db.models import Subquery, OuterRef, Q
from revisar.models import AutorizarPrenomina, Estado
from proyecto.filters import CostoFilter
from .models import Prenomina, Retardos, Castigos, Permiso_goce, Permiso_sin, Descanso, Incapacidades, Faltas, Comision, Domingo
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
# Create your views here.

@login_required(login_url='user-login')
def Tabla_prenomina(request):
    user_filter = UserDatos.objects.get(user=request.user)
    ahora = datetime.date.today()
    catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
    if user_filter.distrito.distrito == 'Matriz':
        costo = Costo.objects.filter(complete=True, status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador")
    else:
        costo = Costo.objects.filter(distrito=user_filter.distrito, complete=True,  status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador")

    costo_filter = CostoFilter(request.GET, queryset=costo)
    costo = costo_filter.qs

    prenominas = Prenomina.objects.filter(empleado__in=costo,fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final])

    #crear las prenominas actuales si es que ya es nueva catorcena
    for empleado in costo:
        #checar si existe prenomina para el empleado en la catorcena actual
        prenomina_existente = prenominas.filter(empleado=empleado).exists()
        #si no existe crear una nueva prenomina
        if not prenomina_existente:
            nueva_prenomina = Prenomina(empleado=empleado, fecha=datetime.date.today())
            nueva_prenomina.save()
    
    prenominas = Prenomina.objects.filter(empleado__in=costo, fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]).order_by("empleado__status__perfil__numero_de_trabajador")

    for prenomina in prenominas:
        ultima_autorizacion = AutorizarPrenomina.objects.filter(prenomina=prenomina).order_by('-updated_at').first() #Ultimo modificado

        if ultima_autorizacion is not None:
            prenomina.valor = ultima_autorizacion.estado.tipo #Esta bien como agarra el dato de RH arriba que es el primero
        prenomina.estado_general = determinar_estado_general(ultima_autorizacion)

    if request.method =='POST' and 'Excel' in request.POST:
        return Excel_estado_prenomina(prenominas, user_filter)
    
    p = Paginator(prenominas, 50)
    page = request.GET.get('page')
    salidas_list = p.get_page(page)

    context = {
        'costo_filter':costo_filter,
        #'costo': costo,
        'salidas_list': salidas_list,
        'prenominas':prenominas
    }
    return render(request, 'prenomina/Tabla_prenomina.html', context)

def prenomina_revisar_ajax(request, pk):
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

@login_required(login_url='user-login')
def PrenominaRevisar(request, pk):
    user_filter = UserDatos.objects.get(user=request.user)
    ahora = datetime.date.today()
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

    if catorcena_actual:
        delta = catorcena_actual.fecha_final - catorcena_actual.fecha_inicial
        dias_entre_fechas = [catorcena_actual.fecha_inicial + timedelta(days=i) for i in range(delta.days + 1)]

    if request.method == 'POST' and 'guardar_cambios' in request.POST:
        revisado_rh, created = AutorizarPrenomina.objects.get_or_create(prenomina=prenomina, tipo_perfil=user_filter.tipo)
        estado_verificado = Estado.objects.get(tipo="aprobado")
        revisado_rh.estado=estado_verificado
        nombre = Perfil.objects.get(numero_de_trabajador = user_filter.numero_de_trabajador, distrito = user_filter.distrito)
        revisado_rh.perfil=nombre
        revisado_rh.comentario="Revisado por RH"
        revisado_rh.save()
        for fecha, etiqueta, comentario in fechas_con_etiquetas:
            fecha_str = fecha.strftime('%Y-%m-%d')
            nuevo_estado = request.POST.get(f'estado_{fecha_str}')
            nuevo_comentario = request.POST.get(f'comentario_{fecha_str}')

            # revisa si el estado ha cambiado
            if nuevo_estado and nuevo_estado != etiqueta:
                # elimina el dato asociado a la fecha
                prenomina.retardos.filter(fecha=fecha).delete()
                prenomina.castigos.filter(fecha=fecha).delete()
                prenomina.permiso_goce.filter(fecha=fecha).delete()
                prenomina.permiso_sin.filter(fecha=fecha).delete()
                prenomina.descanso.filter(fecha=fecha).delete()
                prenomina.incapacidades.filter(fecha=fecha).delete()
                prenomina.faltas.filter(fecha=fecha).delete()
                prenomina.comision.filter(fecha=fecha).delete()
                prenomina.domingo.filter(fecha=fecha).delete()

            # crea el nuevo dato según el nuevo estado o comentario
            if nuevo_estado and nuevo_estado != 'asistencia':
                evento_model = {
                    'retardo': Retardos,
                    'castigo': Castigos,
                    'permiso_goce': Permiso_goce,  
                    'permiso_sin': Permiso_sin,  
                    'descanso': Descanso,  
                    'incapacidades': Incapacidades,  
                    'faltas': Faltas,  
                    'comision': Comision,  
                    'domingo': Domingo  
                }.get(nuevo_estado)

                if evento_model:
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
        }

    return render(request, 'prenomina/Actualizar_revisar.html',context)

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