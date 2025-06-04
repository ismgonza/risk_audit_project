from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import AuditProject

@login_required
def audit_dashboard(request):
    """Dashboard de auditorías - página temporal"""
    
    # Obtener algunos datos básicos
    total_projects = AuditProject.objects.count()
    active_projects = AuditProject.objects.filter(status__in=['IN_PROGRESS', 'REVIEW']).count()
    completed_projects = AuditProject.objects.filter(status='COMPLETED').count()
    
    context = {
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
    }
    
    return render(request, 'audit/coming_soon.html', context)

@login_required
def project_list(request):
    """Lista de proyectos de auditoría - próximamente"""
    return render(request, 'audit/coming_soon.html')

@login_required  
def coming_soon(request):
    """Página de próximamente"""
    return render(request, 'audit/coming_soon.html')