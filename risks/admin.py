from django.contrib import admin
from .models import RiskCategory, Risk


@admin.register(RiskCategory)
class RiskCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'risk_appetite', 'description')
    list_filter = ('risk_appetite',)
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = (
        'code', 
        'name', 
        'category', 
        'probability', 
        'impact', 
        'inherent_risk_score',
        'inherent_risk_level',
        'get_residual_display',
        'created_by',
        'created_at'
    )
    list_filter = (
        'category', 
        'inherent_risk_level', 
        'residual_risk_level',
        'created_at'
    )
    search_fields = ('code', 'name', 'description')
    readonly_fields = (
        'inherent_risk_score', 
        'inherent_risk_level',
        'residual_probability',
        'residual_impact', 
        'residual_risk_score', 
        'residual_risk_level',
        'created_at', 
        'updated_at'
    )
    fieldsets = (
        ('Información Básica', {
            'fields': ('code', 'name', 'description', 'category', 'created_by')
        }),
        ('Evaluación de Riesgo Inherente', {
            'fields': ('probability', 'impact', 'inherent_risk_score', 'inherent_risk_level')
        }),
        ('Riesgo Residual (Calculado automáticamente)', {
            'fields': (
                'residual_probability', 
                'residual_impact', 
                'residual_risk_score', 
                'residual_risk_level'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('code',)
    
    def get_residual_display(self, obj):
        """Mostrar riesgo residual en la lista"""
        if obj.residual_risk_score:
            return f"{obj.residual_risk_score:.1f} ({obj.residual_risk_level})"
        return "Sin controles"
    get_residual_display.short_description = "Riesgo Residual"
    
    def save_model(self, request, obj, form, change):
        """Asignar usuario actual si es un nuevo riesgo"""
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)