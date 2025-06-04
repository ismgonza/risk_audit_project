from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AuditProject, RiskMatrix, AuditReport


class RiskMatrixInline(admin.TabularInline):
    """Inline para mostrar matriz de riesgo dentro del proyecto"""
    model = RiskMatrix
    extra = 0
    readonly_fields = (
        'snapshot_date',
        'inherent_score',
        'inherent_level', 
        'residual_score',
        'residual_level',
        'get_risk_reduction_display'
    )
    fields = (
        'risk',
        'snapshot_date',
        'inherent_score',
        'inherent_level',
        'residual_score', 
        'residual_level',
        'get_risk_reduction_display',
        'active_controls_count',
        'approved_controls_count'
    )
    
    def get_risk_reduction_display(self, obj):
        if obj.pk:
            return f"{obj.get_risk_reduction_percentage()}%"
        return ""
    get_risk_reduction_display.short_description = "Reducción"


@admin.register(AuditProject)
class AuditProjectAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'client', 
        'auditor',
        'get_status_badge',
        'start_date',
        'end_date',
        'get_completion_display',
        'get_total_risks',
        'get_high_risks'
    )
    list_filter = (
        'status',
        'start_date',
        'end_date',
        'auditor'
    )
    search_fields = ('name', 'client', 'description')
    filter_horizontal = ('risks', 'team_members')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información del Proyecto', {
            'fields': ('name', 'description', 'client')
        }),
        ('Equipo de Auditoría', {
            'fields': ('auditor', 'team_members')
        }),
        ('Cronograma', {
            'fields': ('start_date', 'end_date', 'status')
        }),
        ('Riesgos Incluidos', {
            'fields': ('risks',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [RiskMatrixInline]
    
    actions = ['create_risk_matrix_snapshot']
    
    def get_status_badge(self, obj):
        """Mostrar estado con badge de color"""
        color = obj.get_status_color()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            self._get_bootstrap_color(color),
            obj.get_status_display()
        )
    get_status_badge.short_description = "Estado"
    
    def get_completion_display(self, obj):
        """Mostrar porcentaje de completitud"""
        percentage = obj.get_completion_percentage()
        
        if percentage >= 80:
            color = 'success'
        elif percentage >= 50:
            color = 'warning'
        else:
            color = 'danger'
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            self._get_bootstrap_color(color),
            f"{percentage}%"
        )
    get_completion_display.short_description = "Completitud"
    
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
    
    def create_risk_matrix_snapshot(self, request, queryset):
        """Acción para crear snapshot de matriz de riesgo"""
        for project in queryset:
            RiskMatrix.create_snapshot(project)
        
        count = queryset.count()
        self.message_user(
            request, 
            f"Se crearon snapshots para {count} proyecto(s)."
        )
    create_risk_matrix_snapshot.short_description = "Crear snapshot de matriz de riesgo"


@admin.register(RiskMatrix)
class RiskMatrixAdmin(admin.ModelAdmin):
    list_display = (
        'risk',
        'audit_project',
        'snapshot_date',
        'get_inherent_risk_display',
        'get_residual_risk_display', 
        'get_reduction_badge',
        'approved_controls_count'
    )
    list_filter = (
        'audit_project',
        'inherent_level',
        'residual_level',
        'snapshot_date'
    )
    search_fields = (
        'risk__code',
        'risk__name', 
        'audit_project__name'
    )
    readonly_fields = (
        'snapshot_date',
        'get_risk_reduction_percentage'
    )
    
    fieldsets = (
        ('Información General', {
            'fields': ('audit_project', 'risk', 'snapshot_date')
        }),
        ('Riesgo Inherente', {
            'fields': (
                'inherent_probability',
                'inherent_impact', 
                'inherent_score',
                'inherent_level'
            )
        }),
        ('Riesgo Residual', {
            'fields': (
                'residual_probability',
                'residual_impact',
                'residual_score', 
                'residual_level'
            )
        }),
        ('Controles', {
            'fields': (
                'active_controls_count',
                'approved_controls_count'
            )
        }),
        ('Análisis', {
            'fields': ('get_risk_reduction_percentage',),
            'classes': ('collapse',)
        }),
    )
    
    def get_inherent_risk_display(self, obj):
        """Mostrar riesgo inherente con color"""
        color = self._get_risk_level_color(obj.inherent_level)
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({})</span>',
            color,
            obj.inherent_score,
            obj.inherent_level
        )
    get_inherent_risk_display.short_description = "Riesgo Inherente"
    
    def get_residual_risk_display(self, obj):
        """Mostrar riesgo residual con color"""
        if obj.residual_score:
            color = self._get_risk_level_color(obj.residual_level)
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} ({})</span>',
                color,
                f"{obj.residual_score:.1f}",
                obj.residual_level
            )
        return "Sin controles"
    get_residual_risk_display.short_description = "Riesgo Residual"
    
    def get_reduction_badge(self, obj):
        """Mostrar porcentaje de reducción"""
        reduction = obj.get_risk_reduction_percentage()
        
        if reduction >= 50:
            color = 'success'
        elif reduction >= 25:
            color = 'warning'
        else:
            color = 'danger'
            
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">-{}</span>',
            self._get_bootstrap_color(color),
            f"{reduction}%"
        )
    get_reduction_badge.short_description = "Reducción"
    
    def _get_risk_level_color(self, level):
        """Color según nivel de riesgo"""
        colors = {
            'LOW': '#28a745',    # Verde
            'MEDIUM': '#ffc107', # Amarillo  
            'HIGH': '#dc3545',   # Rojo
        }
        return colors.get(level, '#6c757d')
    
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


@admin.register(AuditReport)
class AuditReportAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'audit_project',
        'report_type',
        'generated_by',
        'generated_at',
        'get_download_link'
    )
    list_filter = (
        'report_type',
        'generated_at',
        'generated_by'
    )
    search_fields = (
        'title',
        'audit_project__name',
        'content'
    )
    readonly_fields = ('generated_at',)
    
    fieldsets = (
        ('Información del Reporte', {
            'fields': ('audit_project', 'title', 'report_type', 'generated_by')
        }),
        ('Contenido', {
            'fields': ('content', 'report_file')
        }),
        ('Metadatos', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_download_link(self, obj):
        """Link para descargar el reporte"""
        if obj.report_file:
            return format_html(
                '<a href="{}" target="_blank" style="color: #007bff;">📄 Descargar</a>',
                obj.report_file.url
            )
        return "Sin archivo"
    get_download_link.short_description = "Archivo"
    
    def save_model(self, request, obj, form, change):
        """Asignar usuario actual si es un nuevo reporte"""
        if not change:  # Si es un nuevo objeto
            obj.generated_by = request.user
        super().save_model(request, obj, form, change)