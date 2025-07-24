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
    user_id = request.user.id
    #print('user:',user_id)
    roles = UserDatos.objects.filter(perfil__usuario__id = user_id, activo=True)
    #print('roles:', roles)
      
    if request.method == 'POST': 
        #print('request:',request)
        pk = request.POST.get('user_datos')
        request.session['selected_rol_id'] = pk        
        return redirect('index')
        
    else:
        form = UserDatosForm()
        form.fields['user_datos'].queryset = roles
            
    context = {
        'form':form,
        'roles': roles,
    }
    
    return render(request, 'user/seleccionar_perfil.html', context)




