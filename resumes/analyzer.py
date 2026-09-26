"""
Rule-based resume analysis: skill extraction, education hints, and a rough
years-of-experience hint, all derived from the resume's extracted_text.

Every result here is explainable - a skill is "found" only because its exact
keyword/phrase appears in the resume text (word-boundary matched, case-insensitive).
No black-box scoring happens in this module.
"""
import re
from django.utils import timezone

from candidates.models import Skill
from .skill_keywords import COMMON_SKILLS, DEGREE_KEYWORDS


def _build_skill_lookup():
    """Combine the curated keyword list with whatever skills already exist
    in the live catalog (added by candidates/recruiters), deduplicated
    case-insensitively. Longer phrases are checked first so 'Machine Learning'
    matches before a hypothetical bare 'Learning' entry would."""
    names = set(COMMON_SKILLS)
    names.update(Skill.objects.values_list('name', flat=True))
    return sorted(names, key=len, reverse=True)


def extract_skills_from_text(text):
    """Return a sorted list of skill names found in the text via word-boundary matching."""
    if not text:
        return []

    text_lower = text.lower()
    found = []
    found_lower = set()

    for name in _build_skill_lookup():
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(name.lower()) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, text_lower) and name.lower() not in found_lower:
            found.append(name)
            found_lower.add(name.lower())

    return sorted(found, key=str.lower)


def extract_education_hints(text):
    """Return resume lines that mention a recognizable degree keyword."""
    if not text:
        return []

    hints = []
    seen = set()
    for line in text.split('\n'):
        line_lower = line.lower()
        for keyword in DEGREE_KEYWORDS:
            pattern = r'(?<![a-zA-Z])' + re.escape(keyword.lower()) + r'(?![a-zA-Z])'
            if re.search(pattern, line_lower):
                clean_line = line.strip()
                if clean_line and clean_line not in seen:
                    hints.append(clean_line)
                    seen.add(clean_line)
                break
    return hints[:10]


def extract_experience_years_hint(text):
    """Look for explicit phrases like '3 years of experience'. Returns a float or None."""
    if not text:
        return None
    match = re.search(r'(\d+(?:\.\d+)?)\s*\+?\s*years?\s+(?:of\s+)?experience', text.lower())
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def analyze_resume(resume):
    """Run all extractors against resume.extracted_text and persist the results."""
    text = resume.extracted_text

    resume.extracted_skills = extract_skills_from_text(text)
    resume.extracted_education_hints = extract_education_hints(text)
    resume.experience_years_hint = extract_experience_years_hint(text)
    resume.analyzed_at = timezone.now()
    resume.save()

    return {
        'skills': resume.extracted_skills,
        'education_hints': resume.extracted_education_hints,
        'experience_years_hint': resume.experience_years_hint,
    }
