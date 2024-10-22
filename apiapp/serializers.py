from rest_framework import serializers
from proyecto.models import Perfil, Empresa, Proyecto, SubProyecto, Distrito, Status, Nivel, TablaFestivos

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ['id','empresa']

class DistritoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distrito
        fields = ['id','distrito']

class ProyectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proyecto
        fields = ['proyecto']

class SubProyectoSerializer(serializers.ModelSerializer):
    proyecto = ProyectoSerializer()  # Anidamos el Proyecto para obtener su nombre

    class Meta:
        model = SubProyecto
        fields = ['subproyecto', 'proyecto']

class NivelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nivel
        fields = ['nivel']  # Solo el campo 'nivel'

class StatusSerializer(serializers.ModelSerializer):
    nivel = NivelSerializer()  # Anidar el serializador de Nivel

    class Meta:
        model = Status
        fields = ['nivel']  # Solo queremos el campo 'nivel' en este serializador
    def get_nivel(self, obj):
        # Convertir el nivel a float si es posible, de lo contrario, devolver None
        try:
            return float(obj.nivel.nivel)
        except (ValueError, TypeError):
            return None  #Se puede regresar a return el charfield
        
class PerfilSerializer(serializers.ModelSerializer):
    empresa = EmpresaSerializer()  # Anidamos Empresa para obtener su nombre
    distrito = DistritoSerializer()  # Anidamos Distrito para obtener su nombre
    proyecto = ProyectoSerializer()  # Anidamos Proyecto para obtener su nombre
    subproyecto = SubProyectoSerializer()  # Anidamos SubProyecto para obtener su nombre y el proyecto relacionado
    correo_vordcab = serializers.EmailField(source='usuario.email', read_only=True)  # Campo personalizado para correo de User
    #activo = serializers.BooleanField(source='baja', read_only=True)  # Mapea 'baja' a 'activo'    No necesario como el boleano te dice si baja=True en vez si es activo
    nivel = StatusSerializer(source='status', read_only=True) 

    class Meta:
        model = Perfil
        fields = ['correo_vordcab','baja','numero_de_trabajador', 'empresa', 'distrito', 'division', 'nombres', 'apellidos', 'fecha_nacimiento', 'correo_electronico', 'proyecto', 'subproyecto','nivel',]

class PerfilIngenieriaSerializer(serializers.ModelSerializer):
    empresa = EmpresaSerializer()  # Anidamos Empresa para obtener su nombre
    distrito = DistritoSerializer()  # Anidamos Distrito para obtener su nombre
    correo_vordcab = serializers.EmailField(source='usuario.email', read_only=True)  # Campo personalizado para correo de User
    class Meta:
        model = Perfil
        fields = ['id','correo_vordcab','baja','numero_de_trabajador', 'empresa', 'distrito','nombres', 'apellidos', 'fecha_nacimiento', 'correo_electronico',]

class TablaFestivosSerializer(serializers.ModelSerializer):
    class Meta:
        model = TablaFestivos
        fields = ['id', 'dia_festivo',]  