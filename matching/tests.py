from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User
from candidates.models import CandidateProfile, Skill, CandidateSkill, Experience
from companies.models import Company
from recruiters.models import RecruiterProfile
from jobs.models import Job, JobSkill
from applications.models import Application

from .algorithms import skill_match_score, text_similarity_score, experience_relevance_score
from .services import compute_match, get_ranked_jobs_for_candidate, build_recommendation


class SkillMatchAlgorithmTests(TestCase):
    def test_full_mandatory_match_scores_high(self):
        score, matched, missing, _ = skill_match_score(
            candidate_skills={'python', 'django', 'sql'},
            mandatory_skills={'python', 'django', 'sql'},
        )
        self.assertEqual(score, 1.0)
        self.assertEqual(missing, set())

    def test_partial_mandatory_match(self):
        score, matched, missing, _ = skill_match_score(
            candidate_skills={'python', 'sql'},
            mandatory_skills={'python', 'django', 'sql', 'rest api'},
        )
        self.assertAlmostEqual(score, 0.5)
        self.assertEqual(missing, {'django', 'rest api'})

    def test_no_requirements_does_not_penalize(self):
        score, matched, missing, pref = skill_match_score(
            candidate_skills={'python'}, mandatory_skills=set(), preferred_skills=set()
        )
        self.assertEqual(score, 1.0)

    def test_preferred_skills_add_small_bonus(self):
        score_without_preferred, *_ = skill_match_score(
            candidate_skills={'python', 'django'},
            mandatory_skills={'python', 'django'},
        )
        score_with_preferred, *_ = skill_match_score(
            candidate_skills={'python', 'django', 'docker'},
            mandatory_skills={'python', 'django'},
            preferred_skills={'docker'},
        )
        self.assertGreaterEqual(score_with_preferred, score_without_preferred - 0.01)


class TextSimilarityAlgorithmTests(TestCase):
    def test_identical_text_scores_high(self):
        score = text_similarity_score("Python Django backend developer", "Python Django backend developer")
        self.assertGreater(score, 0.9)

    def test_unrelated_text_scores_low(self):
        score = text_similarity_score("Python Django backend developer", "Marketing social media content strategy")
        self.assertLess(score, 0.3)

    def test_empty_text_returns_zero(self):
        self.assertEqual(text_similarity_score("", "something"), 0.0)
        self.assertEqual(text_similarity_score("something", ""), 0.0)


class ExperienceRelevanceAlgorithmTests(TestCase):
    def test_no_minimum_always_scores_full(self):
        self.assertEqual(experience_relevance_score(0, min_experience=0), 1.0)
        self.assertEqual(experience_relevance_score(10, min_experience=0), 1.0)

    def test_meets_minimum_scores_full(self):
        self.assertEqual(experience_relevance_score(3, min_experience=2, max_experience=5), 1.0)

    def test_under_minimum_scores_proportionally(self):
        score = experience_relevance_score(1, min_experience=4)
        self.assertEqual(score, 0.25)

    def test_over_maximum_is_discounted_but_not_zero(self):
        score = experience_relevance_score(10, min_experience=1, max_experience=3)
        self.assertEqual(score, 0.85)


class BuildRecommendationTests(TestCase):
    def test_no_missing_skills_message(self):
        msg = build_recommendation([])
        self.assertIn("meet all", msg.lower())

    def test_missing_skills_named_in_message(self):
        msg = build_recommendation(['Django', 'REST API'])
        self.assertIn('Django', msg)
        self.assertIn('REST API', msg)


class ComputeMatchIntegrationTests(TestCase):
    def setUp(self):
        self.candidate_user = User.objects.create_user(
            username='match_cand', email='matchcand@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.profile = CandidateProfile.objects.create(
            user=self.candidate_user, headline='Python Developer', bio='Backend development with Django and REST APIs'
        )
        for name in ['Python', 'Django', 'SQL', 'Git']:
            skill = Skill.objects.create(name=name)
            CandidateSkill.objects.create(candidate=self.profile, skill=skill, proficiency='advanced')

        Experience.objects.create(
            candidate=self.profile, job_title='Backend Intern', company_name='TestCo',
            start_date='2023-01-01', end_date='2024-01-01', description='Worked on Django REST APIs'
        )

        recruiter = User.objects.create_user(
            username='match_recr', email='matchrecr@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        company = Company.objects.create(name='MatchCo', created_by=recruiter)
        self.job = Job.objects.create(
            company=company, posted_by=recruiter, title='Python Developer',
            description='Build backend systems using Python and Django', status='open',
            min_experience=0,
        )
        for name in ['Python', 'Django', 'REST API']:
            skill, _ = Skill.objects.get_or_create(name=name)
            JobSkill.objects.create(job=self.job, skill=skill, is_mandatory=True)

    def test_strong_match_scores_reasonably_high(self):
        result = compute_match(self.profile, self.job)
        self.assertGreater(result['match_score'], 50)
        self.assertIn('Python', result['matched_skills'])
        self.assertIn('Django', result['matched_skills'])
        self.assertIn('REST API', result['missing_skills'])

    def test_match_score_is_weighted_combination(self):
        result = compute_match(self.profile, self.job)
        weights = result['weights']
        expected = (
            result['skill_score'] / 100 * weights['SKILL_MATCH']
            + result['text_score'] / 100 * weights['TEXT_SIMILARITY']
            + result['experience_score'] / 100 * weights['EXPERIENCE_RELEVANCE']
        ) * 100
        self.assertAlmostEqual(result['match_score'], round(expected, 1), places=1)

    def test_poor_match_scores_lower(self):
        unrelated_user = User.objects.create_user(
            username='unrelated_cand', email='unrelated@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        unrelated_profile = CandidateProfile.objects.create(
            user=unrelated_user, headline='Graphic Designer', bio='Adobe Photoshop and Illustrator expert'
        )
        result = compute_match(unrelated_profile, self.job)
        strong_result = compute_match(self.profile, self.job)
        self.assertLess(result['match_score'], strong_result['match_score'])


class RankedJobsTests(TestCase):
    def setUp(self):
        self.candidate_user = User.objects.create_user(
            username='rank_cand', email='rankcand@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.profile = CandidateProfile.objects.create(user=self.candidate_user)
        skill = Skill.objects.create(name='Python')
        CandidateSkill.objects.create(candidate=self.profile, skill=skill, proficiency='advanced')

        recruiter = User.objects.create_user(
            username='rank_recr', email='rankrecr@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        company = Company.objects.create(name='RankCo', created_by=recruiter)

        self.matching_job = Job.objects.create(
            company=company, posted_by=recruiter, title='Python Developer',
            description='Python development role', status='open',
        )
        JobSkill.objects.create(job=self.matching_job, skill=skill, is_mandatory=True)

        self.unrelated_job = Job.objects.create(
            company=company, posted_by=recruiter, title='Sales Executive',
            description='Field sales and client relationship management', status='open',
        )
        for name in ['Sales', 'Negotiation', 'CRM Software']:
            unrelated_skill, _ = Skill.objects.get_or_create(name=name)
            JobSkill.objects.create(job=self.unrelated_job, skill=unrelated_skill, is_mandatory=True)

    def test_jobs_ranked_best_first(self):
        ranked = get_ranked_jobs_for_candidate(self.profile, Job.objects.filter(status='open'))
        self.assertEqual(ranked[0][0], self.matching_job)

    def test_recommended_jobs_view_accessible(self):
        client = Client()
        client.login(username='rank_cand', password='pass12345')
        response = client.get(reverse('candidates:job_recommendations'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Developer')

    def test_min_score_filter_excludes_low_matches(self):
        client = Client()
        client.login(username='rank_cand', password='pass12345')
        response = client.get(reverse('candidates:job_recommendations'), {'min_score': '70'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Sales Executive')

    def test_pagination_limits_results_per_page(self):
        recruiter = User.objects.get(username='rank_recr')
        company = Company.objects.get(name='RankCo')
        for i in range(15):
            Job.objects.create(
                company=company, posted_by=recruiter, title=f'Extra Job {i}',
                description='Generic role', status='open',
            )
        client = Client()
        client.login(username='rank_cand', password='pass12345')
        response = client.get(reverse('candidates:job_recommendations'))
        self.assertEqual(len(response.context['page_obj']), 10)  # page size is 10

    def test_dashboard_shows_top_recommended_jobs(self):
        client = Client()
        client.login(username='rank_cand', password='pass12345')
        response = client.get(reverse('candidates:dashboard'))
        self.assertContains(response, 'Top Recommended Jobs')
        self.assertContains(response, 'Python Developer')


class RecruiterMatchViewTests(TestCase):
    def setUp(self):
        self.candidate_user = User.objects.create_user(
            username='view_cand', email='viewcand@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.profile = CandidateProfile.objects.create(user=self.candidate_user)

        self.recruiter = User.objects.create_user(
            username='view_recr', email='viewrecr@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        self.company = Company.objects.create(name='ViewCo', created_by=self.recruiter)
        RecruiterProfile.objects.create(user=self.recruiter, company=self.company)
        self.job = Job.objects.create(company=self.company, posted_by=self.recruiter, title='Dev', description='x', status='open')
        self.application = Application.objects.create(candidate=self.profile, job=self.job)

    def test_applicant_list_shows_match_score(self):
        client = Client()
        client.login(username='view_recr', password='pass12345')
        response = client.get(reverse('applications:job_applicants', args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Match Score')

    def test_applicant_detail_shows_match_breakdown(self):
        client = Client()
        client.login(username='view_recr', password='pass12345')
        response = client.get(reverse('applications:applicant_detail', args=[self.application.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Match Score')


class SkillGapAnalysisTests(TestCase):
    def setUp(self):
        self.candidate_user = User.objects.create_user(
            username='gap_cand', email='gapcand@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.profile = CandidateProfile.objects.create(user=self.candidate_user)
        python_skill = Skill.objects.create(name='Python')
        CandidateSkill.objects.create(candidate=self.profile, skill=python_skill, proficiency='advanced')

        recruiter = User.objects.create_user(
            username='gap_recr', email='gaprecr@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        company = Company.objects.create(name='GapCo', created_by=recruiter)
        self.job = Job.objects.create(
            company=company, posted_by=recruiter, title='Full Stack Developer',
            description='Build web apps', status='open',
        )
        for name in ['Python', 'Django', 'REST API']:
            skill, _ = Skill.objects.get_or_create(name=name)
            JobSkill.objects.create(job=self.job, skill=skill, is_mandatory=True)

    def test_skill_gap_report_includes_learning_plan(self):
        from matching.services import get_skill_gap_report
        report = get_skill_gap_report(self.profile, self.job)
        self.assertIn('Python', report['matched_skills'])
        self.assertIn('Django', report['missing_skills'])
        self.assertIn('REST API', report['missing_skills'])
        learning_skills = [item['skill'] for item in report['learning_plan']]
        self.assertIn('Django', learning_skills)
        django_item = next(item for item in report['learning_plan'] if item['skill'] == 'Django')
        self.assertGreater(len(django_item['topics']), 0)

    def test_known_skill_uses_curated_suggestions(self):
        from matching.learning_suggestions import get_learning_suggestions
        topics = get_learning_suggestions('Django')
        self.assertIn('Django Fundamentals', topics)

    def test_unknown_skill_gets_generic_suggestions(self):
        from matching.learning_suggestions import get_learning_suggestions
        topics = get_learning_suggestions('SomeObscureTool')
        self.assertEqual(len(topics), 2)
        self.assertIn('SomeObscureTool', topics[0])

    def test_skill_gap_view_accessible(self):
        client = Client()
        client.login(username='gap_cand', password='pass12345')
        response = client.get(reverse('candidates:skill_gap', args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django')
        self.assertContains(response, 'Suggested Learning Areas')

    def test_dashboard_shows_top_missing_skills(self):
        client = Client()
        client.login(username='gap_cand', password='pass12345')
        response = client.get(reverse('candidates:dashboard'))
        self.assertContains(response, 'Skill Gap Summary')

    def test_get_top_missing_skills_aggregation(self):
        from matching.services import get_top_missing_skills
        from jobs.models import Job as JobModel
        results = get_top_missing_skills(self.profile, JobModel.objects.filter(status='open'))
        skill_names = [name for name, count in results]
        self.assertIn('Django', skill_names)
