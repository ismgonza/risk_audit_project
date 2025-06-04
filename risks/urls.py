from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('risks/', views.risk_list, name='risk_list'),
    path('risks/<int:pk>/', views.risk_detail, name='risk_detail'),
    path('risk-matrix/', views.risk_matrix, name='risk_matrix'),
]