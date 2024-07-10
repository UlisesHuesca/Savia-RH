#from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.http import FileResponse
from django.contrib.auth.decorators import login_required

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch,cm,mm
from reportlab.lib.pagesizes import letter,A4,landscape
import io
from reportlab.lib import colors
from reportlab.lib.colors import Color, black, blue, red, white
from reportlab.platypus import BaseDocTemplate, Frame, Paragraph, NextPageTemplate, PageBreak, PageTemplate,Table, SimpleDocTemplate,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import os
from proyecto.models import Perfil, Vacaciones, Economicos, UserDatos, Uniforme, DatosBancarios, Catorcenas
#from django.contrib.auth.decorators import login_required
#from .filters import ArticulosparaSurtirFilter
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import NamedStyle, Font, PatternFill
from openpyxl.utils import get_column_letter
import datetime
from django.db.models.functions import Concat, Extract
from django.db.models import Value
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta #Años entre 2 fechas con años bisiestos
#PDF generator
from django.db.models import Q
from openpyxl.drawing.image import Image
from openpyxl.chart import PieChart, LineChart, Reference
from openpyxl.chart.axis import DateAxis
from collections import Counter
from proyecto.models import Costo, Bonos, Status, DatosBancarios
from django.db.models import Sum
from django.core.mail import send_mail
from django.conf import settings
import locale
from proyecto.models import Costo,CostoAnterior,SalarioDatos
import calendar
locale.setlocale( locale.LC_ALL, '' )

@login_required(login_url='user-login')
def index(request):#Por si se hace una carga de json y no se activan ciertos boleanos
    #for dato in DatosBancarios.objects.filter(complete=True):
    #    dato.status.complete_bancarios = True
    #    dato.status.save()

    #vacacion = Vacaciones.objects.filter(periodo="2023")
    #for dato in vacacion:
    #    status = Status.objects.get(id=dato.status.id)
    #    status.complete_vacaciones = False
    #    status.save()
    #    dato.delete()

    #fecha_actual = date.today()
    #año_actual = str(fecha_actual.year)
    #fecha_hace_un_año = fecha_actual - relativedelta(years=1)
    #status= Status.objects.filter(complete=True, perfil__baja=False)
    #reinicio = status.filter(Q(fecha_planta_anterior__lte=fecha_hace_un_año) |Q(fecha_planta__lte=fecha_hace_un_año))
    #economicos = Economicos.objects.exclude(status__in=reinicio)
    #for dato in economicos:
    #    status = Status.objects.get(id=dato.status.id)
    #    status.complete_economicos = False
    #    status.save()
    #    dato.delete()
    """
    #Falta implementar la tarea que se dispare automaticamente
    # Obtener la fecha y hora actuales
    fecha_actual = datetime.datetime.now().date()
    #print("fecha actual: ",fecha_actual)

    # Primer día del mes
    primer_dia_mes = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, 1).date()
    print('primer dia mes: ',primer_dia_mes)

    # Último día del mes actual
    ultimo_dia_mes = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month,
                                        calendar.monthrange(datetime.datetime.now().year, datetime.datetime.now().month)[1]).date()

    # Asegurarse de que sea la última hora del último día del mes
    #ultimo_dia_mes = datetime.datetime.combine(ultimo_dia_mes, datetime.time.max)
    print("ultimo dia: ",ultimo_dia_mes)

    #if fecha_actual == ultimo_dia_mes:
    if 1 ==1:
        #se ejecuta el bull_create
        #Me atre todos los costos actualmente
        costos = Costo.objects.all()
        porcentaje = SalarioDatos.objects.get(pk = 1)

        #Pasa los datos del modelo Costo a CostoAnterior para llevar el registro
        volcar_datos = [CostoAnterior(
            amortizacion_infonavit = costo.amortizacion_infonavit,
            fonacot = costo.fonacot,
            neto_catorcenal_sin_deducciones = costo.neto_catorcenal_sin_deducciones,
            complemento_salario_catorcenal = costo.complemento_salario_catorcenal,
            sueldo_diario=costo.sueldo_diario,
            sdi=costo.sdi,
            apoyo_de_pasajes = costo.apoyo_de_pasajes,
            imms_obrero_patronal = costo.imms_obrero_patronal,
            apoyo_vist_familiar = costo.apoyo_vist_familiar,
            estancia = costo.estancia,
            renta = costo.renta,
            apoyo_estudios = costo.apoyo_estudios,
            amv = costo.amv,
            gasolina = costo.gasolina,
            campamento = costo.campamento,
            total_deduccion = costo.total_deduccion,
            neto_pagar = costo.neto_pagar,
            sueldo_mensual_neto = costo.sueldo_mensual_neto,
            complemento_salario_mensual = costo.complemento_salario_mensual,
            sueldo_mensual = costo.sueldo_mensual,
            sueldo_mensual_sdi = costo.sueldo_mensual_sdi,
            total_percepciones_mensual = costo.total_percepciones_mensual,
            impuesto_estatal = costo.impuesto_estatal,
            sar = costo.sar,
            cesantia = costo.cesantia,
            infonavit = costo.infonavit,
            isr= costo.isr,
            lim_inferior = costo.lim_inferior,
            excedente = costo.excedente,
            tasa = costo.tasa,
            impuesto_marginal = costo.impuesto_marginal,
            cuota_fija = costo.cuota_fija,
            impuesto = costo.impuesto,
            subsidio = costo.subsidio,
            total_apoyosbonos_empleadocomp = costo.total_apoyosbonos_empleadocomp,
            total_apoyosbonos_agregcomis = costo.total_apoyosbonos_agregcomis,
            comision_complemeto_salario_bonos = costo.comision_complemeto_salario_bonos,
            total_costo_empresa = costo.total_costo_empresa,
            ingreso_mensual_neto_empleado = costo.ingreso_mensual_neto_empleado,
            complete = costo.complete,
            status_id = costo.status_id,
            seccion = costo.seccion,
            laborados = costo.laborados,
            editado = costo.editado,
            total_prima_vacacional = costo.total_prima_vacacional,
            bono_total = costo.bono_total,
            laborados_imss = costo.laborados_imss,
            sdi_imss = costo.sdi_imss,
        ) for costo in costos]

        #se llama el metodo para pasar todos los datos
        CostoAnterior.objects.bulk_create(volcar_datos)
        print("La tarea ejecuto correctamente")
    else:
        print("No se debe ejecutar la tarea")
    """
    
    usuario = UserDatos.objects.get(user__id=request.user.id)
    periodo = str(datetime.date.today().year)

    fecha_actual = date.today()
    año_actual = str(fecha_actual.year)
    fecha_hace_un_año = fecha_actual - relativedelta(years=1)

    if usuario.tipo.id in [9,10,11]:
        perfiles = Perfil.objects.filter(complete = True, baja=False)
        cantidad = perfiles.count()
        status = Status.objects.filter(complete = True, perfil__baja=False)
        cantidad2 = status.count()
        costo = Costo.objects.filter(complete = True, status__perfil__baja=False)
        cantidad3 = costo.count()
        #vacacion = Vacaciones.objects.filter(complete = True, Q(periodo=año_actual) | Q(periodo=str(fecha_hace_un_año.year)), status__perfil__baja=False)
        vacacion = Vacaciones.objects.filter(
            Q(periodo=año_actual) | Q(periodo=str(fecha_hace_un_año.year)),
            status__perfil__id__in=Perfil.objects.all(),
            complete=True,
        )
        vacacion1 = vacacion.filter(periodo = año_actual) #traingo los de 2024
        vacacion2 = vacacion.filter(periodo = fecha_hace_un_año.year) #traigo los del 2023
        #elimina los perfiles repetidos del periodo actual con el periodo anterio | se queda con el actual 2024
        vacacion3 = vacacion2.exclude(status_id__in=vacacion1.values('status_id'))
        vacacion = vacacion1 | vacacion3
        cantidad4 = vacacion.count()

        economico = Economicos.objects.filter(complete = True, periodo = periodo, status__perfil__baja=False)
        cantidad5 = economico.count()
        bancario = DatosBancarios.objects.filter(complete = True, status__perfil__baja=False)
        cantidad6 = bancario.count()
        #vacaciones = Vacaciones.objects.filter(status__perfil__numero_de_trabajador=usuario.numero_de_trabajador).last()
        vacaciones = Vacaciones.objects.filter(status__perfil__numero_de_trabajador=usuario.numero_de_trabajador).values("total_pendiente").aggregate(vacaciones=Sum('total_pendiente'))['vacaciones']
        economicos = Economicos.objects.filter(status__perfil__numero_de_trabajador=usuario.numero_de_trabajador).last()
        uniformes = Uniforme.objects.filter(orden__status__perfil__numero_de_trabajador=usuario.numero_de_trabajador)
        cantidad_uniformes=0
        #for uniforme in uniformes:
        #    cantidad_ = uniforme.cantidad
        #    cantidad_uniformes = cantidad_uniformes+cantidad
    else:
        perfiles= Perfil.objects.filter(distrito=usuario.distrito,complete=True, baja=False)
        cantidad = perfiles.count()
        status = Status.objects.filter(perfil__distrito=usuario.distrito,complete = True, perfil__baja=False)
        cantidad2 = status.count()
        costo = Costo.objects.filter(status__perfil__distrito=usuario.distrito,complete = True, status__perfil__baja=False)
        cantidad3 = costo.count()
        #vacacion = Vacaciones.objects.filter(status__perfil__distrito=usuario.distrito,complete = True,periodo = periodo, status__perfil__baja=False)
        vacacion = Vacaciones.objects.filter(
            Q(periodo=año_actual) | Q(periodo=str(fecha_hace_un_año.year)),
            status__perfil__id__in=Perfil.objects.filter(distrito = usuario.distrito,complete=True),
            complete=True,
        )
        vacacion1 = vacacion.filter(periodo = año_actual) #traingo los de 2024
        vacacion2 = vacacion.filter(periodo = fecha_hace_un_año.year) #traigo los del 2023
        #elimina los perfiles repetidos del periodo actual con el periodo anterio | se queda con el actual 2024
        vacacion3 = vacacion2.exclude(status_id__in=vacacion1.values('status_id'))
        vacacion = vacacion1 | vacacion3
        cantidad4 = vacacion.count()

        economico = Economicos.objects.filter(status__perfil__distrito=usuario.distrito,complete = True,periodo = periodo, status__perfil__baja=False)
        cantidad5 = economico.count()
        bancario = DatosBancarios.objects.filter(status__perfil__distrito=usuario.distrito,complete = True, status__perfil__baja=False)
        cantidad6 = bancario.count()
        #vacaciones = Vacaciones.objects.filter(status__perfil__numero_de_trabajador=usuario.numero_de_trabajador).last()
        vacaciones = Vacaciones.objects.filter(status__perfil__numero_de_trabajador=usuario.numero_de_trabajador).values("total_pendiente").aggregate(vacaciones=Sum('total_pendiente'))['vacaciones']
        economicos = Economicos.objects.filter(status__perfil__numero_de_trabajador=usuario.numero_de_trabajador).last()
        uniformes = Uniforme.objects.filter(orden__status__perfil__numero_de_trabajador=usuario.numero_de_trabajador)
        cantidad_uniformes=0
        for uniforme in uniformes:
            cantidad = uniforme.cantidad
            cantidad_uniformes = cantidad_uniformes+cantidad
    context = {
        'cantidad': cantidad,
        'cantidad2': cantidad2,
        'cantidad3': cantidad3,
        'cantidad4': cantidad4,
        'cantidad5': cantidad5,
        'cantidad6': cantidad6,
        'vacaciones': vacaciones,
        'economicos': economicos,
        'cantidad_uniformes': cantidad_uniformes,
    }

    return render(request, 'dashboard/dashboard.html', context)
