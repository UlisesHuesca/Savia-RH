from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from proyecto import views


urlpatterns = [
    path('', views.Index, name='Inicio'),
    path('...', views.Principal, name='Principal'),

    path('Perfil', views.Perfil_vista, name='Perfil'),
    path('Perfil_baja', views.Perfil_vista_baja, name='Perfil_baja'),
    path('Perfil/Reingreso<int:pk>/', views.Reingreso, name='Reingreso'),  
    path('Status', views.Status_vista, name='Status'),
    path('Formulario_Perfil', views.FormularioPerfil, name='Formulario_perfil'),
    path('Formulario_Status', views.FormularioStatus, name='Formulario_status'),
    path('upload_Perfil', views.upload_batch_empleados, name='Upload_perfil'),

    path('Perfil/update/<int:pk>/', views.PerfilUpdate, name='Perfil_update'),
    path('Perfil/Baja/<int:pk>/', views.Baja_empleado, name='Baja_empleado'),  
    path('Perfil/Baja/update<int:pk>/', views.Baja_update, name='Baja_empleado_update'),  
    path('Perfil/revisar/<int:pk>/', views.Perfil_revisar, name='Perfil_revisar'),
    path('Status/update/<int:pk>/', views.StatusUpdate, name='Status_update'),
    path('Status/revisar/<int:pk>/', views.Status_revisar, name='Status_revisar'),
    path('upload_Status', views.upload_batch_status, name='Upload_status'),
    path('Status/CV/<int:pk>/', views.Cv_datos, name='Cv_datos'),
    path('CV/Agregar/<int:pk>/', views.Cv_agregar, name='Cv_agregar'),

    path('Administrar', views.Administrar_tablas, name='Administrar_tablas'),
    path('Tabla_catorcenas', views.Tabla_catorcenas, name='Tabla_catorcenas'),
    path('Formulario_catorcenas', views.FormularioCatorcenas, name='Formulario_catorcenas'), #Inhabilitar
    path('Catorcenas/update/<int:pk>/', views.CatorcenasUpdate, name='Catorcenas_update'),
    path('Tabla_ISR', views.Tabla_isr, name='Tabla_isr'),
    path('ISR/update/<int:pk>/', views.IsrUpdate, name='Isr_update'),
    path('Tabla_dias_vacaciones', views.Tabla_dias_vacaciones, name='Tabla_dias_vacaciones'),
    path('Vacaciones_dias/update/<int:pk>/', views.Dias_VacacionesUpdate, name='Dias_Vacaciones_update'),

    path('Tabla_Costo', views.TablaCosto, name='Tabla_costo'),
    path('Formulario_Costo', views.FormularioCosto, name='Formulario_costo'),
    path('Costo/update/<int:pk>/', views.CostoUpdate, name='Costo_update'),
    path('Costo/revisar/<int:pk>/', views.Costo_revisar, name='Costo_revisar'),
    path('Costo/History/<int:pk>/', views.HistoryCosto, name='Costo_history'),
    path('upload_Costos', views.upload_batch_costos, name='Upload_costos'),
    path('Empleado/Costo/<int:pk>/', views.Empleado_Costo, name='Empleado_costo'),

    #path('Formulario_Vacaciones', views.FormularioVacaciones, name='Formulario_vacaciones'),
    path('VacacionesEmpleados', views.Tabla_Vacaciones, name='Tabla_vacaciones_empleados'),

    path('Vacaciones/update/<int:pk>/', views.VacacionesUpdate, name='Vacaciones_update'),
    path('Vacaciones/revisar/<int:pk>/', views.VacacionesRevisar, name='Vacaciones_revisar'),
    path('Solicitudes_vacaciones', views.Tabla_solicitud_vacaciones, name='Solicitudes_vacaciones'),
    path('Solicitudes_vacaciones_formato/<int:pk>/', views.PdfFormatoVacaciones, name='Solicitudes_vacaciones_formato'), #genera el pdf
    path('Solicitud_vacacion_autorizar/<int:pk>/', views.solicitud_vacacion_verificar, name='solicitud-vacacion-update'),
    path('upload_Vacaciones_anteriores', views.upload_batch_vacaciones_anteriores, name='Upload_vacaciones_anteriores'),

    path('Formulario_DatosBancarios', views.FormularioDatosBancarios, name='Formulario_datosbancarios'),
    path('Tabla_DatosBancarios', views.Tabla_Datosbancarios, name='Tabla_datosbancarios'),
    path('upload_Bancarios', views.upload_batch_bancarios, name='Upload_bancarios'),
    path('Empleado/Datos_bancarios/<int:pk>/', views.Empleado_Datosbancarios, name='Empleado_bancarios'),
    path('upload_Bonos_catorcena', views.upload_batch_bonos, name='Upload_bonos_catorcena'),

    path('Formulario_Bonos', views.FormularioBonos, name='Formulario_bonos'),
    path('Tabla_Bonos', views.TablaBonos, name='Tabla_bonos'),

    path('Bonos/update/<int:pk>/', views.BonosUpdate, name='Bonos_update'),
    path('Empleado/Bonos/<int:pk>/', views.Empleado_Bonos, name='Empleado_bonos'),

    path('DatosBancarios/update/<int:pk>/', views.BancariosUpdate, name='Bancarios_update'),

    path('Tabla/Uniformes', views.Tabla_uniformes, name='Tabla_uniformes'),
    path('Orden/Uniformes/<int:pk>/', views.Orden_uniformes, name='Orden_uniformes'),
    path('Orden/Uniformes/<int:pk>/update_uniformes/', views.update_uniformes, name='update-uniformes'),

    path('Uniformes/completados/revisar/<int:pk>/', views.Uniformes_revisar_completados, name='Uniformes_completados_revisar'),
    path('Uniformes/ordenes/revisar/<int:pk>/', views.Uniformes_revisar_ordenes, name='Uniformes_ordenes_revisar'),
    path('Uniformes/pdf/<int:pk>/', views.reporte_pdf_uniformes, name='reporte_pdf_uniformes'),

    path('Formulario_Economicos', views.FormularioEconomicos, name='Formulario_economicos'),
    path('Tabla_Economicos', views.Tabla_Economicos, name='Tabla_economicos'),

    path('Solicitar/Vacaciones', views.SolicitudVacaciones, name='Solicitar_vacacion'),
    path('Formato/Vacaciones', views.FormatoVacaciones, name='Formato_vacaciones'), #Borrar
    #path('Formulario/Formato/Vacaciones', views.FormFormatoVacaciones, name='Formularioformato_vacaciones'),
    path('Formato/Economicos', views.FormatoEconomicos, name='Formato_economicos'), #Borrar
    path('Solicitar/Economico', views.SolicitudEconomicos, name='Solicitar_economico'),

    path('Economicos/update/<int:pk>/', views.EconomicosUpdate, name='Economicos_update'),
    path('Economicos/revisar/<int:pk>/', views.EconomicosRevisar, name='Economicos_revisar'),
    path('Solicitudes_economicos', views.Tabla_solicitud_economicos, name='Solicitudes_economicos'),
    path('Solicitudes_economicos_formato/<int:pk>/', views.PdfFormatoEconomicos, name='Solicitudes_economicos_formato'), #genera el pdf
    path('Solicitud_economico_autorizar/<int:pk>/', views.solicitud_economico_verificar, name='solicitud-economico-update'),

    path('Solicitudes_revisadas/Empleado', views.Solicitudes_revisar_empleado, name='Solicitudes_vista_empleado'), #Vista empleado generar pdf
    path('antiguedad/<int:pk>/', views.Antiguedad, name='antiguedad'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)