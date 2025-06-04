from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from .models import Control, ControlEvidence
from risks.models import Risk
from .forms import ControlForm, ControlEvidenceForm

@login_required
def control_list(request):
    """Lista de controles con filtros"""
    controls = Control.objects.all().select_related('risk', 'created_by', 'auditor').prefetch_related('controlevidence_set')
    
    # Filtros
    search = request.GET.get('search')
    if search:
        controls = controls.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) | 
            Q(risk__code__icontains=search) |
            Q(risk__name__icontains=search)
        )
    
    control_type_filter = request.GET.get('type')
    if control_type_filter:
        controls = controls.filter(control_type=control_type_filter)
    
    approval_filter = request.GET.get('approval')
    if approval_filter:
        controls = controls.filter(auditor_approval=approval_filter)
    
    active_filter = request.GET.get('active')
    if active_filter:
        controls = controls.filter(is_active=active_filter == 'true')
    
    # Ordenar
    sort_by = request.GET.get('sort', '-created_at')
    controls = controls.order_by(sort_by)
    
    # Agregar datos calculados a cada control
    controls_with_stats = []
    for control in controls:
        evidences = control.controlevidence_set.all()
        validated_count = sum(1 for e in evidences if e.is_validated)
        
        control.evidence_count = evidences.count()
        control.validated_evidence_count = validated_count
        controls_with_stats.append(control)
    
    # Paginación
    paginator = Paginator(controls_with_stats, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas para el filtro
    stats = {
        'total': Control.objects.count(),
        'pending': Control.objects.filter(auditor_approval='PENDING').count(),
        'approved': Control.objects.filter(auditor_approval='APPROVED').count(),
        'rejected': Control.objects.filter(auditor_approval='REJECTED').count(),
        'active': Control.objects.filter(is_active=True).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'controls': page_obj,
        'stats': stats,
        'search': search,
        'control_type_filter': control_type_filter,
        'approval_filter': approval_filter,
        'active_filter': active_filter,
        'sort_by': sort_by,
        'control_types': Control.CONTROL_TYPE_CHOICES,
        'approval_statuses': Control.APPROVAL_STATUS_CHOICES,
    }
    
    return render(request, 'controls/control_list.html', context)

@login_required
def control_detail(request, pk):
    """Detalle de control con evidencias"""
    control = get_object_or_404(Control, pk=pk)
    evidences = ControlEvidence.objects.filter(control=control).order_by('-evidence_date')
    
    # Verificar permisos
    can_edit = control.created_by == request.user or request.user.is_staff
    can_approve = request.user.is_staff and control.auditor_approval in ['PENDING', 'PENDING_REVALUATION']
    can_add_evidence = can_edit
    
    context = {
        'control': control,
        'evidences': evidences,
        'can_edit': can_edit,
        'can_approve': can_approve,
        'can_add_evidence': can_add_evidence,
        'effectiveness_chart_data': _get_effectiveness_chart_data(evidences),
    }
    
    return render(request, 'controls/control_detail.html', context)

@login_required
def control_create(request, risk_id=None):
    """Crear nuevo control"""
    risk = None
    if risk_id:
        risk = get_object_or_404(Risk, pk=risk_id)
    
    if request.method == 'POST':
        form = ControlForm(request.POST)
        if form.is_valid():
            control = form.save(commit=False)
            control.created_by = request.user
            if risk:
                control.risk = risk
            control.save()
            
            messages.success(request, f'Control "{control.name}" creado exitosamente.')
            return redirect('controls:control_detail', pk=control.pk)
    else:
        initial_data = {'risk': risk} if risk else {}
        form = ControlForm(initial=initial_data)
    
    context = {
        'form': form,
        'risk': risk,
        'is_edit': False,
    }
    
    return render(request, 'controls/control_form.html', context)

@login_required
def control_edit(request, pk):
    """Editar control existente"""
    control = get_object_or_404(Control, pk=pk)
    
    # Verificar permisos
    if control.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'No tienes permisos para editar este control.')
        return redirect('controls:control_detail', pk=pk)
    
    if request.method == 'POST':
        form = ControlForm(request.POST, instance=control)
        if form.is_valid():
            form.save()
            
            messages.success(request, f'Control "{control.name}" actualizado exitosamente.')
            return redirect('controls:control_detail', pk=control.pk)
    else:
        form = ControlForm(instance=control)
    
    context = {
        'form': form,
        'control': control,
        'is_edit': True,
    }
    
    return render(request, 'controls/control_form.html', context)

@login_required
def control_approve(request, pk):
    """Aprobar o rechazar control (solo para staff)"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para aprobar controles.')
        return redirect('control_detail', pk=pk)
    
    control = get_object_or_404(Control, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        feedback = request.POST.get('feedback', '')
        
        if action in ['APPROVED', 'REJECTED', 'NEEDS_REVISION']:
            control.auditor_approval = action
            control.auditor_feedback = feedback
            control.auditor = request.user
            control.save()
            
            # Recalcular riesgo residual si se aprueba
            if action == 'APPROVED':
                control.risk.calculate_residual_risk()
            
            action_text = {
                'APPROVED': 'aprobado',
                'REJECTED': 'rechazado',
                'NEEDS_REVISION': 'marcado para revisión'
            }
            
            messages.success(request, f'Control "{control.name}" {action_text[action]} exitosamente.')
        else:
            messages.error(request, 'Acción no válida.')
    
    return redirect('controls:control_detail', pk=pk)

@login_required
def evidence_create(request, control_id):
    """Crear nueva evidencia para un control"""
    control = get_object_or_404(Control, pk=control_id)
    
    # Verificar permisos
    if control.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'No tienes permisos para agregar evidencias a este control.')
        return redirect('controls:control_detail', pk=control_id)
    
    if request.method == 'POST':
        form = ControlEvidenceForm(request.POST, request.FILES)
        if form.is_valid():
            evidence = form.save(commit=False)
            evidence.control = control
            evidence.uploaded_by = request.user
            evidence.save()
            
            messages.success(request, 'Evidencia agregada exitosamente.')
            return redirect('controls:control_detail', pk=control_id)
    else:
        form = ControlEvidenceForm()
    
    context = {
        'form': form,
        'control': control,
    }
    
    return render(request, 'controls/evidence_form.html', context)

@login_required
def evidence_validate(request, pk):
    """Validar evidencia (solo para staff)"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para validar evidencias.')
        return redirect('controls:control_list')
    
    evidence = get_object_or_404(ControlEvidence, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        review = request.POST.get('review', '')
        
        if action == 'validate':
            evidence.is_validated = True
            evidence.validated_by = request.user
            evidence.validation_date = timezone.now()
            evidence.auditor_review = review
            evidence.save()
            
            # Recalcular riesgo residual
            evidence.control.risk.calculate_residual_risk()
            
            messages.success(request, 'Evidencia validada exitosamente.')
        elif action == 'reject':
            evidence.is_validated = False
            evidence.validated_by = None
            evidence.validation_date = None
            evidence.auditor_review = review
            evidence.save()
            
            messages.success(request, 'Evidencia rechazada.')
    
    return redirect('controls:control_detail', pk=evidence.control.pk)

@login_required
def control_request_revaluation(request, pk):
    """Solicitar nueva evaluación de un control que necesita revisión"""
    control = get_object_or_404(Control, pk=pk)
    
    # Verificar que el control esté en estado "Necesita Revisión"
    if control.auditor_approval != 'NEEDS_REVISION':
        messages.error(request, 'Solo se puede solicitar re-evaluación de controles que necesitan revisión.')
        return redirect('controls:control_detail', pk=pk)
    
    if request.method == 'POST':
        # Cambiar estado a pendiente de re-evaluación
        control.auditor_approval = 'PENDING_REVALUATION'
        
        # Opcional: agregar comentario del usuario sobre los cambios realizados
        user_comment = request.POST.get('user_comment', '').strip()
        if user_comment:
            # Agregar comentario del usuario al feedback existente
            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
            new_feedback = f"\n\n--- Comentarios del usuario ({timestamp}) ---\n{user_comment}"
            control.auditor_feedback = (control.auditor_feedback or '') + new_feedback
        
        control.save()
        
        messages.success(
            request, 
            'Solicitud de re-evaluación enviada exitosamente. El auditor será notificado para revisar los cambios realizados.'
        )
        return redirect('controls:control_detail', pk=pk)
    
    context = {
        'control': control,
    }
    
    return render(request, 'controls/request_revaluation.html', context)

@login_required
def auditor_dashboard(request):
    """Dashboard especial para auditores"""
    if not request.user.is_staff:
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')
    
    # Controles pendientes de aprobación
    pending_controls = Control.objects.filter(
        auditor_approval='PENDING'
    ).select_related('risk', 'created_by').order_by('-created_at')[:10]
    
    # Evidencias pendientes de validación
    pending_evidences = ControlEvidence.objects.filter(
        is_validated=False
    ).select_related('control', 'uploaded_by').order_by('-uploaded_at')[:10]
    
    # Estadísticas generales para auditores
    stats = {
        'pending_controls': Control.objects.filter(auditor_approval='PENDING').count(),
        'pending_evidences': ControlEvidence.objects.filter(is_validated=False).count(),
        'approved_today': Control.objects.filter(
            auditor_approval='APPROVED',
            updated_at__date=timezone.now().date()
        ).count(),
        'total_controls': Control.objects.count(),
        'effectiveness_avg': ControlEvidence.objects.filter(
            is_validated=True
        ).aggregate(Avg('effectiveness_percentage'))['effectiveness_percentage__avg'] or 0,
    }
    
    # Controles por estado
    control_stats = {
        'PENDING': Control.objects.filter(auditor_approval='PENDING').count(),
        'APPROVED': Control.objects.filter(auditor_approval='APPROVED').count(),
        'REJECTED': Control.objects.filter(auditor_approval='REJECTED').count(),
        'NEEDS_REVISION': Control.objects.filter(auditor_approval='NEEDS_REVISION').count(),
    }
    
    context = {
        'pending_controls': pending_controls,
        'pending_evidences': pending_evidences,
        'stats': stats,
        'control_stats': control_stats,
    }
    
    return render(request, 'controls/auditor_dashboard.html', context)

def _get_effectiveness_chart_data(evidences):
    """Generar datos para gráfico de efectividad a lo largo del tiempo"""
    data = []
    for evidence in evidences.order_by('evidence_date'):
        data.append({
            'date': evidence.evidence_date.strftime('%Y-%m-%d'),
            'effectiveness': evidence.effectiveness_percentage,
            'description': evidence.description[:50] + '...' if len(evidence.description) > 50 else evidence.description,
            'is_validated': evidence.is_validated,
        })
    return data