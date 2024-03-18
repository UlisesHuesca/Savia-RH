from django import forms
from django.shortcuts import render,get_object_or_404
from proyecto.models import Perfil,UserDatos
from .models import Solicitud,BonoSolicitado,Subcategoria,Puesto,Requerimiento
from revisar.models import AutorizarSolicitudes,Estado
from datetime import datetime


def usuarioLogueado(request):
    usuario = get_object_or_404(UserDatos,user_id = request.user.id)
    return usuario.distrito.id

#ESQUEMA BONOS
class SolicitudForm(forms.ModelForm):
    class Meta:
        model = Solicitud
        fields = ['bono']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #se filtra el bono por la subcategoria - bono varillero
        #self.fields['folio'].widget.attrs['readonly'] = 'readonly'
        self.fields['bono'].queryset = Subcategoria.objects.filter(esquema_categoria_id=1).order_by('nombre')   
    
class BonoSolicitadoForm(forms.ModelForm):
    class Meta:
        model = BonoSolicitado
        fields = ['trabajador','puesto','cantidad']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #se filtra el puesto para el bono varillero
        self.fields['puesto'].queryset = Puesto.objects.all()
        #para que la cantidad no sea editable
        self.fields['cantidad'].widget.attrs['readonly'] = 'readonly'
        #self.fields['cantidad'].widget.attrs['required'] = 'required'
  
class RequerimientoForm(forms.ModelForm):    
    class Meta:
        model = Requerimiento
        fields = ['url']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['url'].widget.attrs['multiple'] = 'multiple'

#REVISION AUTORIZACIONES
class AutorizarSolicitudesUpdateForm(forms.ModelForm):
    class Meta:
        model = AutorizarSolicitudes
        fields = ['comentario']
    
    comentario = forms.CharField(required=False)
    
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #se filtran los estados de las autorizaciones
       
        self.fields['estado'].queryset = Estado.objects.all().order_by('tipo')
    """   
class AutorizarSolicitudesGerenteUpdateForm(forms.ModelForm):
    class Meta:
        model = AutorizarSolicitudes
        fields = ['estado','comentario']
    
    comentario = forms.CharField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #se filtran los estados de las autorizaciones
       
        self.fields['estado'].queryset = Estado.objects.filter(id__in=[1,2,3,]).order_by('tipo')