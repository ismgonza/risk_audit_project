from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from risks.models import RiskCategory, Risk
from controls.models import Control, ControlEvidence


class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema de auditoría de riesgos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Eliminar datos existentes antes de crear nuevos',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Eliminando datos existentes...')
            ControlEvidence.objects.all().delete()
            Control.objects.all().delete()
            Risk.objects.all().delete()
            RiskCategory.objects.all().delete()
            self.stdout.write(self.style.WARNING('Datos eliminados'))

        # Crear usuario auditor (ismgonza) si no existe
        auditor_user, created = User.objects.get_or_create(
            username='ismgonza',
            defaults={
                'email': 'ismgonza@empresa.com',
                'first_name': 'Ismael',
                'last_name': 'González',
                'is_staff': True,
            }
        )
        if created:
            auditor_user.set_password('auditor123')
            auditor_user.save()
            self.stdout.write(f'✓ Usuario auditor creado (username: ismgonza, password: auditor123)')

        # Crear usuario regular (jperez)
        regular_user, created = User.objects.get_or_create(
            username='jperez',
            defaults={
                'email': 'jperez@empresa.com',
                'first_name': 'Juan',
                'last_name': 'Pérez',
            }
        )
        if created:
            regular_user.set_password('usuario123')
            regular_user.save()
            self.stdout.write(f'✓ Usuario regular creado (username: jperez, password: usuario123)')

        self.stdout.write('\n🏗️  Creando datos de prueba...\n')

        # Crear categorías de riesgo (mantener las existentes)
        categories_data = [
            {
                'name': 'Continuidad operativa',
                'description': 'Altamente sensible a fallos e interrupciones.',
                'risk_appetite': 'LOW'
            },
            {
                'name': 'Desarrollo ágil',
                'description': 'Se permite flexibilidad controlada.',
                'risk_appetite': 'MEDIUM'
            },
            {
                'name': 'Seguridad de TI',
                'description': 'Riesgos relacionados con sistemas de información y ciberseguridad. Alta confidencialidad esperada.',
                'risk_appetite': 'LOW'
            },
            {
                'name': 'TI operativo',
                'description': 'Se toleran riesgos controlados en operaciones.',
                'risk_appetite': 'MEDIUM'
            },
            {
                'name': 'Cumplimiento legal',
                'description': 'Riesgos regulatorios y de cumplimiento normativo. Riesgo alto de sanciones y daño reputacional.',
                'risk_appetite': 'LOW'
            }
        ]

        categories = []
        for cat_data in categories_data:
            category, created = RiskCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories.append(category)
            if created:
                self.stdout.write(f'✓ Categoría: {category.name}')

        # Crear riesgos basados en los datos del Excel
        risks_data = [
            {
                'code': 'TI-001',
                'name': 'Fuga de datos sensibles (clientes y código fuente)',
                'description': 'Riesgo de exposición no autorizada de información confidencial de clientes y código fuente propietario que puede resultar en daños reputacionales, legales y competitivos',
                'category': categories[2],  # Seguridad de TI
                'probability': 1,
                'impact': 4,
            },
            {
                'code': 'TI-002',
                'name': 'Entrega de software con vulnerabilidades críticas',
                'description': 'Riesgo de implementar y entregar software que contenga vulnerabilidades de seguridad críticas que puedan ser explotadas por atacantes',
                'category': categories[1],  # Desarrollo ágil
                'probability': 2,
                'impact': 4,
            }
        ]

        risks = []
        for risk_data in risks_data:
            risk, created = Risk.objects.get_or_create(
                code=risk_data['code'],
                defaults={**risk_data, 'created_by': auditor_user}
            )
            risks.append(risk)
            if created:
                self.stdout.write(f'✓ Riesgo: {risk.code} - {risk.name}')

        # Crear controles específicos para cada riesgo basados en el Excel
        controls_data = {
            'TI-001': [  # Fuga de datos sensibles
                {
                    'name': 'Implementación de un sistema DLP (Data Loss Prevention)',
                    'description': 'Sistema automatizado para prevenir la pérdida o fuga de datos sensibles mediante monitoreo y control de transferencias de información.',
                    'control_type': 'PREVENTIVE',
                    'frequency': 'DAILY',
                    'responsible_person': 'Especialista en Seguridad de TI'
                },
                {
                    'name': 'Implementar una solución de Gestión de Accesos Privilegiados (PAM)',
                    'description': 'Sistema PAM para controlar, monitorear y registrar el uso de cuentas privilegiadas y accesos administrativos.',
                    'control_type': 'PREVENTIVE',
                    'frequency': 'DAILY',
                    'responsible_person': 'Administrador de Sistemas'
                },
                {
                    'name': 'Implementar un sistema SIEM (Security Information and Event Management)',
                    'description': 'Sistema centralizado para recopilar, analizar y correlacionar eventos de seguridad en tiempo real.',
                    'control_type': 'DETECTIVE',
                    'frequency': 'DAILY',
                    'responsible_person': 'Analista de Seguridad'
                },
                {
                    'name': 'Implementar cifrado para los datos sensibles',
                    'description': 'Cifrado de datos sensibles tanto en reposo como en tránsito para proteger la confidencialidad de la información.',
                    'control_type': 'PREVENTIVE',
                    'frequency': 'DAILY',
                    'responsible_person': 'Administrador de Base de Datos'
                },
                {
                    'name': 'Políticas de uso aceptable y acuerdos de confidencialidad',
                    'description': 'Establecimiento y mantenimiento de políticas claras sobre el uso aceptable de datos y sistemas, respaldadas por acuerdos de confidencialidad.',
                    'control_type': 'PREVENTIVE',
                    'frequency': 'QUARTERLY',
                    'responsible_person': 'Gerente de Recursos Humanos'
                }
            ],
            'TI-002': [  # Entrega de software con vulnerabilidades críticas
                {
                    'name': 'Implementación de Pruebas de Seguridad Automatizadas (SAST/DAST)',
                    'description': 'Integración de herramientas de análisis estático y dinámico de código para detectar vulnerabilidades durante el desarrollo.',
                    'control_type': 'DETECTIVE',
                    'frequency': 'DAILY',
                    'responsible_person': 'Lead Developer'
                },
                {
                    'name': 'Revisiones de Código Enfocadas en Seguridad',
                    'description': 'Proceso formal de revisión de código con enfoque específico en identificación de vulnerabilidades de seguridad.',
                    'control_type': 'DETECTIVE',
                    'frequency': 'WEEKLY',
                    'responsible_person': 'Senior Developer'
                },
                {
                    'name': 'Capacitación en Desarrollo Seguro para Desarrolladores',
                    'description': 'Programa de capacitación continua para desarrolladores en prácticas de codificación segura y identificación de vulnerabilidades.',
                    'control_type': 'PREVENTIVE',
                    'frequency': 'QUARTERLY',
                    'responsible_person': 'Gerente de Desarrollo'
                }
            ]
        }

        control_count = 0
        for risk in risks:
            risk_controls = controls_data.get(risk.code, [])
            
            for control_data in risk_controls:
                control_info = {
                    'risk': risk,
                    'name': control_data['name'],
                    'description': control_data['description'],
                    'control_type': control_data['control_type'],
                    'frequency': control_data['frequency'],
                    'responsible_person': control_data['responsible_person'],
                    'created_by': regular_user,
                    'auditor_approval': random.choice(['APPROVED', 'APPROVED', 'PENDING']),  # 66% aprobados
                    'is_active': True
                }
                
                # Si está aprobado, asignar auditor
                if control_info['auditor_approval'] == 'APPROVED':
                    control_info['auditor'] = auditor_user

                control = Control.objects.create(**control_info)
                control_count += 1
                
                # Crear evidencias para controles aprobados
                if control.auditor_approval == 'APPROVED':
                    evidence_count = random.randint(1, 2)
                    
                    for j in range(evidence_count):
                        evidence_date = timezone.now() - timedelta(days=random.randint(1, 30))
                        effectiveness = random.choice([95, 85, 75, 65])  # Efectividad alta para controles reales
                        
                        evidence = ControlEvidence.objects.create(
                            control=control,
                            evidence_date=evidence_date,
                            description=f'Evidencia de ejecución del control {control.name}. '
                                      f'Se verificó la correcta implementación y funcionamiento del control '
                                      f'durante el período correspondiente.',
                            effectiveness_percentage=effectiveness,
                            uploaded_by=regular_user,
                            is_validated=random.choice([True, True, False]),  # 66% validadas
                            validated_by=auditor_user if random.choice([True, False]) else None
                        )
                        
                        if evidence.is_validated and evidence.validated_by:
                            evidence.validation_date = evidence_date + timedelta(days=random.randint(1, 5))
                            evidence.auditor_review = random.choice([
                                'Evidencia válida y completa.',
                                'Evidencia aceptable, cumple con los requisitos.',
                                'Buena evidencia, bien documentada.',
                            ])
                            evidence.save()

        # Recalcular riesgos residuales
        self.stdout.write('\n🔄 Recalculando riesgos residuales...')
        for risk in risks:
            risk.calculate_residual_risk()

        # Resumen final
        self.stdout.write(f'\n🎉 ¡Datos de prueba creados exitosamente!')
        self.stdout.write(f'')
        self.stdout.write(f'📊 Resumen:')
        self.stdout.write(f'  • {len(categories)} categorías de riesgo')
        self.stdout.write(f'  • {len(risks)} riesgos')
        self.stdout.write(f'  • {control_count} controles')
        self.stdout.write(f'  • {ControlEvidence.objects.count()} evidencias')
        self.stdout.write(f'')
        self.stdout.write(f'👥 Usuarios creados:')
        self.stdout.write(f'  • ismgonza / auditor123 (Auditor)')
        self.stdout.write(f'  • jperez / usuario123 (Usuario regular)')
        self.stdout.write(f'')
        self.stdout.write(self.style.SUCCESS('✅ Puedes acceder al sistema en http://127.0.0.1:8000/admin/'))