from django.db import models

# Create your models here.
from django.db import models
from esquema.models import Solicitud
from proyecto.models import Perfil,TipoPerfil
from prenomina.models import Prenomina

class Estado(models.Model):
    tipo = models.CharField(max_length=20)
    
    def __str__(self):
        return self.tipo
    
class AutorizarSolicitudes(models.Model):
    solicitud = models.ForeignKey(Solicitud,on_delete=models.CASCADE,related_name='autorizarsolicitudes')
    perfil = models.ForeignKey(Perfil,on_delete=models.CASCADE) #nombre 
    tipo_perfil = models.ForeignKey(TipoPerfil,on_delete=models.CASCADE)
    estado = models.ForeignKey(Estado,on_delete=models.CASCADE)
    comentario = models.CharField(max_length=255,null=True)
    revisar = models.BooleanField(default=False)#flujo revisión
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    
class AutorizarPrenomina(models.Model):
    prenomina = models.ForeignKey(Prenomina,on_delete=models.CASCADE,null=True)
    perfil = models.ForeignKey(Perfil,on_delete=models.CASCADE,null=True) #nombre 
    tipo_perfil = models.ForeignKey(TipoPerfil,on_delete=models.CASCADE,null=True)
    estado = models.ForeignKey(Estado,on_delete=models.CASCADE,null=True)
    comentario = models.CharField(max_length=255,null=True)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)