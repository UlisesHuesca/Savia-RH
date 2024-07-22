from django import forms
from proyecto.models import Perfil, Status, Costo, DatosBancarios, Bonos, Uniformes, Vacaciones, Economicos, DatosISR, TablaVacaciones, Empleados_Batch, Catorcenas
from proyecto.models import Status_Batch, Uniforme, Costos_Batch, Bancarios_Batch, Solicitud_economicos, Solicitud_vacaciones, Vacaciones_anteriores_Batch, Datos_baja
from proyecto.models import Empleado_cv, RegistroPatronal, UserDatos
class PerfilForm(forms.ModelForm): #Matriz
    class Meta:
        model = Perfil
        fields = ['foto','numero_de_trabajador','empresa','distrito','nombres',
                'apellidos','fecha_nacimiento','correo_electronico','proyecto','subproyecto',]
        
class PerfilDistritoForm(forms.ModelForm): #Distrito no pregunta de donde es
    class Meta:
        model = Perfil
        fields = ['foto','numero_de_trabajador','empresa','nombres',
                'apellidos','fecha_nacimiento','correo_electronico','proyecto','subproyecto',]

class PerfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto','empresa','distrito','nombres',
                'apellidos','fecha_nacimiento','correo_electronico','proyecto','subproyecto',]

class BajaEmpleadoForm(forms.ModelForm):
    class Meta:
        model = Datos_baja
        fields = ['fecha','finiquito','liquidacion',
                'motivo','exitosa',]

class BajaEmpleadoUpdate(forms.ModelForm):
    class Meta:
        model = Datos_baja
        fields = ['fecha','finiquito','liquidacion',
                'motivo','exitosa',]

class StatusForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['perfil','puesto','registro_patronal','fecha_ingreso','nss','curp','rfc','profesion',
                'no_cedula','fecha_cedula','nivel','tipo_de_contrato','ultimo_contrato_vence','tipo_sangre',
                'sexo','domicilio','estado_civil','fecha_planta_anterior','fecha_planta','telefono','fecha_alta_imss']

class StatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['registro_patronal','puesto','nss','curp','rfc','profesion','fecha_ingreso',
                'no_cedula','fecha_cedula','nivel','tipo_de_contrato','ultimo_contrato_vence','tipo_sangre',
                'sexo','domicilio','estado_civil','fecha_planta_anterior','fecha_planta','telefono','escuela','lugar_nacimiento',
                'numero_ine','fecha_alta_imss']

class CvAgregar(forms.ModelForm):
    class Meta:
        model = Empleado_cv
        fields = ['fecha_inicio','fecha_fin','puesto',
                'distrito','empresa','comentario',]

class CostoForm(forms.ModelForm):
    class Meta:
        model = Costo
        fields = ['status','amortizacion_infonavit','fonacot','neto_catorcenal_sin_deducciones',
                'complemento_salario_catorcenal','sueldo_diario','apoyo_de_pasajes','laborados',
                'apoyo_vist_familiar','apoyo_salud','estancia','renta','apoyo_estudios','amv','gasolina','campamento','sdi_imss','laborados_imss']


class CostoUpdateForm(forms.ModelForm):
    class Meta:
        model = Costo
        fields = ['amortizacion_infonavit','fonacot','neto_catorcenal_sin_deducciones',
                'complemento_salario_catorcenal','sueldo_diario','apoyo_de_pasajes','laborados',
                'apoyo_vist_familiar','estancia','apoyo_salud','renta','apoyo_estudios','amv','gasolina','campamento','sdi_imss','laborados_imss']

class DatosBancariosForm(forms.ModelForm):
    class Meta:
        model = DatosBancarios
        fields = ['status','no_de_cuenta','numero_de_tarjeta','clabe_interbancaria','banco']

class BancariosUpdateForm(forms.ModelForm):
    class Meta:
        model = DatosBancarios
        fields = ['no_de_cuenta','numero_de_tarjeta','clabe_interbancaria','banco']

class BonosForm(forms.ModelForm):
    class Meta:
        model = Bonos
        fields = ['monto','costo','fecha_bono','comentario',]

class BonosUpdateForm(forms.ModelForm):
    class Meta:
        model = Bonos
        fields = ['monto','fecha_bono','comentario',]

class UniformesForm(forms.ModelForm):
    class Meta:
        model = Uniformes
        fields = ['fecha_pedido']

class UniformeForm(forms.ModelForm):
    class Meta:
        model = Uniforme
        fields = ['ropa','talla','cantidad']

class VacacionesForm(forms.ModelForm):
    class Meta:
        model = Vacaciones
        fields = ['status','fecha_inicio','fecha_fin','comentario', 'dia_inhabil',]

class VacacionesFormato(forms.ModelForm): ###
    class Meta:
        model = Vacaciones
        fields = ['fecha_inicio','fecha_fin', 'dia_inhabil',]

class SolicitudVacacionesForm(forms.ModelForm):
    class Meta:
        model = Solicitud_vacaciones
        fields = ['fecha_inicio','fecha_fin','dia_inhabil','perfil']
        
    def __init__(self, *args, **kwargs):
        #si se necesita agregar el usuario para obtener el distrito y aplicar el filtrado**
        super(SolicitudVacacionesForm, self).__init__(*args, **kwargs)
        # Filtrar las opciones del campo 'perfil'
        self.fields['perfil'].queryset = Perfil.objects.all()

class SolicitudVacacionesUpdateForm(forms.ModelForm):    
    class Meta:
        model = Solicitud_vacaciones
        fields = ['fecha_inicio','fecha_fin','dia_inhabil']

class VacacionesUpdateForm(forms.ModelForm):
    class Meta:
        model = Vacaciones
        fields = ['fecha_inicio', 'fecha_fin', 'comentario', 'dia_inhabil']
        widgets = {
            'comentario': forms.TextInput(attrs={'maxlength': '32'}),
        }

class EconomicosForm(forms.ModelForm):
    class Meta:
        model = Economicos
        fields = ['status','fecha','comentario',]

class EconomicosFormato(forms.ModelForm): ####Borrar
    class Meta:
        model = Economicos
        fields = ['fecha','comentario',]

class SolicitudEconomicosForm(forms.ModelForm):
    class Meta:
        model = Solicitud_economicos
        fields = ['perfil','fecha','comentario',]
    
    def __init__(self, *args, **kwargs):
        #si se necesita agregar el usuario para obtener el distrito y aplicar el filtrado**
        super(SolicitudEconomicosForm, self).__init__(*args, **kwargs)
        # Filtrar las opciones del campo 'perfil'
        self.fields['perfil'].queryset = Perfil.objects.all()
        
class SolicitudEconomicosUpdateForm(forms.ModelForm):

    class Meta:
        model = Solicitud_economicos
        fields = ['fecha','comentario']

class EconomicosUpdateForm(forms.ModelForm):
    class Meta:
        model = Economicos
        fields = ['fecha','comentario',]

class IsrForm(forms.ModelForm):
    class Meta:
        model = DatosISR
        fields = ['liminf','limsup','cuota','excedente',
                 'p_ingresos','g_ingresos','subsidio',]

class Dias_VacacionesForm(forms.ModelForm):
    class Meta:
        model = TablaVacaciones
        fields = ['years','days',]

class Empleados_BatchForm(forms.ModelForm):
    class Meta:
        model = Empleados_Batch
        fields= ['file_name']

class Status_BatchForm(forms.ModelForm):
    class Meta:
        model = Status_Batch
        fields= ['file_name']

class Costos_BatchForm(forms.ModelForm):
    class Meta:
        model = Costos_Batch
        fields= ['file_name']

class Bancarios_BatchForm(forms.ModelForm):
    class Meta:
        model = Bancarios_Batch
        fields= ['file_name']

class CatorcenasForm(forms.ModelForm):
    class Meta:
        model = Catorcenas
        fields = ['catorcena','fecha_inicial','fecha_final',]

class Vacaciones_anteriores_BatchForm(forms.ModelForm):
    class Meta:
        model = Vacaciones_anteriores_Batch
        fields= ['file_name']

class Registro_patronal_form(forms.ModelForm):
    class Meta:
        model = RegistroPatronal
        fields = ['prima_anterior', 'prima']