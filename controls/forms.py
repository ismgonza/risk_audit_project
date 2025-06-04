from django import forms
from django.contrib.auth.models import User
from .models import Control, ControlEvidence
from risks.models import Risk


class ControlForm(forms.ModelForm):
    """Formulario para crear y editar controles"""
    
    class Meta:
        model = Control
        fields = [
            'risk', 'name', 'description', 'control_type', 
            'frequency', 'responsible_person', 'is_active'
        ]
        widgets = {
            'risk': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Selecciona el riesgo'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo del control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe cómo funciona este control y qué mitiga...'
            }),
            'control_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'frequency': forms.Select(attrs={
                'class': 'form-select'
            }),
            'responsible_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del responsable de ejecutar el control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'risk': 'Riesgo a Controlar',
            'name': 'Nombre del Control',
            'description': 'Descripción Detallada',
            'control_type': 'Tipo de Control',
            'frequency': 'Frecuencia de Ejecución',
            'responsible_person': 'Persona Responsable',
            'is_active': 'Control Activo',
        }
        help_texts = {
            'name': 'Debe ser claro y específico sobre qué hace el control',
            'description': 'Incluye procedimientos, herramientas y criterios de éxito',
            'control_type': 'Preventivo: evita el riesgo | Detectivo: identifica cuando ocurre | Correctivo: mitiga el impacto',
            'frequency': 'Con qué frecuencia se ejecuta este control',
            'responsible_person': 'Quién es responsable de asegurar que se ejecute',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ordenar riesgos por código
        self.fields['risk'].queryset = Risk.objects.all().order_by('code')
        
        # Configurar required fields
        self.fields['risk'].required = True
        self.fields['name'].required = True
        self.fields['description'].required = True
        self.fields['responsible_person'].required = True
        
        # Valores por defecto
        if not self.instance.pk:
            self.fields['is_active'].initial = True
    
    def clean_name(self):
        """Validar que el nombre no esté duplicado para el mismo riesgo"""
        name = self.cleaned_data.get('name')
        risk = self.cleaned_data.get('risk')
        
        if name and risk:
            existing = Control.objects.filter(
                name__iexact=name,
                risk=risk
            )
            
            # Si estamos editando, excluir el control actual
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    f'Ya existe un control con este nombre para el riesgo {risk.code}'
                )
        
        return name


class ControlEvidenceForm(forms.ModelForm):
    """Formulario para agregar evidencias de controles"""
    
    class Meta:
        model = ControlEvidence
        fields = [
            'evidence_date', 'description', 'effectiveness_percentage', 'document'
        ]
        widgets = {
            'evidence_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe la evidencia, cómo se ejecutó el control, resultados obtenidos...'
            }),
            'effectiveness_percentage': forms.Select(attrs={
                'class': 'form-select'
            }),
            'document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png'
            }),
        }
        labels = {
            'evidence_date': 'Fecha de la Evidencia',
            'description': 'Descripción de la Evidencia',
            'effectiveness_percentage': 'Nivel de Efectividad',
            'document': 'Documento de Soporte (Opcional)',
        }
        help_texts = {
            'evidence_date': 'Cuándo se ejecutó el control o se recopiló la evidencia',
            'description': 'Explica qué evidencia tienes de que el control funcionó',
            'effectiveness_percentage': 'Qué tan efectivo fue el control en esta ocasión',
            'document': 'Archivo que respalda la evidencia (reportes, capturas, logs, etc.)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar required fields
        self.fields['evidence_date'].required = True
        self.fields['description'].required = True
        self.fields['effectiveness_percentage'].required = True
        
        # Valor por defecto para fecha
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['evidence_date'].initial = timezone.now()
    
    def clean_document(self):
        """Validar el archivo subido"""
        document = self.cleaned_data.get('document')
        
        if document:
            # Validar tamaño (max 10MB)
            if document.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    'El archivo es demasiado grande. Máximo 10MB permitido.'
                )
            
            # Validar extensión
            allowed_extensions = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                '.jpg', '.jpeg', '.png', '.txt', '.csv'
            ]
            
            file_extension = document.name.lower()
            if not any(file_extension.endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError(
                    'Tipo de archivo no permitido. Formatos aceptados: ' +
                    ', '.join(allowed_extensions)
                )
        
        return document


class ControlApprovalForm(forms.Form):
    """Formulario para aprobar/rechazar controles"""
    
    ACTION_CHOICES = [
        ('APPROVED', 'Aprobar'),
        ('REJECTED', 'Rechazar'),
        ('NEEDS_REVISION', 'Necesita Revisión'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Decisión del Auditor'
    )
    
    feedback = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Comentarios para el creador del control...'
        }),
        label='Comentarios',
        required=False,
        help_text='Opcional: proporciona retroalimentación sobre la decisión'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        feedback = cleaned_data.get('feedback')
        
        # Requerir comentarios para rechazos o revisiones
        if action in ['REJECTED', 'NEEDS_REVISION'] and not feedback:
            raise forms.ValidationError(
                'Los comentarios son obligatorios cuando se rechaza o solicita revisión'
            )
        
        return cleaned_data


class EvidenceValidationForm(forms.Form):
    """Formulario para validar evidencias"""
    
    action = forms.ChoiceField(
        choices=[
            ('validate', 'Validar Evidencia'),
            ('reject', 'Rechazar Evidencia'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Decisión del Auditor'
    )
    
    review = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Comentarios sobre la validación...'
        }),
        label='Revisión del Auditor',
        required=False,
        help_text='Opcional: comentarios sobre la calidad y validez de la evidencia'
    )


class BulkControlActionForm(forms.Form):
    """Formulario para acciones en lote sobre controles"""
    
    ACTION_CHOICES = [
        ('activate', 'Activar Controles'),
        ('deactivate', 'Desactivar Controles'),
        ('approve', 'Aprobar Controles'),
        ('reject', 'Rechazar Controles'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Acción a Realizar'
    )
    
    control_ids = forms.CharField(
        widget=forms.HiddenInput(),
        label='IDs de Controles'
    )
    
    feedback = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Comentarios para la acción en lote...'
        }),
        label='Comentarios',
        required=False
    )
    
    def clean_control_ids(self):
        """Validar que los IDs de controles sean válidos"""
        control_ids = self.cleaned_data.get('control_ids', '')
        
        try:
            ids = [int(id.strip()) for id in control_ids.split(',') if id.strip()]
            
            # Verificar que todos los controles existan
            existing_count = Control.objects.filter(id__in=ids).count()
            if existing_count != len(ids):
                raise forms.ValidationError('Algunos controles seleccionados no existen')
            
            return ids
        except ValueError:
            raise forms.ValidationError('IDs de controles inválidos')