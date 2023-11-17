from django.db import models

#se importa los modelos de la otra app
from proyecto.models import Distrito,Puesto,Perfil

# Los esquemas de bonos tendran una categoria y subcategorias
class Categoria(models.Model):
    nombre = models.CharField(max_length=100,null=False)
    
    def __str__(self):
        return self.nombre
        
class Subcategoria(models.Model):
    esquema_categoria = models.ForeignKey(Categoria,on_delete=models.CASCADE,null=False)
    nombre = models.CharField(max_length=100,null=False)
    
    def __str__(self):
        return self.nombre

#Este es el esquema que contiene los bonos definidos
class Esquema(models.Model):
    esquema_subcategoria = models.ForeignKey(Subcategoria,on_delete=models.CASCADE,null=False)
    puesto = models.ForeignKey(Puesto,on_delete=models.CASCADE,null=False)
    distrito = models.ForeignKey(Distrito,on_delete=models.CASCADE,null=False)
    importe = models.DecimalField(max_digits=6,decimal_places=2,null=False)#Se filtra la información para no ser mostrada

    def __str__(self):
        return self.esquema_subcategoria

#Quien realiza la solicitud
class Solicitud(models.Model):
    puesto = models.ForeignKey(Puesto,on_delete=models.CASCADE,null=False)
    perfil = models.ForeignKey(Perfil,on_delete=models.CASCADE,null=False)
    distrito = models.ForeignKey(Distrito,on_delete=models.CASCADE,null=False)

#El bono que pasara a revisión
class EsquemaSolicitado(models.Model):
    solicitud = models.ForeignKey(Solicitud,on_delete=models.CASCADE,null=False)
    trabajador = models.ForeignKey(Perfil,on_delete=models.CASCADE,null=False)
    Esquema = models.ForeignKey(Esquema,on_delete=models.CASCADE,null=False)
    cantidad = models.DecimalField(max_digits=6,decimal_places=2,null=False)
    fecha = models.DateTimeField(null=False,auto_now_add=True)
    
#Se definen los tipos de requerimientos que existen para el bono (AST, reporte cronologico...)  
class TipoRequerimiento(models.Model):
    nombre = models.CharField(max_length=100,null=False)
    
#Se pueden subir imagenes o pdf al esquema bono solicitado
class Requerimiento(models.Model):
    tipo_requerimiento = models.ForeignKey(TipoRequerimiento,on_delete=models.CASCADE,null=False)
    esquema_solicitado = models.ForeignKey(EsquemaSolicitado,on_delete=models.CASCADE,null=False)
    fecha = models.DateTimeField(null=False,auto_now_add=True)
    url = models.FileField(upload_to="archivos/",max_length=254)
    
    
    
    
    
    
    
