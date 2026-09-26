import os
from django.shortcuts import render, redirect
from django.contrib import messages

from accounts.decorators import candidate_required
from candidates.models import CandidateProfile
from .models import Resume
from .forms import ResumeUploadForm
from .services import extract_text, clean_extracted_text, ResumeExtractionError
from .analyzer import analyze_resume


@candidate_required
def resume_upload(request):
    profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
    existing_resume = Resume.objects.filter(candidate=profile).first()

    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Replace old file if re-uploading, to avoid orphaned media files.
            if existing_resume:
                if existing_resume.file:
                    existing_resume.file.delete(save=False)
                resume = existing_resume
                resume.file = form.cleaned_data['file']
            else:
                resume = form.save(commit=False)
                resume.candidate = profile

            uploaded_file = form.cleaned_data['file']
            ext = os.path.splitext(uploaded_file.name)[1].lower().lstrip('.')

            resume.original_filename = uploaded_file.name
            resume.file_type = ext
            resume.file_size_kb = uploaded_file.size // 1024
            resume.save()  # save first so resume.file is written to disk / storage

            # Extract text right after upload.
            try:
                resume.file.seek(0)
                raw_text = extract_text(resume.file, ext)
                resume.extracted_text = clean_extracted_text(raw_text)
                resume.extraction_successful = True
                resume.extraction_error = ''
                resume.save()
                analyze_resume(resume)
                messages.success(request, "Resume uploaded and analyzed successfully.")
            except ResumeExtractionError as exc:
                resume.extracted_text = ''
                resume.extraction_successful = False
                resume.extraction_error = str(exc)
                messages.warning(request, f"Resume uploaded, but text extraction failed: {exc}")

            resume.save()
            return redirect('resumes:resume_analysis')
    else:
        form = ResumeUploadForm()

    return render(request, 'resumes/resume_upload.html', {
        'form': form, 'existing_resume': existing_resume,
    })


@candidate_required
def resume_view(request):
    profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
    resume = Resume.objects.filter(candidate=profile).first()
    if not resume:
        messages.info(request, "You haven't uploaded a resume yet.")
        return redirect('resumes:resume_upload')
    return render(request, 'resumes/resume_view.html', {'resume': resume})


@candidate_required
def resume_analysis(request):
    profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
    resume = Resume.objects.filter(candidate=profile).first()
    if not resume:
        messages.info(request, "You haven't uploaded a resume yet.")
        return redirect('resumes:resume_upload')

    if not resume.extraction_successful:
        messages.warning(request, "Resume analysis needs extractable text. Try re-uploading a text-based file.")
        return redirect('resumes:resume_view')

    existing_skill_names = set(
        s.lower() for s in profile.candidateskill_set.values_list('skill__name', flat=True)
    )
    new_skills = [s for s in resume.extracted_skills if s.lower() not in existing_skill_names]

    return render(request, 'resumes/resume_analysis.html', {
        'resume': resume,
        'new_skills': new_skills,
        'already_added_count': len(resume.extracted_skills) - len(new_skills),
    })


@candidate_required
def resume_reanalyze(request):
    profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
    resume = Resume.objects.filter(candidate=profile).first()
    if not resume or not resume.extraction_successful:
        messages.error(request, "No analyzable resume found.")
        return redirect('resumes:resume_upload')

    analyze_resume(resume)
    messages.success(request, "Resume re-analyzed with the latest skill catalog.")
    return redirect('resumes:resume_analysis')


@candidate_required
def add_extracted_skills(request):
    from candidates.models import Skill, CandidateSkill

    profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
    resume = Resume.objects.filter(candidate=profile).first()
    if not resume:
        messages.error(request, "No resume found.")
        return redirect('resumes:resume_upload')

    added = 0
    for name in resume.extracted_skills:
        skill, _ = Skill.objects.get_or_create(name__iexact=name, defaults={'name': name})
        _, created = CandidateSkill.objects.get_or_create(
            candidate=profile, skill=skill, defaults={'proficiency': 'intermediate'}
        )
        if created:
            added += 1

    messages.success(request, f"Added {added} skill(s) to your profile.")
    return redirect('candidates:skills_manage')


@candidate_required
def resume_delete(request):
    profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
    resume = Resume.objects.filter(candidate=profile).first()
    if resume:
        if resume.file:
            resume.file.delete(save=False)
        resume.delete()
        messages.info(request, "Resume deleted. You can upload a new one anytime.")
    return redirect('resumes:resume_upload')
