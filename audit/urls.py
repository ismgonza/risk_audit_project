from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('', views.audit_dashboard, name='audit_dashboard'),
    path('projects/', views.project_list, name='project_list'),
    path('coming-soon/', views.coming_soon, name='coming_soon'),
]