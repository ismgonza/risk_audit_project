from django.contrib import admin
from django.utils.html import format_html
from .models import Control, ControlEvidence


class ControlEvidenceInline(admin.TabularInline):
    """Inline para mostrar evidencias dentro del control"""
    model = ControlEvidence
    extra = 0
    readonly_fields = ('uploaded_at', 'get_effectiveness_display_short')
    fields = (
        'evidence_date', 
        'description', 
        'effectiveness_percentage',
        'get_effectiveness_display_short',
        'document', 
        'is_validated',
        'auditor_review',
        'uploaded_by',
        'uploaded_at'
    )
    
    def get_effectiveness_display_short(self, obj):
        return obj.get_effectiveness_display_short() if obj.pk else ""
    get_effectiveness_display_short.short_description = "Efectividad"


@admin.register(Control)
class ControlAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'risk',
        'control_type',
        'frequency',
        'get_approval_status',
        'get_effectiveness_display',
        'is_active',
        'created_by',
        'created_at'
    )
    list_filter = (
        'control_type',
        'frequency',
        'auditor_approval',
        'is_active',
        'created_at'
    )
    search_fields = ('name', 'description', 'risk__name', 'risk__code')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('risk', 'name', 'description', 'created_by')
        }),
        ('Configuración del Control', {
            'fields': ('control_type', 'frequency', 'responsible_person', 'is_active')
        }),
        ('Revisión del Auditor', {
            'fields': ('auditor_approval', 'auditor_feedback', 'auditor'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ControlEvidenceInline]
    
    def get_approval_status(self, obj):
        """Mostrar estado de aprobación con color"""
        color = obj.get_approval_color()
        return format_html(
            '<span class="badge" style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            self._get_bootstrap_color(color),
            obj.get_auditor_approval_display()
        )
    get_approval_status.short_description = "Estado de Aprobación"
    
    def get_effectiveness_display(self, obj):
        """Mostrar efectividad del control"""
        effectiveness = obj.get_overall_effectiveness()
        percentage = effectiveness * 100
        
        if percentage >= 90:
            color = 'success'
        elif percentage >= 70:
            color = 'info'
        elif percentage >= 40:
            color = 'warning'
        else:
            color = 'danger'
            
        return format_html(
            '<span style="color: {};">{}</span>',
            self._get_bootstrap_color(color),
            f"{percentage:.1f}%"
        )
    get_effectiveness_display.short_description = "Efectividad"
    
    def _get_bootstrap_color(self, color_name):
        """Convertir nombre de color Bootstrap a código hexadecimal"""
        colors = {
            'success': '#28a745',
            'info': '#17a2b8',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'primary': '#007bff',
            'secondary': '#6c757d'
        }
        return colors.get(color_name, '#6c757d')
    
    def save_model(self, request, obj, form, change):
        """Asignar usuario actual si es un nuevo control"""
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        
        # Si es staff y está aprobando/rechazando, asignar como auditor
        if request.user.is_staff and 'auditor_approval' in form.changed_data:
            obj.auditor = request.user
            
        super().save_model(request, obj, form, change)
        
        # Recalcular riesgo residual si se aprueba o rechaza
        if 'auditor_approval' in form.changed_data:
            obj.risk.calculate_residual_risk()


@admin.register(ControlEvidence)
class ControlEvidenceAdmin(admin.ModelAdmin):
    list_display = (
        'control',
        'evidence_date',
        'get_effectiveness_badge',
        'get_validation_status',
        'uploaded_by',
        'uploaded_at'
    )
    list_filter = (
        'effectiveness_percentage',
        'is_validated',
        'evidence_date',
        'uploaded_at'
    )
    search_fields = (
        'control__name', 
        'control__risk__name', 
        'control__risk__code',
        'description'
    )
    readonly_fields = ('uploaded_at', 'validation_date')
    
    fieldsets = (
        ('Información de la Evidencia', {
            'fields': ('control', 'evidence_date', 'description', 'uploaded_by')
        }),
        ('Evaluación de Efectividad', {
            'fields': ('effectiveness_percentage', 'document')
        }),
        ('Validación del Auditor', {
            'fields': (
                'is_validated', 
                'validated_by', 
                'validation_date',
                'auditor_review'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_effectiveness_badge(self, obj):
        """Mostrar efectividad con badge de color"""
        color = obj.get_effectiveness_color()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            self._get_bootstrap_color(color),
            obj.get_effectiveness_display_short()
        )
    get_effectiveness_badge.short_description = "Efectividad"
    
    def get_validation_status(self, obj):
        """Mostrar estado de validación"""
        if obj.is_validated:
            return format_html(
                '<span style="color: #28a745;">✓ Validado</span>'
            )
        else:
            return format_html(
                '<span style="color: #ffc107;">⏳ Pendiente</span>'
            )
    get_validation_status.short_description = "Validación"
    
    def _get_bootstrap_color(self, color_name):
        """Convertir nombre de color Bootstrap a código hexadecimal"""
        colors = {
            'success': '#28a745',
            'info': '#17a2b8',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'primary': '#007bff',
            'secondary': '#6c757d'
        }
        return colors.get(color_name, '#6c757d')
    
    def save_model(self, request, obj, form, change):
        """Configuraciones especiales al guardar evidencia"""
        if not change:  # Si es un nuevo objeto
            obj.uploaded_by = request.user
        
        # Si es staff y está validando, asignar como validador
        if request.user.is_staff and 'is_validated' in form.changed_data and obj.is_validated:
            obj.validated_by = request.user
            from django.utils import timezone
            obj.validation_date = timezone.now()
            
        super().save_model(request, obj, form, change)
        
        # Recalcular riesgo residual cuando se valida evidencia
        if 'is_validated' in form.changed_data:
            obj.control.risk.calculate_residual_risk()