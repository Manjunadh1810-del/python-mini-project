"""
Helpers that turn Django model instances (CandidateProfile, Job) into the
plain data the algorithms module needs: skill sets, text blobs, and
years-of-experience numbers.
"""
from datetime import date


def get_candidate_skill_names(candidate_profile):
    """Lowercase set of the candidate's declared skills (from their profile, not the resume)."""
    return set(
        name.lower() for name in
        candidate_profile.candidateskill_set.values_list('skill__name', flat=True)
    )


def get_job_skill_maps(job):
    """
    Returns (mandatory_map, preferred_map) where each map is {lowercase_name: display_name},
    so scoring can work in lowercase while templates still show original casing.
    """
    mandatory_map = {js.skill.name.lower(): js.skill.name for js in job.mandatory_skills()}
    preferred_map = {js.skill.name.lower(): js.skill.name for js in job.preferred_skills()}
    return mandatory_map, preferred_map


def build_candidate_text(candidate_profile):
    """Combine profile fields, education, experience, skills, and resume text into one blob for TF-IDF."""
    parts = [candidate_profile.headline or '', candidate_profile.bio or '']

    for edu in candidate_profile.education_entries.all():
        parts.append(f"{edu.degree} {edu.field_of_study}")

    for exp in candidate_profile.experience_entries.all():
        parts.append(f"{exp.job_title} {exp.description}")

    for cs in candidate_profile.candidateskill_set.select_related('skill'):
        parts.append(cs.skill.name)

    resume = getattr(candidate_profile, 'resume', None)
    if resume and resume.extraction_successful and resume.extracted_text:
        parts.append(resume.extracted_text)

    return " ".join(p for p in parts if p).strip()


def build_job_text(job):
    """Combine job title, description, responsibilities, and required/preferred skills for TF-IDF."""
    parts = [job.title or '', job.description or '', job.responsibilities or '']
    for js in job.jobskill_set.select_related('skill'):
        parts.append(js.skill.name)
    return " ".join(p for p in parts if p).strip()


def calculate_candidate_experience_years(candidate_profile):
    """
    Sum durations across the candidate's structured Experience entries.
    Falls back to the resume's regex-detected 'X years experience' hint
    if no structured entries exist yet.
    """
    total_days = 0
    has_entries = False
    for exp in candidate_profile.experience_entries.all():
        has_entries = True
        end = date.today() if exp.currently_working or not exp.end_date else exp.end_date
        if exp.start_date and end >= exp.start_date:
            total_days += (end - exp.start_date).days

    if has_entries:
        return round(total_days / 365.25, 1)

    resume = getattr(candidate_profile, 'resume', None)
    if resume and resume.experience_years_hint:
        return round(resume.experience_years_hint, 1)

    return 0.0
