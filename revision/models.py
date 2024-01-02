from django.db import models
from esquema.models import Solicitud
from proyecto.models import Perfil,TipoPerfil

class Estado(models.Model):
    tipo = models.CharField(max_length=20)
    
    def __str__(self):
        return self.tipo

class autorizacion_solicitudes(models.Model):
    solicitud = models.ForeignKey(Solicitud,on_delete=models.CASCADE)
    perfil = models.OneToOneField(Perfil,on_delete=models.CASCADE) #nombre 
    tipo_perfil = models.OneToOneField(TipoPerfil,on_delete=models.CASCADE)
    estado = models.OneToOneField(Estado,on_delete=models.CASCADE)
    comentario = models.CharField(max_length=255,null=True)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    
