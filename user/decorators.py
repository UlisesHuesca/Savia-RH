from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
#from 

# Decorador personalizado para verificar si el usuario está autenticado
def perfil_session_seleccionado(view_func):
    #@wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Verifica si el usuario está autenticado
        if not request.user.is_authenticated:
             return redirect('user-login') 
           
        # Aqui lo manda a seleccionar el perfil sino hay seleccionado el rol
        rol = request.session.get('selected_rol_id')  
        #print(rol)  
        if not rol:
            return redirect('seleccionar-perfil')
        
        #try:
        #    selected_profile = UserDatos.objects.get(id = selected_profile_id)
        #except ObjectDoesNotExist:
        #    logger.warning(f"Perfil con ID {selected_profile_id} no encontrado. Redirigiendo a selección de perfil.")
        #    return redirect('select-profile')  # Redirige si el perfil no existe
        #Continua a la siguente vista
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view