from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from accounts.decorators import candidate_required
from .models import CandidateProfile, Education, Experience, Skill, CandidateSkill
from .forms import CandidateProfileForm, EducationForm, ExperienceForm, SkillAddForm


def _get_or_create_profile(user):
    profile, _ = CandidateProfile.objects.get_or_create(user=user)
    return profile


@candidate_required
def skill_gap_view(request, job_pk):
    from jobs.models import Job
    from matching.services import get_skill_gap_report

    profile = _get_or_create_profile(request.user)
    job = get_object_or_404(Job, pk=job_pk)
    report = get_skill_gap_report(profile, job)
    return render(request, 'candidates/skill_gap.html', {'job': job, 'report': report})


@candidate_required
def job_recommendations(request):
    from django.core.paginator import Paginator
    from jobs.models import Job
    from matching.services import get_ranked_jobs_for_candidate

    profile = _get_or_create_profile(request.user)

    # Cap the number of open jobs scored for performance (TF-IDF runs per job);
    # fine for a mini-project/portfolio scale, called out here for anyone scaling this up.
    open_jobs = Job.objects.filter(status='open').select_related('company')[:200]
    ranked = get_ranked_jobs_for_candidate(profile, open_jobs)

    try:
        min_score = float(request.GET.get('min_score', 0))
    except ValueError:
        min_score = 0
    min_score = max(0, min(min_score, 100))

    if min_score > 0:
        ranked = [pair for pair in ranked if pair[1]['match_score'] >= min_score]

    paginator = Paginator(ranked, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'candidates/recommended_jobs.html', {
        'page_obj': page_obj,
        'min_score': min_score,
        'total_matched': len(ranked),
    })


@candidate_required
def dashboard(request):
    from applications.models import Application  # local import avoids app-loading order issues
    from resumes.models import Resume
    from jobs.models import Job
    from matching.services import get_top_missing_skills, get_ranked_jobs_for_candidate
    from django.db.models import Count
    import json

    profile = _get_or_create_profile(request.user)
    applications = Application.objects.filter(candidate=profile)
    resume = Resume.objects.filter(candidate=profile).first()

    top_missing_skills = []
    top_recommended_jobs = []
    if profile.candidateskill_set.exists():  # only compute if profile has something to match against
        open_jobs = Job.objects.filter(status='open').select_related('company')[:20]  # cap for dashboard performance
        top_missing_skills = get_top_missing_skills(profile, open_jobs, limit=5)
        top_recommended_jobs = get_ranked_jobs_for_candidate(profile, open_jobs, limit=3)

    status_counts = applications.values('status').annotate(count=Count('id'))
    status_map = {row['status']: row['count'] for row in status_counts}
    status_labels = json.dumps([Application.Status(s).label for s in status_map.keys()])
    status_values = json.dumps(list(status_map.values()))

    context = {
        'profile': profile,
        'completion': profile.profile_completion_percentage(),
        'education_count': profile.education_entries.count(),
        'experience_count': profile.experience_entries.count(),
        'skill_count': profile.candidateskill_set.count(),
        'resume': resume,
        'top_missing_skills': top_missing_skills,
        'top_recommended_jobs': top_recommended_jobs,
        'total_applications': applications.count(),
        'under_review_count': applications.filter(status='under_review').count(),
        'shortlisted_count': applications.filter(status='shortlisted').count(),
        'recent_applications': applications.select_related('job', 'job__company')[:5],
        'status_labels': status_labels,
        'status_values': status_values,
        'has_applications': applications.exists(),
    }
    return render(request, 'candidates/dashboard.html', context)


@candidate_required
def profile_view(request):
    profile = _get_or_create_profile(request.user)
    context = {
        'profile': profile,
        'completion': profile.profile_completion_percentage(),
        'education_entries': profile.education_entries.all(),
        'experience_entries': profile.experience_entries.all(),
        'candidate_skills': profile.candidateskill_set.select_related('skill').all(),
    }
    return render(request, 'candidates/profile_view.html', context)


@candidate_required
def profile_edit(request):
    profile = _get_or_create_profile(request.user)
    if request.method == 'POST':
        form = CandidateProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('candidates:profile_view')
    else:
        form = CandidateProfileForm(instance=profile)
    return render(request, 'candidates/profile_edit.html', {'form': form})


# ---- Education ----

@candidate_required
def education_add(request):
    profile = _get_or_create_profile(request.user)
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            education = form.save(commit=False)
            education.candidate = profile
            education.save()
            messages.success(request, "Education added.")
            return redirect('candidates:profile_view')
    else:
        form = EducationForm()
    return render(request, 'candidates/education_form.html', {'form': form, 'mode': 'Add'})


@candidate_required
def education_edit(request, pk):
    profile = _get_or_create_profile(request.user)
    education = get_object_or_404(Education, pk=pk, candidate=profile)
    if request.method == 'POST':
        form = EducationForm(request.POST, instance=education)
        if form.is_valid():
            form.save()
            messages.success(request, "Education updated.")
            return redirect('candidates:profile_view')
    else:
        form = EducationForm(instance=education)
    return render(request, 'candidates/education_form.html', {'form': form, 'mode': 'Edit'})


@candidate_required
def education_delete(request, pk):
    profile = _get_or_create_profile(request.user)
    education = get_object_or_404(Education, pk=pk, candidate=profile)
    education.delete()
    messages.info(request, "Education entry removed.")
    return redirect('candidates:profile_view')


# ---- Experience ----

@candidate_required
def experience_add(request):
    profile = _get_or_create_profile(request.user)
    if request.method == 'POST':
        form = ExperienceForm(request.POST)
        if form.is_valid():
            experience = form.save(commit=False)
            experience.candidate = profile
            experience.save()
            messages.success(request, "Experience added.")
            return redirect('candidates:profile_view')
    else:
        form = ExperienceForm()
    return render(request, 'candidates/experience_form.html', {'form': form, 'mode': 'Add'})


@candidate_required
def experience_edit(request, pk):
    profile = _get_or_create_profile(request.user)
    experience = get_object_or_404(Experience, pk=pk, candidate=profile)
    if request.method == 'POST':
        form = ExperienceForm(request.POST, instance=experience)
        if form.is_valid():
            form.save()
            messages.success(request, "Experience updated.")
            return redirect('candidates:profile_view')
    else:
        form = ExperienceForm(instance=experience)
    return render(request, 'candidates/experience_form.html', {'form': form, 'mode': 'Edit'})


@candidate_required
def experience_delete(request, pk):
    profile = _get_or_create_profile(request.user)
    experience = get_object_or_404(Experience, pk=pk, candidate=profile)
    experience.delete()
    messages.info(request, "Experience entry removed.")
    return redirect('candidates:profile_view')


# ---- Skills ----

@candidate_required
def skills_manage(request):
    profile = _get_or_create_profile(request.user)
    if request.method == 'POST':
        form = SkillAddForm(request.POST)
        if form.is_valid():
            raw_skills = form.cleaned_data['skills_input']
            proficiency = form.cleaned_data['proficiency']
            names = [s.strip() for s in raw_skills.split(',') if s.strip()]
            added = 0
            for name in names:
                skill, _ = Skill.objects.get_or_create(name__iexact=name, defaults={'name': name})
                _, created = CandidateSkill.objects.get_or_create(
                    candidate=profile, skill=skill, defaults={'proficiency': proficiency}
                )
                if created:
                    added += 1
            messages.success(request, f"Added {added} skill(s).")
            return redirect('candidates:skills_manage')
    else:
        form = SkillAddForm()

    candidate_skills = profile.candidateskill_set.select_related('skill').all()
    return render(request, 'candidates/skills.html', {'form': form, 'candidate_skills': candidate_skills})


@candidate_required
def skill_remove(request, pk):
    profile = _get_or_create_profile(request.user)
    candidate_skill = get_object_or_404(CandidateSkill, pk=pk, candidate=profile)
    candidate_skill.delete()
    messages.info(request, "Skill removed.")
    return redirect('candidates:skills_manage')
