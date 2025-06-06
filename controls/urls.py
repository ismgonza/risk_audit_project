from django.urls import path
from . import views

app_name = 'controls'

urlpatterns = [
    # Lista y gestión de controles
    path('', views.control_list, name='control_list'),
    path('<int:pk>/', views.control_detail, name='control_detail'),
    path('create/', views.control_create, name='control_create'),
    path('create/<int:risk_id>/', views.control_create, name='control_create_for_risk'),
    path('<int:pk>/edit/', views.control_edit, name='control_edit'),
    path('<int:pk>/approve/', views.control_approve, name='control_approve'),
    path('<int:pk>/request-revaluation/', views.control_request_revaluation, name='control_request_revaluation'),
    
    # Evidencias
    path('<int:control_id>/evidence/create/', views.evidence_create, name='evidence_create'),
    path('evidence/<int:pk>/', views.evidence_detail, name='evidence_detail'),
    path('evidence/<int:pk>/validate/', views.evidence_validate, name='evidence_validate'),
    
    # Dashboard de auditor
    path('auditor-dashboard/', views.auditor_dashboard, name='auditor_dashboard'),
]