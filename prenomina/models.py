from django.db import models

# Create your models here.
from django.db import models
from proyecto.models import Costo
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

class Prenomina(models.Model):
    empleado = models.ForeignKey(Costo, on_delete = models.CASCADE, null=True)
    fecha = models.DateField(null=True)
    complete = models.BooleanField(default=False) #Este complete es para saber si ya se reviso
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    editado = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return f'Empleado: {self.empleado}, Fecha: {self.fecha}'
    #retardos#castigos#permiso_goce#permiso_sin#descanso#incapacidades
    #faltas#comision #domingo

def validar_size(value):
    filesize = value.size
    #if filesize >  5 * 2048 * 2048:  # 10 MB
    if filesize >  5 * 512 * 512:  # 2.5 MB
        raise ValidationError('El tamaño del archivo no puede ser mayor a 2.5 MB.')    
    
class Retardos(models.Model):
    fecha = models.DateField(null=True)
    prenomina = models.ForeignKey(Prenomina, on_delete = models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    comentario = models.CharField(max_length=100,null=True, blank=True)
    editado = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return f'Retardo: {self.fecha} id prenomina:{self.prenomina}'
    
class Castigos(models.Model):
    fecha = models.DateField(null=True)
    fecha_fin = models.DateField(null=True) #fecha fin
    prenomina = models.ForeignKey(Prenomina, on_delete = models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    comentario = models.CharField(max_length=100,null=True, blank=True)
    url = models.FileField(upload_to="prenomina/",unique=True,null=False,validators=[validar_size,FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg','jpeg'])])
    editado = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return f'Castigo {self.id}: {self.fecha}'
    
class Permiso_goce(models.Model):
    fecha = models.DateField(null=True)
    fecha_fin = models.DateField(null=True) #fecha fin
    prenomina = models.ForeignKey(Prenomina, on_delete = models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    comentario = models.CharField(max_length=100,null=True, blank=True)
    url = models.FileField(upload_to="prenomina/",unique=True,null=False,validators=[validar_size,FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg','jpeg'])])
    editado = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return f'Fecha: {self.fecha} id prenomina:{self.prenomina}'

class Permiso_sin(models.Model):
    fecha = models.DateField(null=True)
    fecha_fin = models.DateField(null=True) #fecha fin
    prenomina = models.ForeignKey(Prenomina, on_delete = models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    comentario = models.CharField(max_length=100,null=True, blank=True)
    url = models.FileField(upload_to="prenomina/",unique=True,null=False,validators=[validar_size,FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg','jpeg'])])
    editado = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return f'Fecha: {self.fecha} id prenomina:{self.prenomina}'
    
class Descanso(models.Model):
    fecha = models.DateField(null=True)
    prenomina = models.ForeignKey(Prenomina, on_delete = models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    comentario = models.CharField(max_length=100,null=True, blank=True)
    editado = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return f'Fecha: {self.fecha} id prenomina:{self.prenomina}'
    
class Incapacidades(models.Model):
    fecha = models.DateField(null=True) #fecha inicio
    fecha_fin = models.DateField(null=True) #fecha fin
    prenomina = models.ForeignKey(Prenomina, on_delete = models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    comentario = models.CharField(max_length=100,null=True, blank=True)
    url = models.FileField(upload_to="prenomina/",unique=True,null=False,validators=[validar_size,FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg','jpeg'])])
    editado = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return f'Fecha: {self.fecha} id prenomina:{self.prenomina}'

class Faltas(models.Model):
    fecha = models.DateField(null=True)
    prenomina = models.ForeignKey(Prenomina, on_delete = models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    comentario = models.CharField(max_length=100,null=True, blank=True)
    editado = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return f'Fecha: {self.fecha} id prenomina:{self.prenomina}'

class Comision(models.Model):
    fecha = models.DateField(null=True)
    prenomina = models.ForeignKey(Prenomina, on_delete = models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    comentario = models.CharField(max_length=100,null=True, blank=True)
    url = models.FileField(upload_to="prenomina/",unique=True,null=False,validators=[validar_size,FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg','jpeg'])])
    editado = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return f'Fecha: {self.fecha} id prenomina:{self.prenomina}'

class Domingo(models.Model):
    fecha = models.DateField(null=True)
    prenomina = models.ForeignKey(Prenomina, on_delete = models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    comentario = models.CharField(max_length=100,null=True, blank=True)
    editado = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return f'Fecha: {self.fecha} id prenomina:{self.prenomina}'

class Dia_extra(models.Model):
    fecha = models.DateField(null=True)
    prenomina = models.ForeignKey(Prenomina, on_delete = models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    comentario = models.CharField(max_length=100,null=True, blank=True)
    url = models.FileField(upload_to="prenomina/",unique=True,null=False,validators=[validar_size,FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg','jpeg'])])
    editado = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return f'Fecha: {self.fecha} id prenomina:{self.prenomina}'