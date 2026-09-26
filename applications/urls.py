from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    # Candidate
    path('apply/<int:job_pk>/', views.job_apply, name='job_apply'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('<int:pk>/', views.application_detail, name='application_detail'),

    # Recruiter
    path('job/<int:job_pk>/applicants/', views.job_applicants, name='job_applicants'),
    path('applicant/<int:pk>/', views.applicant_detail, name='applicant_detail'),
    path('applicant/<int:application_pk>/schedule-interview/', views.schedule_interview, name='schedule_interview'),
    path('applicant/<int:application_pk>/cancel-interview/', views.cancel_interview, name='cancel_interview'),
]
