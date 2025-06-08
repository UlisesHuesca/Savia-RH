#from genericpath import exists
#from itertools import count
from proyecto.models import UserDatos, Perfil, Status, Solicitud_economicos, Solicitud_vacaciones, Costo, Catorcenas, TipoPerfil
from prenomina.models import Prenomina
from revisar.models import AutorizarPrenomina, Estado, AutorizarSolicitudes
import datetime
from django.db.models import Q 
from django.contrib.auth import logout
#from requisiciones.models import Requis
#from user.models import Profile
#Variables globales de usuario
def contadores_processor(request):
    
    #Filtro para evitar problemas al acceder los administradores sin perfil y status
    #Hace una busqueda en la database y si no lo encuentra lo guarda como ninguno y si lo encuentra lo
    #manda a llamar en forma de get para que sea unico y no mande error
    # Obtener el diccionario de la sesión
    rol_id = request.session.get('selected_rol_id')
    print('rol_id:',rol_id)
  
        
        
        
    try:
        rol = UserDatos.objects.get(id = rol_id)
        print(f"🔹 Rol encontrado: {rol}")  # Debug
    except UserDatos.DoesNotExist:
        rol = None
        print("❌ Rol no encontrado, se asigna None")  # Debug

    #if pk_rol is not None:
        #rol = .get('usuario_id')
        #usuario_tipo = userdatos.get('tipo_id')
        #usuario_distrito = userdatos.get('distrito_id')
        #usuario_perfil = userdatos.get('perfil_id')
        #usuario_rol = userdatos.get("rol")
    #else:
        #usuario_tipo = None
        #usuario_distrito = None
        #usuario_perfil = None
        #usuario_rol = None
    #usuario = UserDatos.objects.get(pk = 3)
    bonos_count = 0
    #if not UserDatos.objects.filter(user=request.user.id):
    #if rol is None:
    #    usuario = None
    #    usuario_fijo = None
    #    status_fijo = None
    #    prenomina_estado = None
    #else:
    #    usuario = UserDatos.objects.get(pk = usuario_id)
    #    usuario_fijo = Perfil.objects.filter(pk = usuario_perfil)
            
    if not rol:
        perfil_usuario = None
        status_usuario = None
        prenomina_estado = None
    else:
        #Antes usuario_fjo
        perfil_usuario = Perfil.objects.get(id = rol.perfil.id)
        #Antes status_fijo
        status_usuario = Status.objects.filter(perfil = perfil_usuario)
        tipo_perfil = TipoPerfil.objects.get(id = rol.tipo.id)
        #if not status_fijo:
            #status_fijo = None
        #else:
            #status_fijo = Status.objects.get(perfil__id = usuario_fijo)
                
        #bonos autorizaciones
        if tipo_perfil in [5,4]: #❌ Este hardcoding es una marranada, arreglar 
            #perfil = Perfil.objects.filter(numero_de_trabajador = usuario.numero_de_trabajador,distrito_id = usuario.distrito.id).values_list('id',flat=True)
            bonos_count = AutorizarSolicitudes.objects.filter(solicitud__solicitante = perfil_usuario, estado_id = 4, solicitud__distrito = rol.distrito ).count()
        if tipo_perfil in [6,7,8,12]: #❌ Este hardcoding es una marranada, arreglar 
            bonos_count = AutorizarSolicitudes.objects.filter(perfil_id = perfil_usuario, estado_id = 3, solicitud__distrito = rol.distrito).count()
                
            
        #prenominas - autorizaciones       
        if tipo_perfil in [8,9,10,11]:#GE, SU ADMIN, SU RH, SU Nomina #❌ Este hardcoding es una marranada, arreglar 
            ahora = datetime.date.today()
            catorcena_actual = Catorcenas.objects.filter(fecha_inicial__lte=ahora, fecha_final__gte=ahora).first()
            if tipo_perfil in [9,10,11]: #❌ Este hardcoding es una marranada, arreglar 
                costo = Costo.objects.filter(complete=True, status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador").values_list('id', flat=True)
            else:
                costo = Costo.objects.filter(status__perfil__distrito= rol.distrito, complete=True,  status__perfil__baja=False).order_by("status__perfil__numero_de_trabajador").values_list('id', flat=True)

            prenominas_verificadas = Prenomina.objects.filter(empleado__in=costo,autorizarprenomina__tipo_perfil__nombre="Control Tecnico",catorcena_id = catorcena_actual.id).distinct()    
            rh = Prenomina.objects.filter(empleado__in=costo, catorcena_id = catorcena_actual.id).order_by("empleado__status__perfil__numero_de_trabajador") #Estas son todas las que deben haber en la catorcena
            rh = rh.count()
            ct = prenominas_verificadas.count()
            g = Prenomina.objects.filter(empleado__in=costo,autorizarprenomina__tipo_perfil__nombre="Gerencia",catorcena_id = catorcena_actual.id).distinct()
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
    vacacion_menu = None
        
    if perfil_usuario:        
        if perfil_usuario == 8 : #Gerente o sudireccion
            solicitudes_economicos = Solicitud_economicos.objects.filter(complete=True, autorizar=None, perfil_gerente = perfil_usuario)
            economico_menu = Solicitud_economicos.objects.filter(complete=True, perfil_gerente = perfil_usuario).exists()
            economicos_count = solicitudes_economicos.count()
                
            solicitudes_vacaciones = Solicitud_vacaciones.objects.filter(complete=True, autorizar=None, perfil_gerente = perfil_usuario)
            vacaciones_count = solicitudes_vacaciones.count()
            vacacion_menu = Solicitud_vacaciones.objects.filter(complete=True, perfil_gerente = perfil_usuario).exists()
            
        else:
            solicitudes_economicos = Solicitud_economicos.objects.filter(complete=True, autorizar_jefe=None, perfil = perfil_usuario)
            economicos_count = solicitudes_economicos.count()
            economico_menu = Solicitud_economicos.objects.filter(complete=True, perfil = perfil_usuario).exists()
                
            solicitudes_vacaciones = Solicitud_vacaciones.objects.filter(complete=True, autorizar_jefe=None, perfil = perfil_usuario)
            vacacion_menu = Solicitud_vacaciones.objects.filter(complete=True, perfil = perfil_usuario).exists()
            vacaciones_count = solicitudes_vacaciones.count()                      
                
    return {
        'usuario': rol,
        'usuario_fijo': perfil_usuario,
        'status_fijo': status_usuario,
        'economicos_count':economicos_count,
        'economico_menu': economico_menu,
        'vacacion_menu':  vacacion_menu , 
        'vacaciones_count':vacaciones_count,
        'prenomina_estado':prenomina_estado,
        'bonos_count':bonos_count
    }
        
    #except Exception as e:
    #    print(f"❌ Error en contadores_processor: {e}")  # Debug
    #    logout(request)
    #    return {}  # 🔹 Siempre retorna un diccionario válido