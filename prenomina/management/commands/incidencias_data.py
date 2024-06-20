from django.core.management.base import BaseCommand
from faker import Faker
from datetime import datetime, timedelta
from prenomina.models import PrenominaIncidencias, Prenomina, Incidencia, IncidenciaRango

class Command(BaseCommand):
    help = 'Poblar la base de datos con datos de prueba para PrenominaIncidencias'

    def handle(self, *args, **kwargs):
        fake = Faker()
        num_entries = 10000  # Número de entradas de prueba que quieres crear

        # Obtener todas las prenominas y incidencias disponibles
        prenominas = Prenomina.objects.exclude(id=15)
        incidencias = Incidencia.objects.all()
        incidencia_rangos = IncidenciaRango.objects.all()

        # Generar datos de prueba
        for _ in range(num_entries):
            # Generar datos falsos para cada campo del modelo
            prenomina = fake.random_element(prenominas)
            incidencia = fake.random_element(incidencias)
            incidencia_rango = fake.random_element(incidencia_rangos) if fake.boolean(chance_of_getting_true=50) else None
            fecha = fake.date_between(start_date='-30d', end_date='today')
            comentario = fake.text(max_nb_chars=100)
            soporte = None  # Dejar el campo de soporte vacío para este ejemplo
            complete = fake.boolean(chance_of_getting_true=50)

            # Crear instancia de PrenominaIncidencias
            incidencia_obj = PrenominaIncidencias.objects.create(
                prenomina=prenomina,
                incidencia=incidencia,
                incidencia_rango=incidencia_rango,
                fecha=fecha,
                comentario=comentario,
                soporte=soporte,
                complete=complete
            )

            self.stdout.write(self.style.SUCCESS(f'Se ha creado {incidencia_obj}'))

        self.stdout.write(self.style.SUCCESS('¡Datos de prueba creados correctamente!'))