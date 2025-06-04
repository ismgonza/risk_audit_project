from django.db import models
from django.contrib.auth.models import User
from risks.models import Risk


class AuditProject(models.Model):
    """Proyectos de auditoría que agrupan riesgos y controles"""
    
    STATUS_CHOICES = [
        ('PLANNING', 'Planificación'),
        ('IN_PROGRESS', 'En Progreso'),
        ('REVIEW', 'En Revisión'),
        ('COMPLETED', 'Completado'),
        ('CANCELLED', 'Cancelado'),
    ]
    
    # Información básica del proyecto
    name = models.CharField(max_length=200, verbose_name="Nombre del Proyecto de Auditoría")
    description = models.TextField(verbose_name="Descripción")
    client = models.CharField(max_length=100, verbose_name="Cliente")
    
    # Equipo de auditoría
    auditor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Auditor Principal"
    )
    team_members = models.ManyToManyField(
        User,
        blank=True,
        related_name='audit_team_projects',
        verbose_name="Miembros del Equipo"
    )
    
    # Fechas del proyecto
    start_date = models.DateField(verbose_name="Fecha de Inicio")
    end_date = models.DateField(verbose_name="Fecha de Finalización")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PLANNING',
        verbose_name="Estado del Proyecto"
    )
    
    # Riesgos incluidos en la auditoría
    risks = models.ManyToManyField(Risk, verbose_name="Riesgos Incluidos")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    
    class Meta:
        verbose_name = "Proyecto de Auditoría"
        verbose_name_plural = "Proyectos de Auditoría"
        ordering = ['-created_at']
    
    def get_total_risks(self):
        """Número total de riesgos en el proyecto"""
        return self.risks.count()
    
    def get_high_risks(self):
        """Número de riesgos altos"""
        return self.risks.filter(inherent_risk_level='HIGH').count()
    
    def get_risks_with_controls(self):
        """Número de riesgos que tienen controles"""
        return self.risks.filter(control__isnull=False).distinct().count()
    
    def get_completion_percentage(self):
        """Porcentaje de completitud del proyecto"""
        total_risks = self.get_total_risks()
        if total_risks == 0:
            return 0
        
        risks_with_approved_controls = self.risks.filter(
            control__auditor_approval='APPROVED'
        ).distinct().count()
        
        return round((risks_with_approved_controls / total_risks) * 100, 1)
    
    def get_status_color(self):
        """Color para mostrar el estado del proyecto"""
        colors = {
            'PLANNING': 'secondary',
            'IN_PROGRESS': 'primary',
            'REVIEW': 'warning',
            'COMPLETED': 'success',
            'CANCELLED': 'danger',
        }
        return colors.get(self.status, 'secondary')
    
    def __str__(self):
        return f"{self.name} - {self.client}"


class RiskMatrix(models.Model):
    """Snapshot de la matriz de riesgo en un momento específico"""
    
    audit_project = models.ForeignKey(
        AuditProject, 
        on_delete=models.CASCADE,
        verbose_name="Proyecto de Auditoría"
    )
    risk = models.ForeignKey(Risk, on_delete=models.CASCADE, verbose_name="Riesgo")
    
    # Timestamp del snapshot
    snapshot_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Snapshot")
    
    # Valores del riesgo inherente al momento del snapshot
    inherent_probability = models.IntegerField(verbose_name="Probabilidad Inherente")
    inherent_impact = models.IntegerField(verbose_name="Impacto Inherente")
    inherent_score = models.IntegerField(verbose_name="Puntuación Inherente")
    inherent_level = models.CharField(max_length=10, verbose_name="Nivel Inherente")
    
    # Valores del riesgo residual al momento del snapshot
    residual_probability = models.FloatField(
        null=True, 
        blank=True,
        verbose_name="Probabilidad Residual"
    )
    residual_impact = models.FloatField(
        null=True, 
        blank=True,
        verbose_name="Impacto Residual"
    )
    residual_score = models.FloatField(
        null=True, 
        blank=True,
        verbose_name="Puntuación Residual"
    )
    residual_level = models.CharField(
        max_length=10, 
        null=True, 
        blank=True,
        verbose_name="Nivel Residual"
    )
    
    # Número de controles activos al momento del snapshot
    active_controls_count = models.IntegerField(
        default=0,
        verbose_name="Número de Controles Activos"
    )
    approved_controls_count = models.IntegerField(
        default=0,
        verbose_name="Número de Controles Aprobados"
    )
    
    class Meta:
        verbose_name = "Matriz de Riesgo"
        verbose_name_plural = "Matrices de Riesgo"
        unique_together = ['audit_project', 'risk', 'snapshot_date']
        ordering = ['-snapshot_date']
    
    @classmethod
    def create_snapshot(cls, audit_project):
        """Crear un snapshot de todos los riesgos del proyecto"""
        snapshots = []
        
        for risk in audit_project.risks.all():
            # Contar controles
            active_controls = risk.control_set.filter(is_active=True).count()
            approved_controls = risk.control_set.filter(
                is_active=True, 
                auditor_approval='APPROVED'
            ).count()
            
            snapshot = cls.objects.create(
                audit_project=audit_project,
                risk=risk,
                inherent_probability=risk.probability,
                inherent_impact=risk.impact,
                inherent_score=risk.inherent_risk_score,
                inherent_level=risk.inherent_risk_level,
                residual_probability=risk.residual_probability,
                residual_impact=risk.residual_impact,
                residual_score=risk.residual_risk_score,
                residual_level=risk.residual_risk_level,
                active_controls_count=active_controls,
                approved_controls_count=approved_controls,
            )
            snapshots.append(snapshot)
        
        return snapshots
    
    def get_risk_reduction_percentage(self):
        """Calcula el porcentaje de reducción del riesgo"""
        if not self.residual_score:
            return 0
        
        reduction = ((self.inherent_score - self.residual_score) / self.inherent_score) * 100
        return round(max(0, reduction), 1)
    
    def __str__(self):
        return f"{self.risk.code} - {self.snapshot_date.strftime('%Y-%m-%d %H:%M')}"


class AuditReport(models.Model):
    """Reportes de auditoría generados"""
    
    REPORT_TYPE_CHOICES = [
        ('RISK_MATRIX', 'Matriz de Riesgo'),
        ('CONTROL_EFFECTIVENESS', 'Efectividad de Controles'),
        ('EXECUTIVE_SUMMARY', 'Resumen Ejecutivo'),
        ('DETAILED_FINDINGS', 'Hallazgos Detallados'),
    ]
    
    audit_project = models.ForeignKey(
        AuditProject,
        on_delete=models.CASCADE,
        verbose_name="Proyecto de Auditoría"
    )
    
    # Información del reporte
    title = models.CharField(max_length=200, verbose_name="Título del Reporte")
    report_type = models.CharField(
        max_length=30,
        choices=REPORT_TYPE_CHOICES,
        verbose_name="Tipo de Reporte"
    )
    content = models.TextField(verbose_name="Contenido del Reporte")
    
    # Archivo generado
    report_file = models.FileField(
        upload_to='audit_reports/',
        null=True,
        blank=True,
        verbose_name="Archivo del Reporte"
    )
    
    # Metadatos
    generated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Generado por"
    )
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Generación")
    
    class Meta:
        verbose_name = "Reporte de Auditoría"
        verbose_name_plural = "Reportes de Auditoría"
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} - {self.audit_project.name}"