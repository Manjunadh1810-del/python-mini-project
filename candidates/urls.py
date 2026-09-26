from django.urls import path
from . import views

app_name = 'candidates'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recommended-jobs/', views.job_recommendations, name='job_recommendations'),
    path('skill-gap/<int:job_pk>/', views.skill_gap_view, name='skill_gap'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    path('education/add/', views.education_add, name='education_add'),
    path('education/<int:pk>/edit/', views.education_edit, name='education_edit'),
    path('education/<int:pk>/delete/', views.education_delete, name='education_delete'),

    path('experience/add/', views.experience_add, name='experience_add'),
    path('experience/<int:pk>/edit/', views.experience_edit, name='experience_edit'),
    path('experience/<int:pk>/delete/', views.experience_delete, name='experience_delete'),

    path('skills/', views.skills_manage, name='skills_manage'),
    path('skills/<int:pk>/remove/', views.skill_remove, name='skill_remove'),
]
