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
from user.decorators import perfil_session_seleccionado
locale.setlocale( locale.LC_ALL, '' )

#MUESTRA EL CONTEO DE LOS DATOS DE LAS CARTAS EN EL PANEL DE DASHBOARD
#@login_required(login_url='user-login')
@perfil_session_seleccionado
def index(request):
    context = {}  # Asegura que `context` siempre existe

    try:
        # Obtener el diccionario de la sesión
        userdatos = request.session.get('usuario_datos')
        usuario_tipo = userdatos.get('tipo_id')
        usuario_distrito = userdatos.get('distrito_id')
        usuario_perfil = userdatos.get('perfil_id')
        
        periodo = str(datetime.date.today().year)

        fecha_actual = date.today()
        año_actual = str(fecha_actual.year)
        fecha_hace_un_año = fecha_actual - relativedelta(years=1)

        if usuario_tipo in [9,10,11]:
            cantidad = Perfil.objects.filter(complete = True, baja=False).count()
            cantidad2 = Status.objects.filter(complete = True, perfil__baja=False).count()
            cantidad3 = Costo.objects.filter(complete = True, status__perfil__baja=False).count()
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

            cantidad5 = Economicos.objects.filter(complete = True, periodo = periodo, status__perfil__baja=False).count()
            cantidad6 = DatosBancarios.objects.filter(complete = True, status__perfil__baja=False).count()
            
            vacaciones = Vacaciones.objects.filter(status__perfil__numero_de_trabajador=usuario.numero_de_trabajador).last()
            vacaciones = Vacaciones.objects.filter(status__perfil_id=usuario_perfil).values("total_pendiente").aggregate(vacaciones=Sum('total_pendiente'))['vacaciones'] or 0
            economicos = Economicos.objects.filter(status__perfil_id=usuario_perfil).last()
            uniformes = Uniforme.objects.filter(orden__status__perfil_id=usuario_perfil)
            cantidad_uniformes=0
            for uniforme in uniformes:
                cantidad_ = uniforme.cantidad
                cantidad_uniformes = cantidad_uniformes+cantidad
        else:
            cantidad= Perfil.objects.filter(distrito_id=usuario_distrito,complete=True, baja=False).count()
            cantidad2 = Status.objects.filter(perfil__distrito_id=usuario_distrito,complete = True, perfil__baja=False).count()
            cantidad3 = Costo.objects.filter(status__perfil__distrito_id=usuario_distrito,complete = True, status__perfil__baja=False).count()
            vacacion = Vacaciones.objects.filter(status__perfil__distrito=usuario.distrito,complete = True,periodo = periodo, status__perfil__baja=False)
            vacacion = Vacaciones.objects.filter(
                Q(periodo=año_actual) | Q(periodo=str(fecha_hace_un_año.year)),
                status__perfil__id__in=Perfil.objects.filter(distrito_id = usuario_distrito,complete=True),
                complete=True,
            )
            vacacion1 = vacacion.filter(periodo = año_actual) or 0#traigo los de 2024
            vacacion2 = vacacion.filter(periodo = fecha_hace_un_año.year) or 0 #traigo los del 2023
            #elimina los perfiles repetidos del periodo actual con el periodo anterio | se queda con el actual 2024
            vacacion3 = vacacion2.exclude(status_id__in=vacacion1.values('status_id'))
            vacacion = vacacion1 | vacacion3
            cantidad4 = vacacion.count()

            cantidad5 = Economicos.objects.filter(status__perfil__distrito_id=usuario_distrito,complete = True,periodo = periodo, status__perfil__baja=False).count()
            cantidad6 = DatosBancarios.objects.filter(status__perfil__distrito_id=usuario_distrito,complete = True, status__perfil__baja=False).count()
            vacaciones = Vacaciones.objects.filter(status__perfil__numero_de_trabajador=usuario.numero_de_trabajador).last()
            
            vacaciones = Vacaciones.objects.filter(status__perfil_id=usuario_perfil).values("total_pendiente").aggregate(vacaciones=Sum('total_pendiente'))['vacaciones'] or 0
            economicos = Economicos.objects.filter(status__perfil_id=usuario_perfil).last()
            uniformes = Uniforme.objects.filter(orden__status__perfil_id=usuario_perfil)
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

    except Exception as e:
        print(f"Error en la vista index: {e}")  # Para debug en logs
        context['error'] = "Hubo un problema cargando los datos."

    return render(request, 'dashboard/dashboard.html', context)
