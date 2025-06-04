from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import Risk, RiskCategory
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
    risks = Risk.objects.all().select_related('category', 'created_by')
    
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
    
    # Ordenar por código
    risks = risks.order_by('code')
    
    context = {
        'risks': risks,
        'categories': RiskCategory.objects.all(),
        'search': search,
        'category_filter': category_filter,
        'level_filter': level_filter,
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
    for prob in range(1, 4):
        matrix_data[prob] = {}
        for imp in range(1, 6):
            matrix_data[prob][imp] = []
    
    for risk in risks:
        matrix_data[risk.probability][risk.impact].append(risk)
    
    context = {
        'matrix_data': matrix_data,
        'probabilities': range(1, 4),
        'impacts': range(1, 6),
    }
    
    return render(request, 'risks/risk_matrix.html', context)