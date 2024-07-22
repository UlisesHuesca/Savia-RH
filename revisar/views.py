#Bonos
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from esquema.forms import AutorizarSolicitudesUpdateForm
from .models import AutorizarSolicitudes
from esquema.models import BonoSolicitado
from proyecto.models import UserDatos,Perfil,Status,Costo,Catorcenas,SalarioDatos,Empresa
from prenomina.models import PrenominaIncidencias
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from datetime import date
import datetime
from decimal import Decimal
from django.db.models import F
from prenomina.filters import PrenominaFilter
from datetime import datetime, timedelta
from django.utils import timezone
from dateutil import parser

#Prenomina
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from proyecto.models import UserDatos,Perfil, Catorcenas, Costo, TablaFestivos, Vacaciones, Economicos, Economicos_dia_tomado, Vacaciones_dias_tomados, Trabajos_encomendados, Solicitud_vacaciones, Solicitud_economicos
from esquema.models import Solicitud
from .models import AutorizarPrenomina, Estado
from django.db.models import Q
from proyecto.filters import CostoFilter
from prenomina.models import Prenomina
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
import math

#importar reporte Excel prenomina
from prenomina.views import obtener_catorcena
from calculos.utils import excel_estado_prenomina

from prenomina.filters import PrenominaFilter
from prenomina.views import obtener_catorcena
#envio de correos
from django.core.mail import EmailMessage, BadHeaderError
from django.http import HttpResponse
from smtplib import SMTPException
from django.conf import settings
from django.template.loader import render_to_string


#BONOS
def asignarBonoCosto(solicitud):
    #una lista que lleva cada cantidad del bono
    cantidad = []
    #la lista de los perfiles que recibiran los bonos
    lista_perfiles = []

    #se guarda la fecha de la solicitud aprobada por el gerente
    aprobada = Solicitud.objects.get(id=solicitud)
    aprobada.fecha_autorizacion = timezone.now()
    aprobada.save()

    #trae los empleados con sus respectivos bonos
    empleados = BonoSolicitado.objects.filter(solicitud_id = solicitud).values("trabajador_id","cantidad")
    porcentaje = SalarioDatos.objects.get(pk = 1)

    for item in empleados:
        trabajador_id = item['trabajador_id']
        cantidad_obtenida = item['cantidad']
        lista_perfiles.append(trabajador_id)
        cantidad.append(cantidad_obtenida)

    #se asigna cada empleado con su respectivo bono
    for index,perfil in enumerate(lista_perfiles):
        costo = Costo.objects.get(status__perfil_id = perfil)
        costo.bono_total = costo.bono_total + cantidad[index]
        costo.save()

        #realizar calculo bono - costo
        costo.total_apoyosbonos_agregcomis = costo.campamento + costo.bono_total #bien
        costo.comision_complemeto_salario_bonos= ((costo.campamento + costo.bono_total)/Decimal(porcentaje.comision_bonos/10)) - costo.total_apoyosbonos_agregcomis #bien
        costo.total_costo_empresa = costo.sueldo_mensual_neto + costo.complemento_salario_mensual + costo.apoyo_de_pasajes + costo.impuesto_estatal + costo.imms_obrero_patronal + costo.sar + costo.cesantia + costo.infonavit + costo.isr + costo.total_apoyosbonos_empleadocomp + costo.total_apoyosbonos_agregcomis + costo.comision_complemeto_salario_bonos #18221.5
        costo.total_costo_empresa = costo.total_costo_empresa + costo.total_prima_vacacional
        costo.ingreso_mensual_neto_empleado= costo.sueldo_mensual_neto + costo.complemento_salario_mensual + costo.apoyo_de_pasajes + costo.total_apoyosbonos_empleadocomp + costo.total_apoyosbonos_agregcomis
        costo.save()

        """
        print("bonos: ",costo.total_apoyosbonos_agregcomis)
        print("comision: ",costo.comision_complemeto_salario_bonos)
        print("costo total empresa: ",costo.total_costo_empresa)
        print("costo total empleado: ",costo.ingreso_mensual_neto_empleado)
        """

        """
        costo.total_apoyosbonos_agregcomis = costo.campamento #Modificar falta suma
        costo.comision_complemeto_salario_bonos= (costo.complemento_salario_mensual + costo.campamento)*Decimal(dato.comision_bonos/100) #Falta suma dentro de la multiplicacion
        costo.total_costo_empresa = costo.sueldo_mensual_neto + costo.complemento_salario_mensual + costo.apoyo_de_pasajes + costo.impuesto_estatal + costo.imms_obrero_patronal + costo.sar + costo.cesantia + costo.infonavit + costo.isr + costo.total_apoyosbonos_empleadocomp #18221.5
        costo.total_costo_empresa = costo.total_costo_empresa + costo.total_prima_vacacional
        costo.ingreso_mensual_neto_empleado= costo.sueldo_mensual_neto + costo.complemento_salario_mensual + costo.apoyo_de_pasajes + costo.total_apoyosbonos_empleadocomp # + costo.total_apoyosbonos_agregcomis
        """


@login_required(login_url='user-login')
def autorizarSolicitud(request,solicitud):
    from datetime import datetime
    if request.method == "POST":
        autorizarSolicitudesUpdateForm = AutorizarSolicitudesUpdateForm(request.POST)
        
        if autorizarSolicitudesUpdateForm.is_valid():
            usuario = request.user
            rol = UserDatos.objects.get(user_id = usuario.id)
                    
            autorizar = AutorizarSolicitudes.objects.get(solicitud_id = solicitud, tipo_perfil_id = rol.tipo_id)
            
            comentarioDato = autorizarSolicitudesUpdateForm.cleaned_data['comentario']
            if 'aprobar' in request.POST:#aprobado

                if rol.tipo_id == 6:#superintendente -> control tecnico

                        #se guardan los datos de la autorizacion en el superintendente
                        autorizar.estado_id = 1 #aprobado
                        autorizar.comentario = comentarioDato
                        autorizar.save(update_fields=['estado_id', 'comentario'])

                        #se busca el perfil del control tecnico corresponsiente al distrito - recuerda me devuelve una tupla y la posicion 0 = no.trabajador, 6 = distrito
                        rol = UserDatos.objects.filter(distrito_id=usuario.userdatos.distrito, tipo_id=7).values_list('numero_de_trabajador','distrito').first()                      
                        perfil_control_tecnico = Perfil.objects.filter(numero_de_trabajador = rol[0], distrito_id = rol[1]).values('id').first()
                                                    
                        #buscar o crea la autorizacion para el control tecnico
                        control_tecnico, created = AutorizarSolicitudes.objects.get_or_create(
                            solicitud_id=solicitud,
                            tipo_perfil_id=7,
                            #comentario = comentarioDato,
                            perfil_id = perfil_control_tecnico['id'],
                            defaults={'estado_id': 3}  # Pendiente
                        )

                        #entra en el flujo de verifica o cambios
                        if autorizar.revisar and not created:
                            control_tecnico.estado_id = 3
                            control_tecnico.comentario = comentarioDato
                            control_tecnico.save()

                        messages.success(request, "La solicitud se aprobó por el Superintendente, pasa a revisión a Control Técnico")
                        return redirect('listarBonosVarilleros')

                elif rol.tipo_id == 7: #control tecnico -> gerente
                        #se guardan los datos de la autorizacion del control tecnico
                        autorizar.estado_id = 1#aprobado
                        autorizar.comentario = None
                        autorizar.save(update_fields=['estado_id', 'comentario'])


                        #se busca el perfil del gerente correspondiente al distrito
                        rol = UserDatos.objects.filter(distrito_id=usuario.userdatos.distrito, tipo_id=8).values_list('numero_de_trabajador','distrito').first()
                        perfil_gerente = Perfil.objects.filter(numero_de_trabajador = rol[0], distrito_id = rol[1]).values('id').first()

                        #buscar o crea la autorizacion para el gerente
                        gerente, created = AutorizarSolicitudes.objects.get_or_create(
                            solicitud_id=solicitud,
                            tipo_perfil_id=8,
                            #comentario = comentarioDato,
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
                        autorizar.estado_id = 1
                        autorizar.comentario = comentarioDato
                        autorizar.save()

                        #IMPLEMENTAR COSTO
                        asignarBonoCosto(solicitud)

                        messages.success(request, "La solicitud se aprobó por el Gerente")
                        return redirect('listarBonosVarilleros')


            elif 'rechazar' in request.POST :#rechazado
                #autorizar - asignar el estado de la solicitud
                autorizar.estado_id = 2#rechazado
                autorizar.comentario = comentarioDato
                autorizar.save()

                messages.error(request, "La solicitud fue rechazada")
                return redirect('listarBonosVarilleros')

            elif 'cambios': #revisar
                autorizar.estado_id = 4
                autorizar.comentario = comentarioDato
                autorizar.revisar = True
                autorizar.save()

                messages.success(request, "El supervisor debe realizar cambios en la solicitud emitida")
                return redirect('listarBonosVarilleros')
            
#PRENOMINA
@login_required(login_url='user-login')
def Tabla_solicitudes_prenomina(request):
    user_filter = UserDatos.objects.get(user=request.user)
    if user_filter.tipo.id in [7,8,9,10,11]:
        #se llama la funcion para obtener la cartocena actual - llamada de app prenomina
        catorcena_actual = obtener_catorcena()
        
        revisar_perfil = Perfil.objects.get(distrito=user_filter.distrito,numero_de_trabajador=user_filter.numero_de_trabajador)
        if user_filter.tipo.id in [9,10,11]:
            costo = Costo.objects.filter(complete=True, status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador")
        else:
            costo = Costo.objects.filter(status__perfil__distrito=user_filter.distrito, complete=True,  status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador")

        #costo_filter = CostoFilter(request.GET, queryset=costo)
        #costo = costo_filter.qs
        #Trae las prenominas que le toca a cada perfil
        if user_filter.tipo.nombre ==  "Control Tecnico": #1er perfil
            prenominas_verificadas = Prenomina.objects.filter(empleado__in=costo,autorizarprenomina__tipo_perfil__nombre="RH",catorcena = catorcena_actual.id).distinct()
            rh = prenominas = Prenomina.objects.filter(empleado__in=costo, catorcena = catorcena_actual.id).order_by("empleado__status__perfil__apellidos") #Estas son todas las que deben haber en la catorcena
            rh = rh.count()
            ct = prenominas_verificadas.count()
            if ct < rh:
                mensaje_gerencia="Pendientes por autorizar por RH = "+ str(rh-ct)
            elif ct == rh:
                mensaje_gerencia = "Todas revisadas por RH"
        elif user_filter.tipo.nombre ==  "Gerencia":  #2do perfil
            prenominas_verificadas = Prenomina.objects.filter(empleado__in=costo,autorizarprenomina__tipo_perfil__nombre="Control Tecnico",catorcena=catorcena_actual).distinct()
            rh = prenominas = Prenomina.objects.filter(empleado__in=costo,catorcena=catorcena_actual).order_by("empleado__status__perfil__numero_de_trabajador") #Estas son todas las que deben haber en la catorcena
            rh = rh.count()
            ct = prenominas_verificadas.count()
            if ct < rh:
                mensaje_gerencia="Pendientes por autorizar entre RH y CT = "+ str(rh-ct)
            elif ct == rh:
                mensaje_gerencia = "Todas revisadas por RH y CT"
        #Las ordena por numero de trabajador
        prenominas = prenominas_verificadas.order_by("empleado__status__perfil__numero_de_trabajador")
        prenomina_filter = PrenominaFilter(request.GET, queryset=prenominas)
        prenominas = prenomina_filter.qs
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
            filtro = False
            return excel_estado_prenomina(request,prenominas,filtro,user_filter)

        if request.method =='POST' and 'Autorizar' in request.POST:
            if user_filter.tipo.nombre ==  "Control Tecnico":
                prenominas_filtradas = [prenom for prenom in prenominas if prenom.estado_general == 'Controles técnicos pendiente']
                if prenominas_filtradas:
                    # Llamar a la función Autorizar_gerencia con las prenominas filtradas
                    return Autorizar_general(prenominas_filtradas, user_filter,request)
                else:
                    # Si no hay prenominas que cumplan la condición, manejar según sea necesario
                    messages.error(request,'Ya se han autorizado todas las prenominas pendientes')
            if user_filter.tipo.nombre ==  "Gerencia":
                prenominas_filtradas = [prenom for prenom in prenominas if prenom.estado_general == 'Gerente pendiente']
                if prenominas_filtradas:
                    # Llamar a la función Autorizar_gerencia con las prenominas filtradas
                    return Autorizar_general(prenominas_filtradas, user_filter,request)
                else:
                    # Si no hay prenominas que cumplan la condición, manejar según sea necesario
                    messages.error(request,'Ya se han autorizado todas las prenominas pendientes')

        p = Paginator(prenominas, 50)
        page = request.GET.get('page')
        salidas_list = p.get_page(page)

        context = {
            'prenomina_filter':prenomina_filter,
            'salidas_list': salidas_list,
            'user_filter':user_filter,
            'mensaje_gerencia':mensaje_gerencia,
        }
        return render(request, 'revisar/prenominas_solicitudes.html', context)
    else:
        return render(request, 'revisar/403.html')
    
@login_required(login_url='user-login')
def Prenomina_Solicitud_Revisar(request, pk):
    user_filter = UserDatos.objects.get(user=request.user)
    if user_filter.tipo.nombre == "Gerencia" or "Control Tecnico":
        #ahora = datetime.date.today()
        #ahora = datetime.date.today() + timedelta(days=10)
        costo = Costo.objects.get(id=pk)
        #se trae la funcion desde Prenomina.view para obtener la catorcena actual
        catorcena_actual=obtener_catorcena()
        prenomina = Prenomina.objects.get(empleado_id=costo.id,catorcena_id=catorcena_actual.id)
        verificado_rh = AutorizarPrenomina.objects.filter(prenomina_id=prenomina.id).first()
        
        #Se crean las fechas para ser mostradas en el template
        fecha_inicio = catorcena_actual.fecha_inicial
        fecha_fin = catorcena_actual.fecha_final

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
            solicitud= Solicitud_economicos.objects.get(status=costo.status,fecha=fecha_economico)
            return PdfFormatoEconomicos(request, solicitud)
        
        if request.method =='POST' and 'vacaciones_pdf' in request.POST:
            fecha_vacaciones = request.POST['vacaciones_pdf']
            fecha_vacaciones = parser.parse(fecha_vacaciones).date()
            solicitud = Solicitud_vacaciones.objects.filter(status=costo.status, fecha_inicio__lte=fecha_vacaciones, fecha_fin__gte=fecha_vacaciones).first()
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
            'costo':costo,
            'autorizacion1':autorizacion1,
            'autorizacion2':autorizacion2,
            'catorcena_actual':catorcena_actual,
            'incidencias':incidencias,
            'fechas':fechas,
            }

        return render(request, 'revisar/Prenomina_Solicitud_Revisar.html',context)
    else:
        return render(request, 'revisar/403.html')

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

def Autorizar_general(prenominas, user_filter,request):
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



