from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q

from accounts.decorators import recruiter_required
from candidates.models import Skill
from recruiters.models import RecruiterProfile
from .models import Job, JobSkill
from .forms import JobForm, JobSearchForm


def _parse_skill_names(raw):
    return [s.strip() for s in raw.split(',') if s.strip()]


def _save_job_skills(job, required_raw, preferred_raw):
    job.jobskill_set.all().delete()
    for name in _parse_skill_names(required_raw):
        skill, _ = Skill.objects.get_or_create(name__iexact=name, defaults={'name': name})
        JobSkill.objects.get_or_create(job=job, skill=skill, defaults={'is_mandatory': True})
    for name in _parse_skill_names(preferred_raw):
        skill, _ = Skill.objects.get_or_create(name__iexact=name, defaults={'name': name})
        JobSkill.objects.get_or_create(job=job, skill=skill, defaults={'is_mandatory': False})


# ---- Recruiter views ----

@recruiter_required
def manage_jobs(request):
    profile, _ = RecruiterProfile.objects.get_or_create(user=request.user)
    if not profile.has_company():
        messages.info(request, "Create your company profile before posting jobs.")
        return redirect('recruiters:company_create')

    jobs = Job.objects.filter(company=profile.company)
    return render(request, 'jobs/manage_jobs.html', {'jobs': jobs, 'company': profile.company})


@recruiter_required
def job_create(request):
    profile, _ = RecruiterProfile.objects.get_or_create(user=request.user)
    if not profile.has_company():
        messages.info(request, "Create your company profile before posting jobs.")
        return redirect('recruiters:company_create')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = profile.company
            job.posted_by = request.user
            job.save()
            _save_job_skills(job, form.cleaned_data['required_skills_input'], form.cleaned_data['preferred_skills_input'])
            messages.success(request, f"Job '{job.title}' posted successfully.")
            return redirect('jobs:manage_jobs')
    else:
        form = JobForm()
    return render(request, 'jobs/job_form.html', {'form': form, 'mode': 'Post'})


@recruiter_required
def job_edit(request, pk):
    profile, _ = RecruiterProfile.objects.get_or_create(user=request.user)
    job = get_object_or_404(Job, pk=pk, company=profile.company)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save()
            _save_job_skills(job, form.cleaned_data['required_skills_input'], form.cleaned_data['preferred_skills_input'])
            messages.success(request, "Job updated successfully.")
            return redirect('jobs:manage_jobs')
    else:
        initial = {
            'required_skills_input': ', '.join(js.skill.name for js in job.mandatory_skills()),
            'preferred_skills_input': ', '.join(js.skill.name for js in job.preferred_skills()),
        }
        form = JobForm(instance=job, initial=initial)
    return render(request, 'jobs/job_form.html', {'form': form, 'mode': 'Edit', 'job': job})


@recruiter_required
def job_close(request, pk):
    profile, _ = RecruiterProfile.objects.get_or_create(user=request.user)
    job = get_object_or_404(Job, pk=pk, company=profile.company)
    job.status = Job.Status.CLOSED
    job.save()
    messages.success(request, f"Job '{job.title}' closed.")
    return redirect('jobs:manage_jobs')


@recruiter_required
def job_reopen(request, pk):
    profile, _ = RecruiterProfile.objects.get_or_create(user=request.user)
    job = get_object_or_404(Job, pk=pk, company=profile.company)
    job.status = Job.Status.OPEN
    job.save()
    messages.success(request, f"Job '{job.title}' reopened.")
    return redirect('jobs:manage_jobs')


@recruiter_required
def job_delete(request, pk):
    profile, _ = RecruiterProfile.objects.get_or_create(user=request.user)
    job = get_object_or_404(Job, pk=pk, company=profile.company)
    title = job.title
    job.delete()
    messages.info(request, f"Job '{title}' deleted.")
    return redirect('jobs:manage_jobs')


@recruiter_required
def job_detail_recruiter(request, pk):
    profile, _ = RecruiterProfile.objects.get_or_create(user=request.user)
    job = get_object_or_404(Job, pk=pk, company=profile.company)
    return render(request, 'jobs/job_detail_recruiter.html', {'job': job})


# ---- Public views ----

def job_list_public(request):
    form = JobSearchForm(request.GET or None)
    jobs = Job.objects.filter(status=Job.Status.OPEN).select_related('company')

    if form.is_valid():
        q = form.cleaned_data.get('q')
        location = form.cleaned_data.get('location')
        job_type = form.cleaned_data.get('job_type')
        work_mode = form.cleaned_data.get('work_mode')

        if q:
            jobs = jobs.filter(
                Q(title__icontains=q) | Q(company__name__icontains=q) | Q(skills__name__icontains=q)
            ).distinct()
        if location:
            jobs = jobs.filter(location__icontains=location)
        if job_type:
            jobs = jobs.filter(job_type=job_type)
        if work_mode:
            jobs = jobs.filter(work_mode=work_mode)

    return render(request, 'jobs/job_list_public.html', {'jobs': jobs, 'form': form})


def job_detail_public(request, pk):
    job = get_object_or_404(Job, pk=pk)
    context = {'job': job}

    if request.user.is_authenticated and request.user.role == 'candidate':
        from candidates.models import CandidateProfile
        from matching.services import compute_match
        profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
        context['match'] = compute_match(profile, job)

    return render(request, 'jobs/job_detail_public.html', context)
