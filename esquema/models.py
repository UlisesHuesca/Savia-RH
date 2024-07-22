from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

#se importa los modelos de la otra app
from proyecto.models import Distrito,Perfil

#Se crea el puesto para los bonos
class Puesto(models.Model):
    puesto = models.CharField(max_length=200,null=False)
    
    def __str__(self):
        return self.puesto
    
# Los esquemas de bonos tendran una categoria y subcategorias
class Categoria(models.Model):
    nombre = models.CharField(max_length=100,null=False)
    slug = models.SlugField(unique=True, blank=True)
    
    def __str__(self):
        return self.nombre
        
class Subcategoria(models.Model):
    esquema_categoria = models.ForeignKey(Categoria,on_delete=models.CASCADE,null=False)
    nombre = models.CharField(max_length=100,null=False)
    soporte = models.CharField(max_length=250,null=True, blank = True)
    
    def __str__(self):
        return self.nombre
    
#Este es el esquema que contiene los bonos definidos
class Bono(models.Model):
    esquema_subcategoria = models.ForeignKey(Subcategoria,on_delete=models.CASCADE,null=False)
    puesto = models.ForeignKey(Puesto,on_delete=models.CASCADE,null=False)
    distrito = models.ForeignKey(Distrito,on_delete=models.CASCADE,null=False)
    #cuando el importe es null se considera NA
    importe = models.DecimalField(max_digits=10,decimal_places=2,null=True, blank=True)

    def __str__(self):
        if self.esquema_subcategoria is None:
            return "Campo vacío"
        return f'{self.esquema_subcategoria.nombre}'
    
#El bono que pasara a revisión
class Solicitud(models.Model):
    id = models.BigIntegerField(primary_key=True)
    folio = models.BigIntegerField(null=False, unique=True)
    #supervisor quien realiza la solicitud
    solicitante = models.ForeignKey(Perfil,on_delete=models.CASCADE,null=False) 
    bono = models.ForeignKey(Subcategoria,on_delete=models.CASCADE,null=True)#hacerlo nulo para relacionar con la foto
    total = models.DecimalField(max_digits=10,decimal_places=2,null=False) 
    fecha = models.DateTimeField(null=False,auto_now_add=True)
    complete_bono = models.BooleanField(default=False)
    complete_requerimiento = models.BooleanField(default=False)
    complete = models.BooleanField(default=False)
    fecha_autorizacion = models.DateTimeField(null=True,auto_now_add=False)
    
class BonoSolicitado(models.Model):
    solicitud = models.ForeignKey(Solicitud,on_delete=models.CASCADE,null=False) 
    trabajador = models.ForeignKey(Perfil,on_delete=models.CASCADE,null=False)
    puesto = models.ForeignKey(Puesto,on_delete=models.CASCADE,null=False)
    distrito = models.ForeignKey(Distrito,on_delete=models.CASCADE,null=False)
    cantidad = models.DecimalField(max_digits=10,decimal_places=2,null=False) 
    fecha = models.DateTimeField(null=False,auto_now_add=True, db_index=True)

def validar_size(value):
    filesize = value.size
    if filesize >  5 * 2048 * 2048:  # 10 MB
    #if filesize >  5 * 512 * 512:  # 2.5 MB
        raise ValidationError('El tamaño del archivo no puede ser mayor a 2.5 MB.')    
    
    
#Se pueden subir imagenes o pdf al esquema bono solicitado - Es el soporte del bono es decir los archivos PDF e Imagenes
class Requerimiento(models.Model):
    solicitud = models.ForeignKey(Solicitud,on_delete=models.CASCADE,null=False)
    fecha = models.DateTimeField(null=False,auto_now_add=True)
    url = models.FileField(upload_to="bonos/",unique=True,null=False,validators=[validar_size,FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg','jpeg','xls', 'xlsx'])])