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

# Create your views here.

#Se deshabilito la plantilla
def register(request):
    raise Http404()
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user-login')
    else:
        form = UserForm()
    ctx = {
        'form':form,
        }
    return render(request, 'user/register.html',ctx)

#Se deshabilito la plantilla
def profile(request):
    raise Http404()
    return render(request, 'user/profile.html')

