from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import Risk, RiskCategory
from .forms import RiskForm
from controls.models import Control

@login_required
def dashboard(request):
    """Dashboard principal con resumen de riesgos"""
    risks = Risk.objects.all()
    
    # Estadísticas generales
    total_risks = risks.count()
    high_risks = risks.filter(inherent_risk_level='HIGH').count()
    medium_risks = risks.filter(inherent_risk_level='MEDIUM').count()
    low_risks = risks.filter(inherent_risk_level='LOW').count()
    
    # Riesgos con controles
    risks_with_controls = risks.filter(control__isnull=False).distinct().count()
    
    # Controles pendientes de aprobación
    pending_controls = Control.objects.filter(auditor_approval='PENDING').count()
    
    # Riesgos por categoría
    categories_stats = []
    for category in RiskCategory.objects.all():
        cat_risks = risks.filter(category=category)
        categories_stats.append({
            'category': category,
            'total': cat_risks.count(),
            'high': cat_risks.filter(inherent_risk_level='HIGH').count(),
            'medium': cat_risks.filter(inherent_risk_level='MEDIUM').count(),
            'low': cat_risks.filter(inherent_risk_level='LOW').count(),
        })
    
    # Riesgos recientes
    recent_risks = risks.order_by('-created_at')[:5]
    
    # Calcular porcentajes para el gráfico
    if total_risks > 0:
        low_percentage = round((low_risks / total_risks) * 100, 1)
        medium_percentage = round((medium_risks / total_risks) * 100, 1)
        high_percentage = round((high_risks / total_risks) * 100, 1)
    else:
        low_percentage = medium_percentage = high_percentage = 0

    context = {
        'total_risks': total_risks,
        'high_risks': high_risks,
        'medium_risks': medium_risks,
        'low_risks': low_risks,
        'risks_with_controls': risks_with_controls,
        'pending_controls': pending_controls,
        'categories_stats': categories_stats,
        'recent_risks': recent_risks,
        'low_percentage': low_percentage,
        'medium_percentage': medium_percentage,
        'high_percentage': high_percentage,
    }
    
    return render(request, 'risks/dashboard.html', context)

@login_required
def risk_list(request):
    """Lista de riesgos con filtros"""
    risks = Risk.objects.all().select_related('category', 'created_by').prefetch_related('control_set')
    
    # Filtros
    search = request.GET.get('search')
    if search:
        risks = risks.filter(
            Q(code__icontains=search) | 
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    category_filter = request.GET.get('category')
    if category_filter:
        risks = risks.filter(category_id=category_filter)
    
    level_filter = request.GET.get('level')
    if level_filter:
        risks = risks.filter(inherent_risk_level=level_filter)
    
    # Ordenar por código por defecto
    sort_by = request.GET.get('sort', 'code')
    valid_sorts = ['code', '-code', 'name', '-name', 'inherent_risk_score', '-inherent_risk_score', 'created_at', '-created_at']
    if sort_by in valid_sorts:
        risks = risks.order_by(sort_by)
    else:
        risks = risks.order_by('code')
    
    # Agregar datos calculados para cada riesgo
    risks_with_data = []
    for risk in risks:
        controls = risk.control_set.all()
        approved_controls = controls.filter(auditor_approval='APPROVED', is_active=True)
        
        risk_data = {
            'risk': risk,
            'total_controls': controls.count(),
            'approved_controls': approved_controls.count(),
            'has_residual': risk.residual_risk_score is not None,
        }
        risks_with_data.append(risk_data)
    
    context = {
        'risks_with_data': risks_with_data,
        'categories': RiskCategory.objects.all(),
        'search': search,
        'category_filter': category_filter,
        'level_filter': level_filter,
        'sort_by': sort_by,
        'total_risks': len(risks_with_data),
    }
    
    return render(request, 'risks/risk_list.html', context)

@login_required
def risk_detail(request, pk):
    """Detalle de riesgo con controles asociados"""
    risk = get_object_or_404(Risk, pk=pk)
    controls = Control.objects.filter(risk=risk).order_by('-created_at')
    
    context = {
        'risk': risk,
        'controls': controls,
        'can_edit': risk.created_by == request.user or request.user.is_staff,
    }
    
    return render(request, 'risks/risk_detail.html', context)

@login_required
def risk_matrix(request):
    """Matriz de riesgo visual"""
    risks = Risk.objects.all().select_related('category')
    
    # Organizar riesgos por probabilidad e impacto
    matrix_data = {}
    for prob in range(1, 4):  # Probabilidad 1-3
        matrix_data[prob] = {}
        for imp in range(1, 6):  # Impacto 1-5
            matrix_data[prob][imp] = []
    
    # Llenar la matriz con los riesgos
    for risk in risks:
        matrix_data[risk.probability][risk.impact].append(risk)
    
    # Convertir a una estructura más fácil para el template
    matrix_cells = []
    for prob in range(3, 0, -1):  # De mayor a menor probabilidad
        row = []
        for imp in range(1, 6):  # De menor a mayor impacto
            cell_risks = matrix_data[prob][imp]
            score = prob * imp
            
            # Determinar clase de riesgo
            if score <= 5:
                risk_class = 'risk-low'
            elif score <= 10:
                risk_class = 'risk-medium'
            else:
                risk_class = 'risk-high'
            
            row.append({
                'probability': prob,
                'impact': imp,
                'score': score,
                'risk_class': risk_class,
                'risks': cell_risks
            })
        matrix_cells.append(row)
    
    # Estadísticas para mostrar
    total_risks = risks.count()
    high_risks = risks.filter(inherent_risk_level='HIGH').count()
    medium_risks = risks.filter(inherent_risk_level='MEDIUM').count()
    low_risks = risks.filter(inherent_risk_level='LOW').count()
    
    # Obtener todas las categorías para el filtro
    categories = RiskCategory.objects.all()
    
    context = {
        'matrix_cells': matrix_cells,
        'probabilities': range(1, 4),
        'impacts': range(1, 6),
        'total_risks': total_risks,
        'high_risks': high_risks,
        'medium_risks': medium_risks,
        'low_risks': low_risks,
        'categories': categories,
    }
    
    return render(request, 'risks/risk_matrix.html', context)

@login_required
def risk_create(request):
    """Crear nuevo riesgo"""
    if request.method == 'POST':
        form = RiskForm(request.POST)
        if form.is_valid():
            risk = form.save(commit=False)
            risk.created_by = request.user
            risk.save()
            
            messages.success(
                request, 
                f'Riesgo "{risk.code} - {risk.name}" creado exitosamente. '
                f'Puntuación de riesgo: {risk.inherent_risk_score} ({risk.get_inherent_risk_level_display()})'
            )
            return redirect('risk_detail', pk=risk.pk)
    else:
        form = RiskForm()
    
    # Verificar si hay categorías disponibles
    categories_count = RiskCategory.objects.count()
    
    context = {
        'form': form,
        'is_edit': False,
        'categories_count': categories_count,
    }
    
    return render(request, 'risks/risk_form.html', context)

@login_required
def risk_edit(request, pk):
    """Editar riesgo existente"""
    risk = get_object_or_404(Risk, pk=pk)
    
    # Verificar permisos
    if risk.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'No tienes permisos para editar este riesgo.')
        return redirect('risk_detail', pk=pk)
    
    if request.method == 'POST':
        form = RiskForm(request.POST, instance=risk)
        if form.is_valid():
            # Guardar valores anteriores para comparación
            old_score = risk.inherent_risk_score
            old_level = risk.inherent_risk_level
            
            updated_risk = form.save()
            
            # Recalcular riesgo residual si cambió el inherente
            if old_score != updated_risk.inherent_risk_score:
                updated_risk.calculate_residual_risk()
                
                messages.info(
                    request,
                    f'El riesgo inherente cambió de {old_score} ({old_level}) a '
                    f'{updated_risk.inherent_risk_score} ({updated_risk.inherent_risk_level}). '
                    f'Se recalculó el riesgo residual.'
                )
            
            messages.success(request, f'Riesgo "{updated_risk.code}" actualizado exitosamente.')
            return redirect('risk_detail', pk=updated_risk.pk)
    else:
        form = RiskForm(instance=risk)
    
    context = {
        'form': form,
        'risk': risk,
        'is_edit': True,
    }
    
    return render(request, 'risks/risk_form.html', context)

@login_required
def risk_delete(request, pk):
    """Eliminar riesgo (con confirmación)"""
    risk = get_object_or_404(Risk, pk=pk)
    
    # Verificar permisos
    if risk.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'No tienes permisos para eliminar este riesgo.')
        return redirect('risk_detail', pk=pk)
    
    # Verificar si tiene controles asociados
    controls_count = risk.control_set.count()
    
    if request.method == 'POST':
        risk_code = risk.code
        risk_name = risk.name
        
        # Si tiene controles, avisar al usuario
        if controls_count > 0:
            if not request.POST.get('confirm_delete'):
                messages.warning(
                    request, 
                    f'Este riesgo tiene {controls_count} control(es) asociado(s). '
                    f'Marque la casilla de confirmación para eliminar.'
                )
                return redirect('risk_detail', pk=pk)
        
        risk.delete()
        messages.success(
            request, 
            f'Riesgo "{risk_code} - {risk_name}" eliminado exitosamente.'
        )
        return redirect('risk_list')
    
    context = {
        'risk': risk,
        'controls_count': controls_count,
    }
    
    return render(request, 'risks/risk_confirm_delete.html', context)