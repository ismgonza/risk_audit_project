from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class RiskCategory(models.Model):
    """Categorías de riesgo con apetito de riesgo definido"""
    
    RISK_APPETITE_CHOICES = [
        ('LOW', 'Bajo'),
        ('MEDIUM', 'Medio'),
        ('HIGH', 'Alto'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nombre de Categoría")
    description = models.TextField(blank=True, verbose_name="Descripción")
    risk_appetite = models.CharField(
        max_length=20,
        choices=RISK_APPETITE_CHOICES,
        verbose_name="Apetito de Riesgo"
    )
    
    class Meta:
        verbose_name = "Categoría de Riesgo"
        verbose_name_plural = "Categorías de Riesgo"
    
    def __str__(self):
        return self.name


class Risk(models.Model):
    """Modelo principal para gestión de riesgos"""
    
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Bajo (1-5)'),
        ('MEDIUM', 'Medio (6-10)'),
        ('HIGH', 'Alto (11-15)'),
    ]
    
    # Información básica del riesgo
    code = models.CharField(max_length=20, unique=True, verbose_name="Código de Riesgo")
    name = models.CharField(max_length=200, verbose_name="Nombre del Riesgo")
    description = models.TextField(verbose_name="Descripción del Riesgo")
    category = models.ForeignKey(RiskCategory, on_delete=models.CASCADE, verbose_name="Categoría")
    
    # Evaluación del riesgo inherente
    probability = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        verbose_name="Probabilidad (1-3)",
        help_text="1=Baja, 2=Media, 3=Alta"
    )
    impact = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Impacto (1-5)",
        help_text="1=Muy Bajo, 2=Bajo, 3=Medio, 4=Alto, 5=Muy Alto"
    )
    
    # Campos calculados automáticamente
    inherent_risk_score = models.IntegerField(
        editable=False, 
        verbose_name="Puntuación de Riesgo Inherente"
    )
    inherent_risk_level = models.CharField(
        max_length=10, 
        choices=RISK_LEVEL_CHOICES, 
        editable=False,
        verbose_name="Nivel de Riesgo Inherente"
    )
    
    # Riesgo residual (después de aplicar controles)
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
    residual_risk_score = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name="Puntuación de Riesgo Residual"
    )
    residual_risk_level = models.CharField(
        max_length=10, 
        choices=RISK_LEVEL_CHOICES, 
        null=True, 
        blank=True,
        verbose_name="Nivel de Riesgo Residual"
    )
    
    # Metadatos
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Creado por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    
    class Meta:
        verbose_name = "Riesgo"
        verbose_name_plural = "Riesgos"
        ordering = ['code']
    
    def save(self, *args, **kwargs):
        """Calcular automáticamente el riesgo inherente al guardar"""
        self.inherent_risk_score = self.probability * self.impact
        
        # Determinar nivel de riesgo inherente
        if self.inherent_risk_score <= 5:
            self.inherent_risk_level = 'LOW'
        elif self.inherent_risk_score <= 10:
            self.inherent_risk_level = 'MEDIUM'
        else:
            self.inherent_risk_level = 'HIGH'
        
        super().save(*args, **kwargs)
    
    def calculate_residual_risk(self):
        """Recalcula el riesgo residual basado en los controles activos y aprobados"""
        # Importar aquí para evitar import circular
        from controls.models import Control
        
        controls = Control.objects.filter(
            risk=self, 
            is_active=True, 
            auditor_approval='APPROVED'
        )
        
        if not controls.exists():
            # Sin controles, el riesgo residual es igual al inherente
            self.residual_probability = float(self.probability)
            self.residual_impact = float(self.impact)
        else:
            # Aplicar reducción de controles
            prob_reduction = 0
            impact_reduction = 0
            
            for control in controls:
                effectiveness = control.get_overall_effectiveness()
                
                # Los controles preventivos reducen probabilidad
                if control.control_type in ['PREVENTIVE', 'BOTH']:
                    prob_reduction += effectiveness * (1 - prob_reduction)
                
                # Los controles detectivos y correctivos reducen impacto
                if control.control_type in ['DETECTIVE', 'CORRECTIVE', 'BOTH']:
                    impact_reduction += effectiveness * (1 - impact_reduction)
            
            # Aplicar las reducciones
            self.residual_probability = self.probability * (1 - prob_reduction)
            self.residual_impact = self.impact * (1 - impact_reduction)
        
        # Calcular puntuación y nivel residual
        self.residual_risk_score = self.residual_probability * self.residual_impact
        
        if self.residual_risk_score <= 5:
            self.residual_risk_level = 'LOW'
        elif self.residual_risk_score <= 10:
            self.residual_risk_level = 'MEDIUM'
        else:
            self.residual_risk_level = 'HIGH'
        
        self.save()
    
    def get_risk_color(self, risk_type='inherent'):
        """Retorna color para mostrar en templates"""
        level = self.inherent_risk_level if risk_type == 'inherent' else self.residual_risk_level
        
        colors = {
            'LOW': 'success',    # Verde
            'MEDIUM': 'warning', # Amarillo
            'HIGH': 'danger',    # Rojo
        }
        return colors.get(level, 'secondary')
    
    def __str__(self):
        return f"{self.code} - {self.name}"