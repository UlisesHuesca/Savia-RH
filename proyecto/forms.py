from django import forms
from proyecto.models import Perfil, Status, Costo, DatosBancarios, Bonos, Uniformes, Vacaciones, Economicos, DatosISR, TablaVacaciones, Empleados_Batch, Catorcenas, Proyecto, SubProyecto
from proyecto.models import Status_Batch, Uniforme, Costos_Batch, Bancarios_Batch, Solicitud_economicos, Solicitud_vacaciones, Temas_comentario_solicitud_vacaciones, Vacaciones_anteriores_Batch

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto','numero_de_trabajador','empresa','distrito','nombres',
                'apellidos','fecha_nacimiento','correo_electronico','proyecto','subproyecto',]

class PerfilDistritoForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto','numero_de_trabajador','empresa','nombres',
                'apellidos','fecha_nacimiento','correo_electronico','proyecto','subproyecto',]

class PerfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto','empresa','distrito','nombres',
                'apellidos','fecha_nacimiento','correo_electronico','proyecto','subproyecto',]

class StatusForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['perfil','puesto','registro_patronal','fecha_ingreso','nss','curp','rfc','profesion',
                'no_cedula','nivel','tipo_de_contrato','ultimo_contrato_vence','tipo_sangre',
                'sexo','domicilio','estado_civil','fecha_planta_anterior','fecha_planta','telefono',]

class StatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['registro_patronal','puesto','nss','curp','rfc','profesion','fecha_ingreso',
                'no_cedula','nivel','tipo_de_contrato','ultimo_contrato_vence','tipo_sangre',
                'sexo','domicilio','estado_civil','fecha_planta_anterior','fecha_planta','telefono',]

class CostoForm(forms.ModelForm):
    class Meta:
        model = Costo
        fields = ['status','amortizacion_infonavit','fonacot','neto_catorcenal_sin_deducciones',
                'complemento_salario_catorcenal','sueldo_diario','apoyo_de_pasajes','laborados',
                'apoyo_vist_familiar','estancia','renta','apoyo_estudios','amv','gasolina','campamento',]


class CostoUpdateForm(forms.ModelForm):
    class Meta:
        model = Costo
        fields = ['amortizacion_infonavit','fonacot','neto_catorcenal_sin_deducciones',
                'complemento_salario_catorcenal','sueldo_diario','apoyo_de_pasajes','laborados',
                'apoyo_vist_familiar','estancia','renta','apoyo_estudios','amv','gasolina','campamento',]

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
        fields = ['fecha_inicio','fecha_fin', 'dia_inhabil',]

class SolicitudVacacionesUpdateForm(forms.ModelForm):
    AUTORIZACION_CHOICES = (
        ('Yes', 'Si'),
        ('No', 'No'),
    )

    autorizar = forms.TypedChoiceField( #definir como TypedChoiceField en vez de ChoiceField, 
        choices=AUTORIZACION_CHOICES, #lo que permite agregar un argumento adicional llamado coerce 
        coerce=lambda x: x == 'Yes', #para realizar la conversión deseada del valor del campo.
        widget=forms.Select(attrs={'class': 'form-control'})
    ) #selecciona 'Yes', se convierte en True, y cuando selecciona 'No', se convierte en False.
    
    class Meta:
        model = Solicitud_vacaciones
        fields = ['fecha_inicio','fecha_fin', 'dia_inhabil','autorizar',]

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
        fields = ['fecha','comentario',]
class SolicitudEconomicosUpdateForm(forms.ModelForm):
    AUTORIZACION_CHOICES = (
        ('Yes', 'Si'),
        ('No', 'No'),
    )
    
    autorizar = forms.TypedChoiceField( #definir como TypedChoiceField en vez de ChoiceField, 
        choices=AUTORIZACION_CHOICES, #lo que permite agregar un argumento adicional llamado coerce 
        coerce=lambda x: x == 'Yes', #para realizar la conversión deseada del valor del campo.
        widget=forms.Select(attrs={'class': 'form-control'})
    ) #selecciona 'Yes', se convierte en True, y cuando selecciona 'No', se convierte en False.
    class Meta:
        model = Solicitud_economicos
        fields = ['fecha','comentario','autorizar',]

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