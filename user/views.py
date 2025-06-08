from django.shortcuts import render, redirect
#Estamos importando la "Form" de default de Django para crear usuarios
#from django.contrib.auth.forms import UserCreationForm
from .forms import UserForm
from django.contrib.auth.views import LoginView
from .forms import CustomLoginForm
from django.contrib.auth.views import PasswordResetView
from django.conf import settings
import os
from django.http import Http404
from django.shortcuts import render
from user.forms import UserDatosForm
from proyecto.models import UserDatos
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse

# Create your views here.

#Se deshabilito la plantilla
def register(request):
    raise Http404()

#Se deshabilito la plantilla
def profile(request):
    raise Http404()

@login_required(login_url='user-login')
def seleccionar_perfil(request):
    #obtener los perfiles del usuario
    user = request.user.id
    print('user:',user)
    roles = UserDatos.objects.filter(perfil_id = user, activo=True)
    print('roles:', roles)
      
    if request.method == 'POST': 
        print('request:',request)
        rol_id = request.POST.get('user_datos')
        print('view_rol_id:',rol_id)
        try:
            rol = UserDatos.objects.get(id = rol_id)
            
            # Se crea la sesión y se almacena los datos en la sesión
            request.session['selected_rol_id'] = rol.id
            
            return redirect('index')
        
        except Exception as e:
            messages.error(request, 'El perfil seleccionado no es válido')
            return redirect('seleccionar-perfil')
    else:
        form = UserDatosForm()
        form.fields['user_datos'].queryset = roles
            
    context = {
        'form':form,
    }
    
    return render(request, 'user/seleccionar_perfil.html', context)




