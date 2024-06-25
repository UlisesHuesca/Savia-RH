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
        raise ValidationError('El tamaño del archivo no puede ser mayor a 10MB.')    
    
class Incidencia(models.Model):
    tipo = models.CharField(max_length=50, null=False)
    slug = models.CharField(max_length=10, null=True)
    
    def __str__(self):
        return self.tipo
    
class IncidenciaRango(models.Model):
    incidencia = models.ForeignKey(Incidencia, on_delete=models.CASCADE, null=False)
    empleado = models.ForeignKey(Costo, on_delete = models.CASCADE, null=True)
    fecha_inicio = models.DateField(null=False, db_index=True)
    fecha_fin = models.DateField(null=False, db_index=True)
    dia_inhabil = models.ForeignKey(Dia_vacacion, on_delete=models.CASCADE, null=False)
    comentario = models.CharField(max_length=100, null=True)
    soporte = models.FileField(upload_to="prenomina/",unique=True,null=False,validators=[validar_size,FileExtensionValidator(allowed_extensions=['pdf','png','jpg','jpeg','xlsx','xls'])])
    subsecuente = models.BooleanField(null=True, default=None)
    complete = models.BooleanField(default=None,null=True, blank=True) 

class PrenominaIncidencias(models.Model):
    prenomina = models.ForeignKey(Prenomina, on_delete=models.CASCADE, null=False, related_name = "incidencias")
    incidencia = models.ForeignKey(Incidencia, on_delete=models.CASCADE, null=False)    
    incidencia_rango = models.ForeignKey(IncidenciaRango, on_delete=models.CASCADE, null=True, blank=True, related_name='prenominaincidencias')
    fecha = models.DateField(null=False, db_index=True)
    comentario = models.CharField(max_length=100, null=True, blank=True)
    soporte = models.FileField(upload_to="prenomina/",null=True,blank=True,validators=[validar_size,FileExtensionValidator(allowed_extensions=['pdf','png','jpg','jpeg','xlsx','xls'])])    
    complete = models.BooleanField(default=None, null=True, blank=True)
    
    def __str__(self):
        return f"{self.prenomina}, {self.incidencia}, {self.fecha}"

class TipoAguinaldo(models.Model):
    tipo = models.CharField(max_length=50, null=False)

    def __str__(self):
        return self.tipo

class Aguinaldo(models.Model):
    empleado = models.ForeignKey(Costo, on_delete = models.CASCADE, null=True)
    catorcena = models.ForeignKey(Catorcenas, on_delete=models.CASCADE, null=True)
    fecha = models.DateField(null=True,db_index=True)
    monto = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    tipo = models.ForeignKey(TipoAguinaldo, on_delete = models.CASCADE, null=True)
    mes = models.IntegerField(null=True,default=None)#para saber si es 1°, 2° o 3° mes
    complete = models.BooleanField(default=False)#para saber si ya se pago

