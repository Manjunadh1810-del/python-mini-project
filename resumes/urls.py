from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    path('upload/', views.resume_upload, name='resume_upload'),
    path('view/', views.resume_view, name='resume_view'),
    path('delete/', views.resume_delete, name='resume_delete'),
    path('analysis/', views.resume_analysis, name='resume_analysis'),
    path('analysis/reanalyze/', views.resume_reanalyze, name='resume_reanalyze'),
    path('analysis/add-skills/', views.add_extracted_skills, name='add_extracted_skills'),
]
