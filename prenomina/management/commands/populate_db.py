from django.core.management.base import BaseCommand
from faker import Faker
from prenomina.models import IncidenciaRango, Incidencia, Costo, Dia_vacacion
from django.utils import timezone
import uuid
import os

class Command(BaseCommand):
    help = 'Poblar la base de datos con datos falsos para IncidenciaRango'

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Obtener todas las instancias de Incidencia, Costo y Dia_vacacion
        incidencias = Incidencia.objects.all()
        #costos = Costo.objects.exclude(id = 1142)
        costos = Costo.objects.filter(id__in = [751,752,769,754,712,1152])
        dias_vacacion = Dia_vacacion.objects.all()

        # Obtener la ruta base para el archivo soporte
        base_dir = 'prenomina/'

        # Crear datos falsos
        for _ in range(10000):
            unique_id = uuid.uuid4()
            incidencia = fake.random_element(incidencias)
            empleado = fake.random_element(costos)
            fecha_inicio = fake.date_between(start_date='-30d', end_date='+30d')
            fecha_fin = fake.date_between(start_date=fecha_inicio, end_date='+30d')
            dia_inhabil = fake.random_element(dias_vacacion)
            comentario = fake.text(max_nb_chars=100)
            subsecuente = fake.boolean()
            complete = fake.boolean()
            soporte_filename = f"{unique_id}.pdf"
            soporte_path = os.path.join(base_dir, soporte_filename)

            # Crear instancia de IncidenciaRango con datos falsos
            incidencia_rango = IncidenciaRango.objects.create(
                incidencia=incidencia,
                empleado=empleado,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                dia_inhabil=dia_inhabil,
                comentario=comentario,
                subsecuente=subsecuente,
                complete=complete,
            )

            # Crear archivo soporte vacío
            with open(soporte_path, 'w') as f:
                f.write('')

            # Asignar archivo soporte a la instancia de IncidenciaRango
            incidencia_rango.soporte.name = soporte_filename
            incidencia_rango.save()

            self.stdout.write(self.style.SUCCESS(f'Se creó IncidenciaRango {incidencia_rango.id}'))