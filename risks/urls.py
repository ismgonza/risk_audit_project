from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('risks/', views.risk_list, name='risk_list'),
    path('risks/create/', views.risk_create, name='risk_create'),
    path('risks/<int:pk>/', views.risk_detail, name='risk_detail'),
    path('risks/<int:pk>/edit/', views.risk_edit, name='risk_edit'),
    path('risks/<int:pk>/delete/', views.risk_delete, name='risk_delete'),
    path('risk-matrix/', views.risk_matrix, name='risk_matrix'),
]