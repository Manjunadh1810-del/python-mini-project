"""
Low-level, pure scoring functions for candidate-job matching.
Each function takes plain data (sets, strings, numbers) and returns a
score in the 0.0-1.0 range plus supporting details, so they can be
unit-tested independently of any Django models.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def skill_match_score(candidate_skills, mandatory_skills, preferred_skills=None):
    """
    candidate_skills, mandatory_skills, preferred_skills: sets of lowercase skill names.

    Mandatory skills drive the bulk of the score; preferred skills add a
    smaller bonus. If a job specifies no skills at all, we don't penalize
    the candidate (score = 1.0) since there's nothing to compare against.

    Returns: (score, matched_mandatory, missing_mandatory, matched_preferred)
    """
    preferred_skills = preferred_skills or set()

    if not mandatory_skills and not preferred_skills:
        return 1.0, set(), set(), set()

    matched_mandatory = candidate_skills & mandatory_skills
    missing_mandatory = mandatory_skills - candidate_skills
    matched_preferred = candidate_skills & preferred_skills

    mandatory_ratio = (len(matched_mandatory) / len(mandatory_skills)) if mandatory_skills else 1.0
    preferred_ratio = (len(matched_preferred) / len(preferred_skills)) if preferred_skills else 0.0

    if preferred_skills:
        score = (mandatory_ratio * 0.85) + (preferred_ratio * 0.15)
    else:
        score = mandatory_ratio

    return min(score, 1.0), matched_mandatory, missing_mandatory, matched_preferred


def text_similarity_score(text1, text2):
    """
    TF-IDF vectorize both texts and return their cosine similarity (0.0-1.0).
    Falls back to 0.0 for empty/too-short text where TF-IDF can't build a vocabulary.
    """
    text1 = (text1 or '').strip()
    text2 = (text2 or '').strip()
    if not text1 or not text2:
        return 0.0

    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(max(0.0, min(similarity, 1.0)))
    except ValueError:
        # Happens when both texts reduce to an empty vocabulary (e.g. only stopwords).
        return 0.0


def experience_relevance_score(candidate_years, min_experience, max_experience=None):
    """
    candidate_years: float, total years of experience (from profile or resume hint).
    min_experience, max_experience: from Job (max_experience may be None = no upper bound).

    A job with no minimum experience requirement scores 1.0 for everyone.
    Meeting the range scores 1.0. Under the minimum scores proportionally.
    Significantly over the max isn't penalized much (overqualified != unfit).
    """
    if not min_experience or min_experience == 0:
        return 1.0

    if candidate_years >= min_experience:
        if max_experience is not None and candidate_years > max_experience:
            return 0.85  # overqualified - still a reasonable match, slightly discounted
        return 1.0

    # Under the minimum: partial, proportional credit.
    return round(candidate_years / min_experience, 2)
