from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from accounts.decorators import candidate_required, recruiter_required
from candidates.models import CandidateProfile
from recruiters.models import RecruiterProfile
from jobs.models import Job
from .models import Application, Interview
from .forms import ApplicationForm, ApplicationStatusForm, InterviewForm


# ---- Candidate side ----

@candidate_required
def job_apply(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    profile, _ = CandidateProfile.objects.get_or_create(user=request.user)

    if not job.is_open():
        messages.error(request, "This job is closed and no longer accepting applications.")
        return redirect('jobs:job_detail_public', pk=job.pk)

    if Application.objects.filter(candidate=profile, job=job).exists():
        messages.info(request, "You have already applied to this job.")
        return redirect('applications:application_detail', pk=Application.objects.get(candidate=profile, job=job).pk)

    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.candidate = profile
            application.job = job
            application.save()

            from notifications.services import notify
            from notifications.models import Notification
            notify(
                job.posted_by,
                f"{request.user.first_name or request.user.username} applied for '{job.title}'.",
                notification_type=Notification.Type.NEW_APPLICATION,
                link_url=f'/applications/applicant/{application.pk}/',
            )

            messages.success(request, f"Applied to '{job.title}' successfully!")
            return redirect('applications:application_detail', pk=application.pk)
    else:
        form = ApplicationForm()

    return render(request, 'applications/job_apply.html', {'form': form, 'job': job})


@candidate_required
def my_applications(request):
    profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
    applications = Application.objects.filter(candidate=profile).select_related('job', 'job__company')
    return render(request, 'applications/my_applications.html', {'applications': applications})


@candidate_required
def application_detail(request, pk):
    profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
    application = get_object_or_404(Application, pk=pk, candidate=profile)
    return render(request, 'applications/application_detail.html', {'application': application})


# ---- Recruiter side ----

@recruiter_required
def job_applicants(request, job_pk):
    from matching.services import get_ranked_applications_for_job

    recruiter_profile, _ = RecruiterProfile.objects.get_or_create(user=request.user)
    job = get_object_or_404(Job, pk=job_pk, company=recruiter_profile.company)
    applications = Application.objects.filter(job=job).select_related('candidate', 'candidate__user')
    ranked = get_ranked_applications_for_job(job, applications)
    return render(request, 'applications/job_applicants.html', {'job': job, 'ranked_applications': ranked})


@recruiter_required
def applicant_detail(request, pk):
    from matching.services import compute_match

    recruiter_profile, _ = RecruiterProfile.objects.get_or_create(user=request.user)
    application = get_object_or_404(Application, pk=pk, job__company=recruiter_profile.company)
    old_status = application.status  # captured before form binding, since ModelForm.is_valid() mutates form.instance in place

    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            updated_application = form.save()

            if updated_application.status != old_status:
                from notifications.services import notify
                from notifications.models import Notification
                notify(
                    application.candidate.user,
                    f"Your application for '{application.job.title}' is now '{updated_application.get_status_display()}'.",
                    notification_type=Notification.Type.STATUS_CHANGE,
                    link_url=f'/applications/{application.pk}/',
                )

            messages.success(request, f"Application status updated to '{application.get_status_display()}'.")
            return redirect('applications:applicant_detail', pk=application.pk)
    else:
        form = ApplicationStatusForm(instance=application)

    match = compute_match(application.candidate, application.job)

    context = {
        'application': application,
        'form': form,
        'candidate_profile': application.candidate,
        'education_entries': application.candidate.education_entries.all(),
        'experience_entries': application.candidate.experience_entries.all(),
        'candidate_skills': application.candidate.candidateskill_set.select_related('skill').all(),
        'resume': getattr(application.candidate, 'resume', None),
        'match': match,
        'interview': getattr(application, 'interview', None),
    }
    return render(request, 'applications/applicant_detail.html', context)


# ---- Interview scheduling (recruiter side) ----

@recruiter_required
def schedule_interview(request, application_pk):
    from notifications.services import notify
    from notifications.models import Notification

    recruiter_profile, _ = RecruiterProfile.objects.get_or_create(user=request.user)
    application = get_object_or_404(Application, pk=application_pk, job__company=recruiter_profile.company)
    existing_interview = getattr(application, 'interview', None)

    if request.method == 'POST':
        form = InterviewForm(request.POST, instance=existing_interview)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.application = application
            interview.save()

            if application.status not in [Application.Status.SELECTED, Application.Status.REJECTED]:
                application.status = Application.Status.INTERVIEW_SCHEDULED
                application.save()

            notify(
                application.candidate.user,
                f"An interview has been scheduled for your application to '{application.job.title}' "
                f"on {interview.scheduled_datetime.strftime('%d %b %Y at %I:%M %p')}.",
                notification_type=Notification.Type.INTERVIEW_SCHEDULED,
                link_url=f'/applications/{application.pk}/',
            )

            messages.success(request, "Interview scheduled and candidate notified.")
            return redirect('applications:applicant_detail', pk=application.pk)
    else:
        initial = {}
        if existing_interview:
            initial = {
                'scheduled_date': existing_interview.scheduled_datetime.date(),
                'scheduled_time': existing_interview.scheduled_datetime.time(),
            }
        form = InterviewForm(instance=existing_interview, initial=initial)

    return render(request, 'applications/schedule_interview.html', {
        'form': form, 'application': application, 'existing_interview': existing_interview,
    })


@recruiter_required
def cancel_interview(request, application_pk):
    recruiter_profile, _ = RecruiterProfile.objects.get_or_create(user=request.user)
    application = get_object_or_404(Application, pk=application_pk, job__company=recruiter_profile.company)
    interview = getattr(application, 'interview', None)
    if interview:
        interview.delete()
        messages.info(request, "Interview cancelled.")
    return redirect('applications:applicant_detail', pk=application.pk)
