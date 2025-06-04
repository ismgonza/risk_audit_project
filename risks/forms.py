from django import forms
from django.contrib.auth.models import User
from .models import Risk, RiskCategory


class RiskForm(forms.ModelForm):
    """Formulario para crear y editar riesgos"""
    
    class Meta:
        model = Risk
        fields = [
            'code', 'name', 'description', 'category', 
            'probability', 'impact'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: OP-001, FN-002, TI-003',
                'pattern': '[A-Z]{2}-[0-9]{3}',
                'title': 'Formato: 2 letras mayúsculas, guión, 3 números'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo del riesgo'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe detalladamente el riesgo, sus causas y posibles consecuencias...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'probability': forms.Select(
                choices=[
                    ('', 'Seleccione la probabilidad'),
                    (1, '1 - Baja (Raro que ocurra)'),
                    (2, '2 - Media (Puede ocurrir)'),
                    (3, '3 - Alta (Muy probable)'),
                ],
                attrs={'class': 'form-select'}
            ),
            'impact': forms.Select(
                choices=[
                    ('', 'Seleccione el impacto'),
                    (1, '1 - Muy Bajo (Mínimo impacto)'),
                    (2, '2 - Bajo (Impacto menor)'),
                    (3, '3 - Medio (Impacto moderado)'),
                    (4, '4 - Alto (Impacto significativo)'),
                    (5, '5 - Muy Alto (Impacto crítico)'),
                ],
                attrs={'class': 'form-select'}
            ),
        }
        labels = {
            'code': 'Código del Riesgo',
            'name': 'Nombre del Riesgo',
            'description': 'Descripción Detallada',
            'category': 'Categoría',
            'probability': 'Probabilidad de Ocurrencia',
            'impact': 'Impacto si Ocurre',
        }
        help_texts = {
            'code': 'Código único para identificar el riesgo (ej: OP-001 para Operacional)',
            'name': 'Nombre claro y específico que identifique el riesgo',
            'description': 'Explique qué es el riesgo, qué lo causa y qué consecuencias puede tener',
            'probability': '1=Baja (raro que ocurra), 2=Media (puede ocurrir), 3=Alta (muy probable)',
            'impact': '1=Muy Bajo, 2=Bajo, 3=Medio, 4=Alto, 5=Muy Alto (en términos de daño)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Asegurar que haya categorías disponibles
        if not RiskCategory.objects.exists():
            self.fields['category'].widget.attrs['disabled'] = True
            self.fields['category'].help_text = 'Primero debe crear categorías de riesgo en el admin'
        
        # Configurar required fields
        for field_name, field in self.fields.items():
            field.required = True
            
        # Agregar asterisco a labels requeridos
        for field_name in self.fields:
            if self.fields[field_name].required:
                self.fields[field_name].label += ' *'
    
    def clean_code(self):
        """Validar que el código sea único y tenga el formato correcto"""
        code = self.cleaned_data.get('code', '').upper().strip()
        
        if not code:
            raise forms.ValidationError('El código es obligatorio')
        
        # Validar formato
        import re
        if not re.match(r'^[A-Z]{2}-[0-9]{3}$', code):
            raise forms.ValidationError(
                'El código debe tener el formato: 2 letras mayúsculas, guión, 3 números (ej: OP-001)'
            )
        
        # Validar unicidad
        existing = Risk.objects.filter(code=code)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise forms.ValidationError(f'Ya existe un riesgo con el código {code}')
        
        return code
    
    def clean_name(self):
        """Validar el nombre del riesgo"""
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise forms.ValidationError('El nombre es obligatorio')
        
        if len(name) < 10:
            raise forms.ValidationError('El nombre debe tener al menos 10 caracteres')
        
        if len(name) > 200:
            raise forms.ValidationError('El nombre no puede exceder 200 caracteres')
        
        return name
    
    def clean_description(self):
        """Validar la descripción"""
        description = self.cleaned_data.get('description', '').strip()
        
        if not description:
            raise forms.ValidationError('La descripción es obligatoria')
        
        if len(description) < 20:
            raise forms.ValidationError('La descripción debe tener al menos 20 caracteres')
        
        if len(description) > 2000:
            raise forms.ValidationError('La descripción no puede exceder 2000 caracteres')
        
        return description
    
    def clean(self):
        """Validaciones adicionales del formulario completo"""
        cleaned_data = super().clean()
        probability = cleaned_data.get('probability')
        impact = cleaned_data.get('impact')
        category = cleaned_data.get('category')
        
        # Validar que probabilidad e impacto estén en rangos correctos
        if probability and (probability < 1 or probability > 3):
            raise forms.ValidationError('La probabilidad debe estar entre 1 y 3')
        
        if impact and (impact < 1 or impact > 5):
            raise forms.ValidationError('El impacto debe estar entre 1 y 5')
        
        # Sugerir revisión para riesgos muy altos
        if probability and impact:
            score = probability * impact
            if score >= 12:  # Riesgo muy alto
                self.add_error(None, 
                    'Este riesgo tendrá una puntuación muy alta ({}). '
                    'Asegúrese de que la evaluación sea correcta.'.format(score)
                )
        
        return cleaned_data


class RiskCategoryForm(forms.ModelForm):
    """Formulario para crear categorías de riesgo (uso futuro)"""
    
    class Meta:
        model = RiskCategory
        fields = ['name', 'description', 'risk_appetite']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la categoría...'
            }),
            'risk_appetite': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def clean_name(self):
        """Validar unicidad del nombre"""
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise forms.ValidationError('El nombre es obligatorio')
        
        # Validar unicidad
        existing = RiskCategory.objects.filter(name__iexact=name)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise forms.ValidationError(f'Ya existe una categoría con el nombre "{name}"')
        
        return name