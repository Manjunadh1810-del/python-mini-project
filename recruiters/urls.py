from django.urls import path
from . import views

app_name = 'recruiters'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('company/', views.company_detail, name='company_detail'),
    path('company/create/', views.company_create, name='company_create'),
    path('company/edit/', views.company_edit, name='company_edit'),
    path('company/delete/', views.company_delete, name='company_delete'),
]
