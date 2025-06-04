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

        # Crear usuario administrador si no existe
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@riskaudit.com',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(f'✓ Usuario admin creado (password: admin123)')

        # Crear auditor
        auditor_user, created = User.objects.get_or_create(
            username='auditor',
            defaults={
                'email': 'auditor@riskaudit.com',
                'first_name': 'María',
                'last_name': 'Rodríguez',
                'is_staff': True,
            }
        )
        if created:
            auditor_user.set_password('auditor123')
            auditor_user.save()
            self.stdout.write(f'✓ Usuario auditor creado (password: auditor123)')

        # Crear usuario regular
        regular_user, created = User.objects.get_or_create(
            username='usuario',
            defaults={
                'email': 'usuario@empresa.com',
                'first_name': 'Carlos',
                'last_name': 'González',
            }
        )
        if created:
            regular_user.set_password('usuario123')
            regular_user.save()
            self.stdout.write(f'✓ Usuario regular creado (password: usuario123)')

        self.stdout.write('\n🏗️  Creando datos de prueba...\n')

        # Crear categorías de riesgo
        categories_data = [
            {
                'name': 'Operacional',
                'description': 'Riesgos relacionados con procesos internos, sistemas y personas',
                'risk_appetite': 'MEDIUM'
            },
            {
                'name': 'Financiero',
                'description': 'Riesgos que pueden afectar la estabilidad financiera',
                'risk_appetite': 'LOW'
            },
            {
                'name': 'Tecnológico',
                'description': 'Riesgos relacionados con sistemas de información y ciberseguridad',
                'risk_appetite': 'MEDIUM'
            },
            {
                'name': 'Cumplimiento',
                'description': 'Riesgos regulatorios y de cumplimiento normativo',
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

        # Crear riesgos
        risks_data = [
            # Riesgos Operacionales
            {
                'code': 'OP-001',
                'name': 'Fallas en procesos de facturación',
                'description': 'Errores en el proceso de facturación que pueden resultar en pérdidas económicas o insatisfacción del cliente',
                'category': categories[0],
                'probability': 2,
                'impact': 4,
            },
            {
                'code': 'OP-002', 
                'name': 'Ausencia de personal clave',
                'description': 'Riesgo de interrupción de operaciones críticas debido a la ausencia temporal o permanente de personal especializado',
                'category': categories[0],
                'probability': 2,
                'impact': 3,
            },
            
            # Riesgos Financieros
            {
                'code': 'FN-001',
                'name': 'Fluctuaciones en tipo de cambio',
                'description': 'Exposición a pérdidas debido a variaciones adversas en tipos de cambio de monedas extranjeras',
                'category': categories[1],
                'probability': 3,
                'impact': 4,
            },
            {
                'code': 'FN-002',
                'name': 'Cartera vencida elevada',
                'description': 'Incremento en cuentas por cobrar vencidas que afectan el flujo de efectivo',
                'category': categories[1],
                'probability': 2,
                'impact': 5,
            },
            
            # Riesgos Tecnológicos
            {
                'code': 'TI-001',
                'name': 'Ataques de ciberseguridad',
                'description': 'Riesgo de ataques maliciosos que comprometan la integridad, confidencialidad o disponibilidad de la información',
                'category': categories[2],
                'probability': 3,
                'impact': 5,
            },
            {
                'code': 'TI-002',
                'name': 'Fallas en sistemas críticos',
                'description': 'Interrupciones no planificadas en sistemas de información que afecten operaciones críticas',
                'category': categories[2],
                'probability': 2,
                'impact': 4,
            },
            
            # Riesgos de Cumplimiento
            {
                'code': 'CP-001',
                'name': 'Incumplimiento regulatorio fiscal',
                'description': 'Riesgo de sanciones por incumplimiento de obligaciones fiscales o normativas',
                'category': categories[3],
                'probability': 1,
                'impact': 5,
            },
            {
                'code': 'CP-002',
                'name': 'Violación de protección de datos',
                'description': 'Incumplimiento de normativas de protección de datos personales (GDPR, etc.)',
                'category': categories[3],
                'probability': 2,
                'impact': 4,
            }
        ]

        risks = []
        for risk_data in risks_data:
            risk, created = Risk.objects.get_or_create(
                code=risk_data['code'],
                defaults={**risk_data, 'created_by': admin_user}
            )
            risks.append(risk)
            if created:
                self.stdout.write(f'✓ Riesgo: {risk.code} - {risk.name}')

        # Crear controles para cada riesgo
        controls_templates = [
            {
                'types': ['PREVENTIVE', 'DETECTIVE', 'CORRECTIVE'],
                'frequencies': ['DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY'],
                'names': [
                    'Revisión diaria de {proceso}',
                    'Control automatizado de {proceso}',
                    'Segregación de funciones en {proceso}',
                    'Aprobación supervisora de {proceso}',
                    'Monitoreo continuo de {proceso}',
                    'Backup y recuperación de {proceso}',
                    'Capacitación en {proceso}',
                    'Políticas y procedimientos de {proceso}'
                ]
            }
        ]

        control_count = 0
        for risk in risks:
            # Crear 2-4 controles por riesgo
            num_controls = random.randint(2, 4)
            
            for i in range(num_controls):
                control_name = random.choice(controls_templates[0]['names']).format(
                    proceso=risk.name.lower()[:20]
                )
                
                control_data = {
                    'risk': risk,
                    'name': control_name,
                    'description': f'Control {i+1} implementado para mitigar el riesgo {risk.code}. '
                                 f'Este control está diseñado para reducir la probabilidad y/o impacto del riesgo identificado.',
                    'control_type': random.choice(controls_templates[0]['types']),
                    'frequency': random.choice(controls_templates[0]['frequencies']),
                    'responsible_person': random.choice([
                        'Gerente de Operaciones',
                        'Supervisor de Área',
                        'Analista Senior',
                        'Coordinador de Procesos',
                        'Jefe de Departamento'
                    ]),
                    'created_by': random.choice([admin_user, regular_user]),
                    'auditor_approval': random.choice(['PENDING', 'APPROVED', 'APPROVED', 'NEEDS_REVISION']),
                    'is_active': True
                }
                
                # Si está aprobado, asignar auditor
                if control_data['auditor_approval'] != 'PENDING':
                    control_data['auditor'] = auditor_user
                    if control_data['auditor_approval'] == 'NEEDS_REVISION':
                        control_data['auditor_feedback'] = 'El control necesita mayor detalle en los procedimientos de verificación.'

                control = Control.objects.create(**control_data)
                control_count += 1
                
                # Crear evidencias para controles aprobados
                if control.auditor_approval == 'APPROVED':
                    evidence_count = random.randint(1, 3)
                    
                    for j in range(evidence_count):
                        evidence_date = timezone.now() - timedelta(days=random.randint(1, 30))
                        effectiveness = random.choice([95, 77, 77, 52, 22])  # Más peso a efectivos
                        
                        evidence = ControlEvidence.objects.create(
                            control=control,
                            evidence_date=evidence_date,
                            description=f'Evidencia {j+1} de ejecución del control. '
                                      f'Se verificó la correcta implementación del control '
                                      f'durante el período correspondiente.',
                            effectiveness_percentage=effectiveness,
                            uploaded_by=random.choice([admin_user, regular_user]),
                            is_validated=random.choice([True, True, False]),  # 66% validadas
                            validated_by=auditor_user if random.choice([True, False]) else None
                        )
                        
                        if evidence.is_validated and evidence.validated_by:
                            evidence.validation_date = evidence_date + timedelta(days=random.randint(1, 5))
                            evidence.auditor_review = random.choice([
                                'Evidencia válida y completa.',
                                'Evidencia aceptable, cumple con los requisitos.',
                                'Buena evidencia, bien documentada.',
                                ''
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
        self.stdout.write(f'  • admin / admin123 (Administrador)')
        self.stdout.write(f'  • auditor / auditor123 (Auditor)')
        self.stdout.write(f'  • usuario / usuario123 (Usuario regular)')
        self.stdout.write(f'')
        self.stdout.write(self.style.SUCCESS('✅ Puedes acceder al sistema en http://127.0.0.1:8000/admin/'))