#from genericpath import exists
#from itertools import count
from proyecto.models import UserDatos, Perfil, Status, Solicitud_economicos, Solicitud_vacaciones, Costo, Catorcenas
from prenomina.models import Prenomina
from prenomina.models import Prenomina
from revisar.models import AutorizarPrenomina, Estado
import datetime 
#from requisiciones.models import Requis
#from user.models import Profile
#Variables globales de usuario
def contadores_processor(request):
    #usuario = UserDatos.objects.get(user=request.user.id)
    #print("ES EL USUARIO LOGUEADO: ",usuario.distrito,usuario.numero_de_trabajador)
    
    #Filtro para evitar problemas al acceder los administradores sin perfil y status
    #Hace una busqueda en la database y si no lo encuentra lo guarda como ninguno y si lo encuentra lo
    #               manda a llamar en forma de get para que sea unico y no mande error
    if not UserDatos.objects.filter(user=request.user.id):
        usuario = None
        usuario_fijo = None
        status_fijo = None
        prenomina_estado = None
    else:
        usuario = UserDatos.objects.get(user=request.user.id)
        usuario_fijo = Perfil.objects.filter(numero_de_trabajador=usuario.numero_de_trabajador, distrito=usuario.distrito)
        if not usuario_fijo:
            usuario_fijo = None
        else:
            usuario_fijo = Perfil.objects.get(numero_de_trabajador=usuario.numero_de_trabajador, distrito=usuario.distrito)
        status_fijo = Status.objects.filter(perfil__numero_de_trabajador = usuario.numero_de_trabajador, perfil__distrito = usuario.distrito)
        if not status_fijo:
            status_fijo = None
        else:
            status_fijo = Status.objects.get(perfil__numero_de_trabajador = usuario.numero_de_trabajador, perfil__distrito = usuario.distrito)
            
                   
        #prenominas - autorizaciones       
        if usuario.tipo.nombre == "Gerencia":
            ahora = datetime.date.today()
            catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
            if usuario.distrito.distrito == 'Matriz':
                costo = Costo.objects.filter(complete=True, status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador")
            else:
                costo = Costo.objects.filter(status__perfil__distrito=usuario.distrito, complete=True,  status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador")

            prenominas_verificadas = Prenomina.objects.filter(empleado__in=costo,autorizarprenomina__tipo_perfil__nombre="Control Tecnico",fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]).distinct()    
            rh = Prenomina.objects.filter(empleado__in=costo, fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]).order_by("empleado__status__perfil__numero_de_trabajador") #Estas son todas las que deben haber en la catorcena
            rh = rh.count()
            ct = prenominas_verificadas.count()
            g = Prenomina.objects.filter(empleado__in=costo,autorizarprenomina__tipo_perfil__nombre="Gerencia",fecha__range=[catorcena_actual.fecha_inicial, catorcena_actual.fecha_final]).distinct()
            g = g.count()
            if rh == ct:
                prenomina_estado = 1 #Ya estan todas revisadas por rh y ct
            if g == rh:
                prenomina_estado = 2 #Ya fueron revisadas todas por gerencia
            else:
                prenomina_estado = 0 #Ninguna de las anteriores
        else:
            prenomina_estado = None
      
    #Solicitudes economicos - Jefe inmediato
    economicos_count = None
    economico_menu = None
    vacaciones_count = None
    
    if usuario_fijo:        
        if usuario.tipo_id == 8 : #Gerente o sudireccion
            solicitudes_economicos = Solicitud_economicos.objects.filter(complete=True, autorizar=None, perfil_gerente_id = usuario_fijo.id)
            economicos_count = solicitudes_economicos.count()
            solicitudes_vacaciones = Solicitud_vacaciones.objects.filter(complete=True, autorizar=None, perfil_id = usuario_fijo.id)
            vacaciones_count = solicitudes_vacaciones.count()
        else:
            solicitudes_economicos = Solicitud_economicos.objects.filter(complete=True, autorizar_jefe=None, perfil_id = usuario_fijo.id)
            economicos_count = solicitudes_economicos.count()
            economico_menu = Solicitud_economicos.objects.filter(complete=True, perfil_id = usuario_fijo.id).exists()
            
            solicitudes_vacaciones = Solicitud_vacaciones.objects.filter(complete=True, autorizar=None, perfil_id = usuario_fijo.id)
            vacaciones_count = solicitudes_vacaciones.count()                      
            
    return {
        'usuario':usuario,
        'usuario_fijo':usuario_fijo,
        'status_fijo':status_fijo,
        'economicos_count':economicos_count,
        'economico_menu': economico_menu,
        'vacaciones_count':vacaciones_count,
        'prenomina_estado':prenomina_estado,
    }
