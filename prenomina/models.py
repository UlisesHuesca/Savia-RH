from django.db import models

# Create your models here.
from django.db import models
from proyecto.models import Costo, Catorcenas, Dia_vacacion
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

class Prenomina(models.Model):
    empleado = models.ForeignKey(Costo, on_delete = models.CASCADE, null=True)
    catorcena = models.ForeignKey(Catorcenas, on_delete=models.CASCADE, null=True)
    complete = models.BooleanField(default=False) #Este complete es para saber si ya se reviso
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    editado = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return f'Empleado: {self.empleado}, Cartocena: {self.catorcena}'
    
def validar_size(value):
    #se utiliza para validar imagenes
    filesize = value.size
    if filesize >  5 * 2048 * 2048:  # 10 MB
    #if filesize >  5 * 512 * 512:  # 2.5 MB
        raise ValidationError('El tamaño del archivo no puede ser mayor a 2.5 MB.')    
    
class Incidencia(models.Model):
    tipo = models.CharField(max_length=50, null=False)
    slug = models.CharField(max_length=10, null=True)
    
    def __str__(self):
        return self.tipo
    
class Rango(models.Model):
    incidencia = models.ForeignKey(Incidencia, on_delete=models.CASCADE, null=False)
    fecha_inicio = models.DateField(null=False, db_index=True)
    fecha_fin = models.DateField(null=False, db_index=True)
    dia_inhabil = models.OneToOneField(Dia_vacacion, on_delete=models.CASCADE, null=False)
    comentario = models.CharField(max_length=100, null=True)
    soporte = models.FileField(upload_to="prenomina/",unique=True,null=False,validators=[validar_size,FileExtensionValidator(allowed_extensions=['pdf','png','jpg','jpeg','xlsx','xls'])])
    complete = models.BooleanField(default=False)

    class Meta:
        abstract = True # no crea una tabla en la BD, es una plantilla
        
class IncapacidadesRango(Rango):
    subsecuente = models.BooleanField(default=False, null=False)
    
    def __str__(self):
        return self.incidencia, self.fecha_inicio, self.fecha_inicio
    
    
class IncidenciasRango(Rango):
    def __str__(self):
        return self.incidencia, self.fecha_inicio, self.fecha_inicio
    
    pass # se pone porque no se requieren más campos

class pagar_incapacidad(models.Model):
    prenomina = models.ForeignKey(Prenomina, on_delete = models.CASCADE, null=False)
    incapacidades_rango = models.ForeignKey(IncapacidadesRango, on_delete=models.CASCADE, null=False)
    dias_pagados = models.IntegerField(null=False)
    subsecuente = models.BooleanField(default=False, null=False)
    complete = models.BooleanField(default=False)
    
    def __str__(self):
        return self.prenomina, self.dias_pagados
    
class PrenominaIncidencias(models.Model):
    prenomina = models.ForeignKey(Prenomina, on_delete=models.CASCADE, null=False, related_name='incidencias')
    incapacidades_rango = models.ForeignKey(IncapacidadesRango, on_delete=models.CASCADE, null=True)
    incidencias_rango = models.ForeignKey(IncidenciasRango, on_delete=models.CASCADE, null=True)
    fecha = models.DateField(null=False, db_index=True)
    comentario = models.CharField(max_length=100, null=True, blank=True)
    incidencia = models.ForeignKey(Incidencia, on_delete=models.CASCADE, null=False)
    soporte = models.FileField(upload_to="prenomina/",null=True,blank=True,validators=[validar_size,FileExtensionValidator(allowed_extensions=['pdf','png','jpg','jpeg','xlsx','xls'])])
    