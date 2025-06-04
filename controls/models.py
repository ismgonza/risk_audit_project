from django.db import models
from django.contrib.auth.models import User
from risks.models import Risk


class Control(models.Model):
    """Controles para mitigar riesgos"""
    
    CONTROL_TYPE_CHOICES = [
        ('PREVENTIVE', 'Preventivo'),
        ('DETECTIVE', 'Detectivo'),
        ('CORRECTIVE', 'Correctivo'),
        ('BOTH', 'Mixto'),
    ]
    
    APPROVAL_STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('APPROVED', 'Aprobado'),
        ('REJECTED', 'Rechazado'),
        ('NEEDS_REVISION', 'Necesita Revisión'),
        ('PENDING_REVALUATION', 'Pendiente de Re-evaluación'),
    ]
    
    FREQUENCY_CHOICES = [
        ('HOURLY', 'Por Hora'),
        ('DAILY', 'Diario'),
        ('WEEKLY', 'Semanal'),
        ('MONTHLY', 'Mensual'),
        ('QUARTERLY', 'Trimestral'),
        ('ANNUALLY', 'Anual'),
    ]
    
    # Relación con el riesgo
    risk = models.ForeignKey(Risk, on_delete=models.CASCADE, verbose_name="Riesgo")
    
    # Información básica del control
    name = models.CharField(max_length=200, verbose_name="Nombre del Control")
    description = models.TextField(verbose_name="Descripción del Control")
    control_type = models.CharField(
        max_length=20, 
        choices=CONTROL_TYPE_CHOICES, 
        verbose_name="Tipo de Control"
    )
    
    # Configuración del control
    frequency = models.CharField(
        max_length=20, 
        choices=FREQUENCY_CHOICES, 
        verbose_name="Frecuencia de Ejecución"
    )
    responsible_person = models.CharField(
        max_length=100, 
        verbose_name="Persona Responsable"
    )
    
    # Aprobación del auditor
    auditor_approval = models.CharField(
        max_length=20, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='PENDING',
        verbose_name="Estado de Aprobación"
    )
    auditor_feedback = models.TextField(
        blank=True, 
        verbose_name="Comentarios del Auditor"
    )
    auditor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='audited_controls',
        verbose_name="Auditor"
    )
    
    # Estado del control
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    # Metadatos
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Creado por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    
    class Meta:
        verbose_name = "Control"
        verbose_name_plural = "Controles"
        ordering = ['-created_at']
    
    def get_overall_effectiveness(self):
        """Calcula la efectividad general del control basada en las evidencias"""
        evidences = self.controlevidence_set.filter(is_validated=True)
        
        if not evidences.exists():
            return 0.0
        
        # Promedio de efectividad de todas las evidencias validadas
        total_effectiveness = sum(evidence.effectiveness_percentage for evidence in evidences)
        return (total_effectiveness / len(evidences)) / 100  # Convertir a decimal (0.0 - 1.0)
    
    def get_overall_effectiveness_percentage(self):
        """Retorna la efectividad como porcentaje entero para mostrar en templates"""
        return round(self.get_overall_effectiveness() * 100)
    
    def get_latest_evidence(self):
        """Obtiene la evidencia más reciente"""
        return self.controlevidence_set.order_by('-evidence_date').first()
    
    def get_approval_color(self):
        """Retorna color para mostrar el estado de aprobación"""
        colors = {
            'PENDING': 'warning',
            'APPROVED': 'success',
            'REJECTED': 'danger',
            'NEEDS_REVISION': 'info',
            'PENDING_REVALUATION': 'secondary',
            
        }
        return colors.get(self.auditor_approval, 'secondary')
    
    def __str__(self):
        return f"{self.name} - {self.risk.code}"


class ControlEvidence(models.Model):
    """Evidencias de la efectividad de los controles"""
    
    EFFECTIVENESS_CHOICES = [
        (95, 'Altamente efectivo (90-95%)'),
        (77, 'Moderadamente efectivo (70-85%)'),
        (52, 'Parcialmente efectivo (40-65%)'),
        (22, 'Poco efectivo (10-35%)'),
    ]
    
    # Relación con el control
    control = models.ForeignKey(Control, on_delete=models.CASCADE, verbose_name="Control")
    
    # Información de la evidencia
    evidence_date = models.DateTimeField(verbose_name="Fecha de la Evidencia")
    description = models.TextField(verbose_name="Descripción de la Evidencia")
    effectiveness_percentage = models.IntegerField(
        choices=EFFECTIVENESS_CHOICES,
        verbose_name="Porcentaje de Efectividad"
    )
    
    # Archivos adjuntos
    document = models.FileField(
        upload_to='evidence_documents/', 
        null=True, 
        blank=True, 
        verbose_name="Documento de Soporte"
    )
    
    # Evaluación del auditor
    auditor_review = models.TextField(
        blank=True, 
        verbose_name="Revisión del Auditor"
    )
    is_validated = models.BooleanField(
        default=False, 
        verbose_name="Validado por Auditor"
    )
    validated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_evidences',
        verbose_name="Validado por"
    )
    validation_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Validación"
    )
    
    # Metadatos
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Subido por")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Subida")
    
    class Meta:
        verbose_name = "Evidencia de Control"
        verbose_name_plural = "Evidencias de Control"
        ordering = ['-evidence_date']
    
    def get_effectiveness_display_short(self):
        """Versión corta del display de efectividad"""
        effectiveness_map = {
            95: 'Altamente efectivo',
            77: 'Moderadamente efectivo',
            52: 'Parcialmente efectivo',
            22: 'Poco efectivo',
        }
        return effectiveness_map.get(self.effectiveness_percentage, 'No definido')
    
    def get_effectiveness_color(self):
        """Color para mostrar la efectividad"""
        if self.effectiveness_percentage >= 90:
            return 'success'
        elif self.effectiveness_percentage >= 70:
            return 'info'
        elif self.effectiveness_percentage >= 40:
            return 'warning'
        else:
            return 'danger'
    
    def __str__(self):
        return f"Evidencia {self.control.name} - {self.evidence_date.strftime('%Y-%m-%d')}"