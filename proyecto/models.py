from django.db import models
from django.db.models import F, Sum
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords

 #Tabla de vacaciones
class TablaVacaciones(models.Model):
    years = models.IntegerField(null=True)
    days = models.IntegerField(null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'Años: {self.years}, dias de vacaciones: {self.days}'

class TablaFestivos(models.Model):
    dia_festivo = models.DateField(null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.dia_festivo}'

class Empresa(models.Model):
    empresa = models.CharField(max_length=50,null=True)
    complete = models.BooleanField(default=False)
    logo = models.ImageField(blank=True, upload_to="logo/")

    @property
    def logoURL(self):
        try:
            url = self.logo.url
        except:
            url = ''
        return url


    def __str__(self):
        return f'{self.empresa}'

class Puesto(models.Model):
    puesto = models.CharField(max_length=50,null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.puesto}'

class Distrito(models.Model):
    distrito = models.CharField(max_length=20,null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.distrito}'


class Proyecto(models.Model):
    proyecto = models.CharField(max_length=50,null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.proyecto}'

class SubProyecto(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete = models.CASCADE, null=True)
    subproyecto = models.CharField(max_length=50,null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.subproyecto}'

class Contrato(models.Model):
    contrato = models.CharField(max_length=50,null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.contrato}'

class Sangre(models.Model):
    sangre = models.CharField(max_length=50,null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.sangre}'

class Sexo(models.Model):
    sexo = models.CharField(max_length=50,null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.sexo}'

class Civil(models.Model):
    estado_civil = models.CharField(max_length=50,null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.estado_civil}'

class Banco(models.Model):
    banco = models.CharField(max_length=50,null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.banco}'

class RegistroPatronal(models.Model):
    patronal = models.CharField(max_length=50,null=True)
    empresa = models.ForeignKey(Empresa, on_delete = models.CASCADE, null=True)
    prima_anterior = models.DecimalField(max_digits=8, decimal_places=5,null=True, default=0)
    prima = models.DecimalField(max_digits=8, decimal_places=5,null=True, default=0)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.patronal}'


    #Tabla ISR
class DatosISR(models.Model):
    liminf = models.DecimalField(max_digits=14, decimal_places=2,null=True)
    limsup = models.DecimalField(max_digits=14, decimal_places=2,null=True)
    cuota = models.DecimalField(max_digits=14, decimal_places=2,null=True)
    excedente = models.DecimalField(max_digits=14, decimal_places=4,null=True)
    p_ingresos = models.DecimalField(max_digits=14, decimal_places=2,null=True)
    g_ingresos = models.DecimalField(max_digits=14, decimal_places=2,null=True)
    subsidio = models.DecimalField(max_digits=14, decimal_places=2,null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        if self.complete == False:
            return "Campo vacio"
        return f'{self.liminf} - {self.limsup} - {self.cuota} - {self.excedente} - {self.p_ingresos} - {self.g_ingresos} - {self.subsidio}'

class TipoPerfil(models.Model): #Boleanos para filtrar lo que puede hacer cada usuario
    nombre = models.CharField(max_length=50,null=True)
    admin = models.BooleanField(null=True, default=False) #RH
    usuario = models.BooleanField(null=True, default=False)
    empleados = models.BooleanField(null=True, default=False) #Perfil Status_
    autorizacion = models.BooleanField(null=True, default=False)
    tablas_empleados = models.BooleanField(null=True, default=False) #Datos bancarios a economicos
    info_general = models.BooleanField(null=True, default=False)
    solicitudes = models.BooleanField(null=True, default=False)

    def __str__(self):
        return f'{self.nombre}, admin: {self.admin} '

class UserDatos(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    distrito = models.ForeignKey(Distrito, on_delete = models.CASCADE, null=True)
    tipo = models.ForeignKey(TipoPerfil, on_delete = models.CASCADE, null=True)
    numero_de_trabajador = models.IntegerField(null=True,blank=True)
    distrito = models.ForeignKey(Distrito, on_delete = models.CASCADE, null=True,blank=True)

    def __str__(self):
        return f'{self.user}, distrito: {self.distrito} '

class Perfil(models.Model):
    foto = models.ImageField(null=True, blank=True, upload_to="perfil/")
    numero_de_trabajador = models.IntegerField(null=True)
    empresa = models.ForeignKey(Empresa, on_delete = models.CASCADE, null=True)
    distrito = models.ForeignKey(Distrito, on_delete = models.CASCADE, null=True)
    division = models.CharField(max_length=15,blank=True)
    nombres = models.CharField(max_length=50,null=True)
    apellidos = models.CharField(max_length=50,null=True)
    fecha_nacimiento = models.DateField(null=True)
    correo_electronico = models.EmailField(max_length=50)
    proyecto = models.ForeignKey(Proyecto, on_delete = models.CASCADE, null=True)
    subproyecto = models.ForeignKey(SubProyecto, on_delete = models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    baja = models.BooleanField(default=False)
    complete_status = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    history = HistoricalRecords(history_change_reason_field=models.TextField(null=True))
    editado = models.CharField(max_length=50,blank=True)

    class Meta:
        unique_together = ('numero_de_trabajador', 'distrito',)

    @property
    def costo_empleado(self):
        costos_perfil = self.status_set.all()
        total =  sum([costo.get_costo for costo in costos_perfil])
        return total
    
    @property
    def fotoURL(self):
        try:
            url = self.foto.url
        except:
            url = ''
        return url


    def __str__(self):
        if self.complete == False:
            return "Campo vacio"
        return f'{self.nombres} {self.apellidos}' or ''

 #Tabla de vacaciones
class Nivel(models.Model):
    nivel = models.IntegerField(null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.nivel}'

class Dia_vacacion(models.Model):
    nombre = models.CharField(max_length=50,null=True)
    numero = models.IntegerField(null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.nombre}'

class Status(models.Model):
    perfil = models.ForeignKey(Perfil, on_delete = models.CASCADE, null=True)
    registro_patronal = models.ForeignKey(RegistroPatronal, on_delete = models.CASCADE, null=True)
    nss = models.CharField(max_length=50,null=True)
    curp = models.CharField(max_length=50,null=True)
    rfc = models.CharField(max_length=50,null=True)
    telefono = models.CharField(max_length=50,null=True,blank=True, default='NR')
    profesion = models.CharField(max_length=100,null=True) #Aumentado a 100
    no_cedula = models.CharField(max_length=50,null=True)
    escuela = models.CharField(max_length=100,null=True, blank=True) #Agregado
    lugar_nacimiento = models.CharField(max_length=50,null=True, blank=True) #Agregado
    numero_ine = models.CharField(max_length=50,null=True,blank=True) #Agregado
    fecha_cedula = models.DateField(null=True, blank=True)
    nivel = models.ForeignKey(Nivel, on_delete = models.CASCADE, null=True)
    tipo_de_contrato = models.ForeignKey(Contrato, on_delete = models.CASCADE, null=True)
    ultimo_contrato_vence = models.DateField(null=True)
    tipo_sangre = models.ForeignKey(Sangre, on_delete = models.CASCADE, null=True)
    sexo = models.ForeignKey(Sexo, on_delete = models.CASCADE, null=True)
    domicilio = models.CharField(max_length=100,null=True)
    estado_civil = models.ForeignKey(Civil, on_delete = models.CASCADE, null=True)
    fecha_planta_anterior = models.DateField(null=True, blank=True)
    fecha_planta = models.DateField(null=True, blank=True)
    fecha_ingreso = models.DateField(null=True,blank=True)
    puesto = models.ForeignKey(Puesto, on_delete = models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    complete_costo = models.BooleanField(default=False)
    complete_bancarios = models.BooleanField(default=False)
    complete_vacaciones = models.BooleanField(default=False)
    complete_uniformes = models.BooleanField(default=False)
    complete_economicos = models.BooleanField(default=False)
    history = HistoricalRecords(history_change_reason_field=models.TextField(null=True))
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    editado = models.CharField(max_length=50,blank=True)

    @property
    def get_costo(self):
        costos = self.costo_set.filter(complete=True)
        total =  sum([costo.total_costo_empresa for costo in costos])
        return total

    def __str__(self):
        if self.perfil ==None:
            return "Campo vacio"
        return f'{self.perfil.nombres} {self.perfil.apellidos}' or ''

class DatosBancarios(models.Model):
    status = models.ForeignKey(Status, on_delete = models.CASCADE, null=True)
    no_de_cuenta = models.CharField(max_length=35,null=True)
    numero_de_tarjeta = models.CharField(max_length=35,null=True,blank=True)
    clabe_interbancaria = models.CharField(max_length=35,null=True)
    banco = models.ForeignKey(Banco, on_delete = models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    history = HistoricalRecords(history_change_reason_field=models.TextField(null=True))
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    editado = models.CharField(max_length=50,blank=True)

    def __str__(self):
        if self.status ==None:
            return "Campo vacio"
        return f'{self.status.perfil.nombres} {self.status.perfil.apellidos}'


    #Para el calculo utilizando la fecha de ingreso
class FactorIntegracion(models.Model):
    years = models.IntegerField(null=True)
    factor = models.DecimalField(max_digits=10, decimal_places=6,null=True, default=0)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'Años: {self.years}, factor: {self.factor}'

class TablaCesantia(models.Model):
    sbc = models.DecimalField(max_digits=8, decimal_places=2,null=True, default=0)
    sbc2 = models.DecimalField(max_digits=8, decimal_places=2,null=True, default=0)
    cuota_patronal = models.DecimalField(max_digits=8, decimal_places=6,null=True, default=0)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'SBC del asegurado: {self.sbc}-{self.sbc2}, %Cuota patronal: {self.cuota_patronal}'

class SalarioDatos(models.Model):
    UMA = models.DecimalField(max_digits=10, decimal_places=2,null=True, default=0)
    Salario_minimo = models.DecimalField(max_digits=10, decimal_places=2,null=True, default=0)

    def __str__(self):
        return f'Salario minimo {self.Salario_minimo}, UMA: {self.UMA}'

class Costo(models.Model):
    #Independientes (formulario)
    status = models.ForeignKey(Status, on_delete = models.CASCADE, null=True)
    laborados = models.IntegerField(null=True, default=0)
    seccion = models.CharField(max_length=50,null=True)
    amortizacion_infonavit = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    fonacot = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    neto_catorcenal_sin_deducciones = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    complemento_salario_catorcenal = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    sueldo_diario = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    sdi = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    apoyo_de_pasajes = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    imms_obrero_patronal = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    apoyo_vist_familiar = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    estancia = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    renta = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    apoyo_estudios = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    amv = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    gasolina = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    campamento = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    #Dependientes
    total_deduccion = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    neto_pagar = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    sueldo_mensual_neto = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    complemento_salario_mensual = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    sueldo_mensual = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    sueldo_mensual_sdi = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    total_percepciones_mensual = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    impuesto_estatal = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    sar = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    cesantia = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    infonavit = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    isr = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    lim_inferior = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    excedente = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    tasa = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    impuesto_marginal = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    cuota_fija = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    impuesto = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    subsidio = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    total_apoyosbonos_empleadocomp = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    #Variables
    total_apoyosbonos_agregcomis = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    comision_complemeto_salario_bonos = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    total_costo_empresa = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    ingreso_mensual_neto_empleado = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    #Otros
    created_at=models.DateField(auto_now_add=True)
    updated_at=models.DateField(auto_now=True)
    complete = models.BooleanField(default=False)
    history = HistoricalRecords(history_change_reason_field=models.TextField(null=True))
    editado = models.CharField(max_length=50,blank=True)

    def __str__(self):
        if self.status ==None:
            return "Campo vacio"
        return f'{self.status.perfil.numero_de_trabajador} {self.status.perfil.nombres} {self.status.perfil.apellidos}'

class Bonos(models.Model):
    costo = models.ForeignKey(Costo, on_delete = models.CASCADE, null=True)
    datosbancarios = models.ForeignKey(DatosBancarios, on_delete = models.CASCADE, null=True)
    monto = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    fecha_bono = models.DateField(null=True)
    mes_bono = models.DateField(null=True)
    comentario = models.CharField(max_length=15,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    complete = models.BooleanField(default=False)
    history = HistoricalRecords(history_change_reason_field=models.TextField(null=True))
    editado = models.CharField(max_length=50,blank=True)

    def __str__(self):
        if self.costo ==None:
            return "Campo vacio"
        return f'{self.costo.status.perfil.nombres} {self.costo.status.perfil.apellidos} {self.fecha_bono}'

class Catorcenas(models.Model):
    catorcena = models.IntegerField(null=True, default=0)
    fecha_inicial = models.DateField(null=True)
    fecha_final = models.DateField(null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f' bono: {self.catorcena}, inicia {self.fecha_inicial} finaliza: {self.fecha_final}'
    class Meta:
        unique_together = ('catorcena', 'fecha_inicial',)

class Ropa(models.Model):
    ropa = models.CharField(max_length=50,null=True)
    complete = models.BooleanField(default=False)
    seleccionado = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.ropa}'

class Seleccion(models.Model):
    status = models.ForeignKey(Status, on_delete = models.CASCADE, null=True)
    ropa = models.ForeignKey(Ropa, on_delete = models.CASCADE, null=True)
    seleccionado = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.status}-{self.ropa}'

class Tallas(models.Model):
    ropa = models.ForeignKey(Ropa, on_delete = models.CASCADE, null=True)
    talla = models.CharField(max_length=50,null=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'Ropa: {self.ropa}, Talla: {self.talla}'

class Uniformes(models.Model):
    status = models.ForeignKey(Status, on_delete = models.CASCADE, null=True)
    fecha_pedido = models.DateField(null=True)
    #uniformes_totales = models.IntegerField(null=True, default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    complete = models.BooleanField(default=False)
    history = HistoricalRecords(history_change_reason_field=models.TextField(null=True))

    def __str__(self):
        if self.status == None:
            return "Campo vacio"
        return f'{self.status.perfil.nombres} {self.status.perfil.apellidos}'

class Uniforme(models.Model):
    orden = models.ForeignKey(Uniformes, on_delete = models.CASCADE, null=True)
    talla = models.ForeignKey(Tallas, on_delete = models.CASCADE, null=True)
    ropa = models.ForeignKey(Ropa, on_delete = models.CASCADE, null=True)
    fecha_entrega = models.DateField(null=True)
    cantidad = models.IntegerField(null=True, default=0)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'Ropa: {self.ropa} Talla: {self.talla} Cantidad: {self.cantidad}'

class Trabajos_encomendados(models.Model):
    asunto1 = models.CharField(max_length=100,null=True,blank=True)
    estado1 = models.CharField(max_length=100,null=True,blank=True)
    asunto2 = models.CharField(max_length=100,null=True,blank=True)
    estado2 = models.CharField(max_length=100,null=True,blank=True)
    asunto3 = models.CharField(max_length=100,null=True,blank=True)
    estado3 = models.CharField(max_length=100,null=True,blank=True)
    asunto4 = models.CharField(max_length=100,null=True,blank=True)
    estado4 = models.CharField(max_length=100,null=True,blank=True)
    asunto5 = models.CharField(max_length=100,null=True,blank=True)
    estado5 = models.CharField(max_length=100,null=True,blank=True)
    asunto6 = models.CharField(max_length=100,null=True,blank=True)
    estado6 = models.CharField(max_length=100,null=True,blank=True)
    asunto7 = models.CharField(max_length=100,null=True,blank=True)
    estado7 = models.CharField(max_length=100,null=True,blank=True)
    asunto8 = models.CharField(max_length=100,null=True,blank=True)
    estado8 = models.CharField(max_length=100,null=True,blank=True)
    asunto9 = models.CharField(max_length=100,null=True,blank=True)
    estado9 = models.CharField(max_length=100,null=True,blank=True)
    asunto10 = models.CharField(max_length=100,null=True,blank=True)
    estado10 = models.CharField(max_length=100,null=True,blank=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'ID: {self.id},'

class Temas_comentario_solicitud_vacaciones(models.Model):
    comentario1 = models.CharField(max_length=100,null=True,blank=True)
    comentario2 = models.CharField(max_length=100,null=True,blank=True)
    comentario3 = models.CharField(max_length=100,null=True,blank=True)
    comentario4 = models.CharField(max_length=100,null=True,blank=True)
    comentario5 = models.CharField(max_length=100,null=True,blank=True)
    comentario6 = models.CharField(max_length=100,null=True,blank=True)
    comentario7 = models.CharField(max_length=100,null=True,blank=True)
    comentario8 = models.CharField(max_length=100,null=True,blank=True)
    comentario9 = models.CharField(max_length=100,null=True,blank=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'ID: {self.id},'

class Solicitud_vacaciones(models.Model):
    status = models.ForeignKey(Status, on_delete = models.CASCADE, null=True)
    periodo = models.CharField(max_length=50,null=True)
    fecha_inicio = models.DateField(null=True)
    fecha_fin = models.DateField(null=True)
    dia_inhabil = models.ForeignKey(Dia_vacacion, on_delete = models.CASCADE, blank=True, null=True)
    recibe_nombre= models.CharField(max_length=50,null=True, blank=True)
    recibe_area= models.CharField(max_length=50,null=True, blank=True)
    recibe_puesto= models.CharField(max_length=50,null=True, blank=True)
    recibe_sector= models.CharField(max_length=50,null=True, blank=True)
    asunto = models.ManyToManyField(Trabajos_encomendados, blank=True)
    informacion_adicional= models.CharField(max_length=50,null=True, blank=True)
    temas = models.ForeignKey(Temas_comentario_solicitud_vacaciones, on_delete = models.CASCADE, null=True)
    anexos = models.CharField(max_length=200,null=True, blank=True)
    autorizar = models.BooleanField(null=True, default=None)
    comentario_rh = models.CharField(max_length=100,null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.temas} id: {self.id} Status: {self.status} Fecha solicitud: {self.created_at} Días: {self.fecha_inicio} a {self.fecha_fin}'

class Vacaciones(models.Model):
    status = models.ForeignKey(Status, on_delete = models.CASCADE, null=True)
    periodo = models.CharField(max_length=50,null=True)
    dias_de_vacaciones = models.IntegerField(null=True, default=0)
    dia_inhabil = models.ForeignKey(Dia_vacacion, on_delete = models.CASCADE, blank=True, null=True)
    fecha_inicio = models.DateField(null=True)
    fecha_fin = models.DateField(null=True)
    dias_disfrutados = models.IntegerField(null=True, default=0)
    total_pendiente = models.IntegerField(null=True, default=0)
    comentario = models.CharField(max_length=100,null=True)
    created_at=models.DateTimeField(auto_now=True)
    updated_at=models.DateTimeField(auto_now=True)
    complete = models.BooleanField(default=False)
    history = HistoricalRecords(history_change_reason_field=models.TextField(null=True))
    editado = models.CharField(max_length=50,blank=True)

    @property
    def total_pendiente_status(self):
        # Calcula la suma del total_pendiente para registros con el mismo status
        total = Vacaciones.objects.filter(status=self.status).aggregate(models.Sum('total_pendiente'))['total_pendiente__sum']
        return total or 0
        

    def __str__(self):
        if self.status == None:
            return "Campo vacio"
        return f'{self.status.perfil.nombres} {self.status.perfil.apellidos} {self.periodo} {self.total_pendiente}'

class Solicitud_economicos(models.Model):
    status = models.ForeignKey(Status, on_delete = models.CASCADE, null=True)
    periodo = models.CharField(max_length=50,null=True)
    fecha = models.DateField(null=True)
    comentario = models.CharField(max_length=50,null=True)
    autorizar = models.BooleanField(null=True, default=None)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f'Status: {self.status} Fecha solicitud: {self.created_at} Día: {self.fecha}'

class Economicos(models.Model):
    status = models.ForeignKey(Status, on_delete = models.CASCADE, null=True)
    periodo = models.CharField(max_length=50,null=True)
    dias_disfrutados = models.IntegerField(null=True, default=0)
    dias_pendientes = models.IntegerField(null=True, default=0)
    fecha = models.DateField(null=True)
    comentario = models.CharField(max_length=100,null=True)
    complete = models.BooleanField(default=False)
    complete_dias = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    history = HistoricalRecords(history_change_reason_field=models.TextField(null=True))
    editado = models.CharField(max_length=50,blank=True)

    def __str__(self):
        if self.status == None:
            return "Campo vacio"
        return f'{self.status.perfil.nombres} {self.status.perfil.apellidos}'

class Empleados_Batch(models.Model):
    file_name = models.FileField(upload_to='product_bash')
    uploaded = models.DateField(auto_now_add=True)
    activated = models.BooleanField(default=False)

    def __str__(self):
        return f'File id:{self.id}'

class Status_Batch(models.Model):
    file_name = models.FileField(upload_to='product_bash')
    uploaded = models.DateField(auto_now_add=True)
    activated = models.BooleanField(default=False)


    def __str__(self):
        return f'File id:{self.id}'

class Costos_Batch(models.Model):
    file_name = models.FileField(upload_to='product_bash')
    uploaded = models.DateField(auto_now_add=True)
    activated = models.BooleanField(default=False)

    def __str__(self):
        return f'File id:{self.id}'

class Bancarios_Batch(models.Model):
    file_name = models.FileField(upload_to='product_bash')
    uploaded = models.DateField(auto_now_add=True)
    activated = models.BooleanField(default=False)

    def __str__(self):
        return f'File id:{self.id}'

class Vacaciones_anteriores_Batch(models.Model):
    file_name = models.FileField(upload_to='product_bash')
    uploaded = models.DateField(auto_now_add=True)
    activated = models.BooleanField(default=False)

    def __str__(self):
        return f'File id:{self.id}'

class Datos_baja(models.Model):
    perfil = models.ForeignKey(Perfil, on_delete = models.CASCADE, null=True)
    fecha = models.DateField(null=True) #blank=True
    finiquito = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    liquidacion = models.DecimalField(max_digits=14, decimal_places=2,null=True, default=0)
    motivo = models.CharField(max_length=50,null=True)
    exitosa = models.BooleanField(null=True, default=None) 
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    history = HistoricalRecords(history_change_reason_field=models.TextField(null=True))
    editado = models.CharField(max_length=50,blank=True)
    complete = models.BooleanField(default=False)
   
    def __str__(self):
        return f'Empleado:{self.perfil}'

class Empleado_cv(models.Model):
    status = models.ForeignKey(Status, on_delete = models.CASCADE, null=True)
    fecha_inicio = models.DateField(null=True) #blank=True
    fecha_fin = models.DateField(null=True) #blank=True
    puesto = models.ForeignKey(Puesto, on_delete = models.CASCADE, null=True)
    distrito = models.ForeignKey(Distrito, on_delete = models.CASCADE, null=True)
    empresa = models.ForeignKey(Empresa, on_delete = models.CASCADE, null=True)
    comentario = models.CharField(max_length=100,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    history = HistoricalRecords(history_change_reason_field=models.TextField(null=True))
    editado = models.CharField(max_length=50,blank=True)
    complete = models.BooleanField(default=False)
   
    def __str__(self):
        return f'Empleado:{self.status}'