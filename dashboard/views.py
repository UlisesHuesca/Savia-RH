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

    usuario = UserDatos.objects.get(user__id=request.user.id)
    periodo = str(datetime.date.today().year)

    fecha_actual = date.today()
    año_actual = str(fecha_actual.year)
    fecha_hace_un_año = fecha_actual - relativedelta(years=1)

    if usuario.distrito.distrito == 'Matriz':
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
        vacaciones = Vacaciones.objects.filter(status__perfil__numero_de_trabajador=usuario.numero_de_trabajador).last()
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
        vacaciones = Vacaciones.objects.filter(status__perfil__numero_de_trabajador=usuario.numero_de_trabajador).last()
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

@login_required(login_url='user-login')
def mensaje(request):
    if request.method == 'POST':
        subject=request.POST["asunto"]
        message=request.POST["mensaje"] + " " + request.POST["email"]
        email_from=settings.EMAIL_HOST_USER
        recipient_list=["halo-victor45@hotmail.com"]
        send_mail(subject, message, email_from, recipient_list)

        return redirect('index')

    return render(request, 'dashboard/Mensaje.html')

@login_required(login_url='user-login')
def render_report(request, pk):
    catorcena = Catorcenas.objects.filter(catorcena=1).last()
    if catorcena:
        fecha_inicial = catorcena.fecha_inicial
        fecha_final = catorcena.fecha_final

        catorcenas = Catorcenas.objects.filter(Q(catorcena__lte=26) & Q(fecha_inicial__gte=fecha_inicial)).order_by('catorcena')
    else:
        catorcenas = Catorcenas.objects.none()

    costo_ver = Costo.objects.get(id=pk)
    costo = Costo.history.filter((~Q(sueldo_mensual_neto=None) | ~Q(sueldo_mensual_neto=0)), id=pk)

    bonos = []
    for catorcena in catorcenas:
        bono = Bonos.objects.filter(costo=costo_ver, fecha_bono__range=[catorcena.fecha_inicial, catorcena.fecha_final]).aggregate(total=Sum('monto'))
        bonos.append({
            'catorcena': catorcena.catorcena,
            'total': bono['total'] if bono['total'] else 0
        })

    meses_cost = {}
    previous_cost = None

    for catorcena in catorcenas:
        if previous_cost is None:
            cost = Costo.history.filter((~Q(sueldo_mensual_neto=None) | ~Q(sueldo_mensual_neto=0)), id=pk, updated_at__range=[catorcena.fecha_inicial, catorcena.fecha_final]).first()
        else:
            cost = previous_cost

        catorcena_number = catorcena.catorcena
        meses_cost[catorcena_number] = cost.total_costo_empresa if cost else 0
        previous_cost = cost

    datos_tabla = [{'catorcena': catorcena.catorcena, 'costo': costo, 'bono': bono['total'] if bono else Decimal('0.00')}
                   for catorcena, costo, bono in zip(catorcenas, meses_cost.values(), bonos)]
    context = {
        'bonos': bonos,
        'registros': costo,
        'meses_cost': meses_cost,
        'costo_ver': costo_ver,
        'catorcenas':catorcenas,
        'catorcena': catorcena,
        'costo':costo,
        'datos_tabla':datos_tabla
    }

    return render(request, 'dashboard/optional_report.html', context)