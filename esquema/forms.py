from django import forms
from django.shortcuts import render,get_object_or_404
from proyecto.models import Perfil,UserDatos
from .models import Solicitud,BonoSolicitado,Subcategoria,Puesto

def usuarioLogueado(request):
    usuario = get_object_or_404(UserDatos,user_id = request.user.id)
    return usuario.distrito.id

class SolicitudForm(forms.ModelForm):
    class Meta:
        model = Solicitud
        fields = ['bono']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #se filtra el bono por la subcategoria - bono varillero
        self.fields['bono'].queryset = Subcategoria.objects.filter(esquema_categoria_id=1).order_by('nombre')   
    
class BonoSolicitadoForm(forms.ModelForm):
    class Meta:
        model = BonoSolicitado
        fields = ['trabajador','puesto','cantidad']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #se filtra el puesto para el bono varillero
        self.fields['puesto'].queryset = Puesto.objects.filter(pk__in=[176,177,178,138])
  
    
    