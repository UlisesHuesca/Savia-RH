from django.db import models
from django.core.validators import FileExtensionValidator

#se importa los modelos de la otra app
from proyecto.models import Distrito,Perfil,Puesto

# Los esquemas de bonos tendran una categoria y subcategorias
class Categoria(models.Model):
    nombre = models.CharField(max_length=100,null=False)
    slug = models.SlugField(unique=True, blank=True)
    
    def __str__(self):
        return self.nombre
        
class Subcategoria(models.Model):
    esquema_categoria = models.ForeignKey(Categoria,on_delete=models.CASCADE,null=False)
    nombre = models.CharField(max_length=100,null=False)
    
    def __str__(self):
        return self.nombre
    
#Este es el esquema que contiene los bonos definidos
class Bono(models.Model):
    esquema_subcategoria = models.ForeignKey(Subcategoria,on_delete=models.CASCADE,null=False)
    puesto = models.ForeignKey(Puesto,on_delete=models.CASCADE,null=False)
    distrito = models.ForeignKey(Distrito,on_delete=models.CASCADE,null=False)
    #cuando el importe es null se considera NA
    importe = models.DecimalField(max_digits=10,decimal_places=2,null=True)

    def __str__(self):
        if self.esquema_subcategoria ==None:
            return "Campo vacio"
        return f'{self.subcategoria.nombre}'
    
#El bono que pasara a revisión
class Solicitud(models.Model):
    folio = models.BigIntegerField(null=False, unique=True)
    #supervisor quien realiza la solicitud
    solicitante = models.ForeignKey(Perfil,on_delete=models.CASCADE,null=False) 
    bono = models.ForeignKey(Subcategoria,on_delete=models.CASCADE,null=False)
    total = models.DecimalField(max_digits=10,decimal_places=2,null=False) 
    fecha = models.DateTimeField(null=False,auto_now_add=True)
    
class BonoSolicitado(models.Model):
    solicitud = models.ForeignKey(Solicitud,on_delete=models.CASCADE,null=False) 
    trabajador = models.ForeignKey(Perfil,on_delete=models.CASCADE,null=False)
    puesto = models.ForeignKey(Puesto,on_delete=models.CASCADE,null=False)
    distrito = models.ForeignKey(Distrito,on_delete=models.CASCADE,null=False)
    cantidad = models.DecimalField(max_digits=10,decimal_places=2,null=False) 
    fecha = models.DateTimeField(null=False,auto_now_add=True)
        
#Se definen los tipos de requerimientos que existen para el bono (AST, reporte cronologico...)  
class TipoRequerimiento(models.Model):
    nombre = models.CharField(max_length=100,null=False)
    
#Se pueden subir imagenes o pdf al esquema bono solicitado
class Requerimiento(models.Model):
    tipo_requerimiento = models.ForeignKey(TipoRequerimiento,on_delete=models.CASCADE,null=False)
    solicitud = models.ForeignKey(Solicitud,on_delete=models.CASCADE,null=False)
    fecha = models.DateTimeField(null=False,auto_now_add=True)
    url = models.FileField(upload_to="archivos/",max_length=254,validators=[FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg','jpeg'])])
    
    
    
    
    
    
    
