from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count
import json

from accounts.decorators import recruiter_required
from companies.models import Company
from companies.forms import CompanyForm
from .models import RecruiterProfile
from .forms import RecruiterProfileForm


def _get_or_create_profile(user):
    profile, _ = RecruiterProfile.objects.get_or_create(user=user)
    return profile


@recruiter_required
def dashboard(request):
    from applications.models import Application  # local import avoids app-loading order issues

    profile = _get_or_create_profile(request.user)
    context = {
        'profile': profile,
        'company': profile.company,
    }
    if profile.company:
        context['active_jobs'] = profile.company.active_jobs_count()
        applications = Application.objects.filter(job__company=profile.company)
        context['total_applicants'] = applications.count()
        context['shortlisted_count'] = applications.filter(status='shortlisted').count()
        context['interview_count'] = applications.filter(status='interview_scheduled').count()
        context['selected_count'] = applications.filter(status='selected').count()
        context['recent_applications'] = applications.select_related('job', 'candidate__user')[:5]

        # Application status breakdown, for the dashboard chart
        status_counts = applications.values('status').annotate(count=Count('id'))
        status_map = {row['status']: row['count'] for row in status_counts}
        context['status_labels'] = json.dumps([Application.Status(s).label for s in status_map.keys()])
        context['status_values'] = json.dumps(list(status_map.values()))
        context['has_applications'] = applications.exists()

        # Candidate matching statistics: average AI match score across all applicants.
        if applications.exists():
            from matching.services import compute_match
            scores = [compute_match(app.candidate, app.job)['match_score'] for app in applications.select_related('candidate')]
            context['avg_match_score'] = round(sum(scores) / len(scores), 1)
        else:
            context['avg_match_score'] = None

    return render(request, 'recruiters/dashboard.html', context)


@recruiter_required
def profile_edit(request):
    profile = _get_or_create_profile(request.user)
    if request.method == 'POST':
        form = RecruiterProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('recruiters:dashboard')
    else:
        form = RecruiterProfileForm(instance=profile)
    return render(request, 'recruiters/profile_edit.html', {'form': form})


@recruiter_required
def company_create(request):
    profile = _get_or_create_profile(request.user)
    if profile.has_company():
        messages.info(request, "You already have a company profile.")
        return redirect('recruiters:company_detail')

    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.created_by = request.user
            company.save()
            profile.company = company
            profile.save()
            messages.success(request, f"Company '{company.name}' created successfully.")
            return redirect('recruiters:dashboard')
    else:
        form = CompanyForm()
    return render(request, 'recruiters/company_form.html', {'form': form, 'mode': 'Create'})


@recruiter_required
def company_edit(request):
    profile = _get_or_create_profile(request.user)
    if not profile.has_company():
        messages.error(request, "Create a company profile first.")
        return redirect('recruiters:company_create')

    company = profile.company
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company profile updated.")
            return redirect('recruiters:company_detail')
    else:
        form = CompanyForm(instance=company)
    return render(request, 'recruiters/company_form.html', {'form': form, 'mode': 'Edit'})


@recruiter_required
def company_detail(request):
    profile = _get_or_create_profile(request.user)
    if not profile.has_company():
        messages.info(request, "You haven't created a company profile yet.")
        return redirect('recruiters:company_create')
    return render(request, 'recruiters/company_detail.html', {'company': profile.company})


@recruiter_required
def company_delete(request):
    profile = _get_or_create_profile(request.user)
    if not profile.has_company():
        messages.error(request, "You don't have a company profile to delete.")
        return redirect('recruiters:dashboard')

    if request.method == 'POST':
        company_name = profile.company.name
        # If the company has other recruiters or open jobs, warn instead of silently deleting.
        other_recruiters = profile.company.recruiters.exclude(pk=profile.pk).count()
        if other_recruiters > 0:
            messages.error(
                request,
                f"Cannot delete '{company_name}': {other_recruiters} other recruiter(s) are linked to it."
            )
            return redirect('recruiters:company_detail')

        profile.company.delete()  # RecruiterProfile.company auto-set to NULL (on_delete=SET_NULL)
        messages.success(request, f"Company '{company_name}' deleted. You can now create a new one.")
        return redirect('recruiters:company_create')

    return render(request, 'recruiters/company_delete_confirm.html', {'company': profile.company})
