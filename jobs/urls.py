from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # Public
    path('', views.job_list_public, name='job_list_public'),
    path('<int:pk>/', views.job_detail_public, name='job_detail_public'),

    # Recruiter
    path('manage/', views.manage_jobs, name='manage_jobs'),
    path('manage/create/', views.job_create, name='job_create'),
    path('manage/<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('manage/<int:pk>/close/', views.job_close, name='job_close'),
    path('manage/<int:pk>/reopen/', views.job_reopen, name='job_reopen'),
    path('manage/<int:pk>/delete/', views.job_delete, name='job_delete'),
    path('manage/<int:pk>/', views.job_detail_recruiter, name='job_detail_recruiter'),
]
