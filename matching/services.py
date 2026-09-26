"""
High-level matching service: combines the algorithms + utils modules into
a single explainable match result, and provides ranked lists for the
"Recommended Jobs" (candidate side) and "Applicant ranking" (recruiter side)
features.

Weights are read from settings.MATCHING_WEIGHTS so they're configurable
without touching this code (per project spec).
"""
from django.conf import settings

from .algorithms import skill_match_score, text_similarity_score, experience_relevance_score
from .utils import (
    get_candidate_skill_names, get_job_skill_maps,
    build_candidate_text, build_job_text, calculate_candidate_experience_years,
)
from .learning_suggestions import get_learning_suggestions
from .learning_suggestions import get_learning_suggestions


def build_recommendation(missing_skills):
    """Simple, explainable learning recommendation based on missing mandatory skills."""
    if not missing_skills:
        return "You meet all the required skills for this role."
    skills_str = " and ".join(missing_skills) if len(missing_skills) <= 2 else ", ".join(missing_skills[:-1]) + f", and {missing_skills[-1]}"
    return f"Improve your {skills_str} skills to strengthen this match."


def compute_match(candidate_profile, job):
    """
    Returns a dict with the final weighted match score (0-100) and a full,
    explainable breakdown: matched/missing skills, sub-scores, and a
    plain-language recommendation.
    """
    weights = settings.MATCHING_WEIGHTS

    candidate_skills = get_candidate_skill_names(candidate_profile)
    mandatory_map, preferred_map = get_job_skill_maps(job)
    mandatory_set = set(mandatory_map.keys())
    preferred_set = set(preferred_map.keys())

    skill_score, matched_mandatory, missing_mandatory, matched_preferred = skill_match_score(
        candidate_skills, mandatory_set, preferred_set
    )

    candidate_text = build_candidate_text(candidate_profile)
    job_text = build_job_text(job)
    text_score = text_similarity_score(candidate_text, job_text)

    candidate_years = calculate_candidate_experience_years(candidate_profile)
    experience_score = experience_relevance_score(candidate_years, job.min_experience, job.max_experience)

    final_score = (
        skill_score * weights['SKILL_MATCH']
        + text_score * weights['TEXT_SIMILARITY']
        + experience_score * weights['EXPERIENCE_RELEVANCE']
    ) * 100

    matched_skills_display = sorted(
        {mandatory_map[k] for k in matched_mandatory} | {preferred_map[k] for k in matched_preferred}
    )
    missing_skills_display = sorted({mandatory_map[k] for k in missing_mandatory})

    return {
        'match_score': round(final_score, 1),
        'skill_score': round(skill_score * 100, 1),
        'text_score': round(text_score * 100, 1),
        'experience_score': round(experience_score * 100, 1),
        'matched_skills': matched_skills_display,
        'missing_skills': missing_skills_display,
        'candidate_years': candidate_years,
        'recommendation': build_recommendation(missing_skills_display),
        'weights': weights,
    }


def get_ranked_jobs_for_candidate(candidate_profile, job_queryset, limit=None):
    """Score every job in job_queryset against the candidate, sorted best-first."""
    results = []
    for job in job_queryset:
        match = compute_match(candidate_profile, job)
        results.append((job, match))
    results.sort(key=lambda pair: pair[1]['match_score'], reverse=True)
    return results[:limit] if limit else results


def get_ranked_applications_for_job(job, applications_queryset):
    """Score every application against its job, sorted best-first - for recruiter ranking."""
    results = []
    for application in applications_queryset:
        match = compute_match(application.candidate, job)
        results.append((application, match))
    results.sort(key=lambda pair: pair[1]['match_score'], reverse=True)
    return results


def get_skill_gap_report(candidate_profile, job):
    """
    Extends compute_match with a per-missing-skill list of suggested
    learning topics - powers the dedicated Skill Gap Analysis page.
    """
    match = compute_match(candidate_profile, job)
    match['learning_plan'] = [
        {'skill': skill, 'topics': get_learning_suggestions(skill)}
        for skill in match['missing_skills']
    ]
    return match


def get_top_missing_skills(candidate_profile, job_queryset, limit=5):
    """
    Aggregate how often each missing mandatory skill shows up across a set
    of jobs (e.g. all open jobs) - used for the dashboard's skill gap summary,
    highlighting which single skill would unlock the most opportunities.
    """
    from collections import Counter
    counter = Counter()
    for job in job_queryset:
        match = compute_match(candidate_profile, job)
        counter.update(match['missing_skills'])
    return counter.most_common(limit)
