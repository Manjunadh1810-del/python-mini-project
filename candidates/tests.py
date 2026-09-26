from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from .models import CandidateProfile, Education, Experience, Skill, CandidateSkill


class CandidateProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.candidate = User.objects.create_user(
            username='cand1', email='cand1@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.recruiter = User.objects.create_user(
            username='recr1', email='recr1@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        self.client.login(username='cand1', password='pass12345')

    def test_profile_auto_created_on_dashboard_visit(self):
        self.assertFalse(CandidateProfile.objects.filter(user=self.candidate).exists())
        self.client.get(reverse('candidates:dashboard'))
        self.assertTrue(CandidateProfile.objects.filter(user=self.candidate).exists())

    def test_profile_completion_starts_low(self):
        response = self.client.get(reverse('candidates:dashboard'))
        self.assertContains(response, '%')

    def test_recruiter_cannot_access_candidate_dashboard(self):
        self.client.logout()
        self.client.login(username='recr1', password='pass12345')
        response = self.client.get(reverse('candidates:dashboard'))
        self.assertRedirects(response, reverse('home'))

    def test_unauthenticated_user_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse('candidates:dashboard'))
        self.assertEqual(response.status_code, 302)


class EducationExperienceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.candidate = User.objects.create_user(
            username='cand2', email='cand2@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.client.login(username='cand2', password='pass12345')
        self.profile = CandidateProfile.objects.create(user=self.candidate)

    def test_add_education(self):
        response = self.client.post(reverse('candidates:education_add'), {
            'degree': 'B.Tech', 'field_of_study': 'CSE', 'institution': 'Test University',
            'start_year': 2021, 'end_year': 2025, 'grade': '8.5 CGPA',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Education.objects.filter(candidate=self.profile).count(), 1)

    def test_add_experience(self):
        response = self.client.post(reverse('candidates:experience_add'), {
            'job_title': 'Intern', 'company_name': 'Test Corp',
            'start_date': '2024-01-01', 'currently_working': True, 'description': 'Worked on stuff',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Experience.objects.filter(candidate=self.profile).count(), 1)

    def test_delete_education_only_own(self):
        edu = Education.objects.create(candidate=self.profile, degree='B.Tech', institution='X', start_year=2020)
        self.client.post(reverse('candidates:education_delete', args=[edu.pk]))
        self.assertFalse(Education.objects.filter(pk=edu.pk).exists())

    def test_edit_education(self):
        edu = Education.objects.create(candidate=self.profile, degree='B.Tech', institution='Old Uni', start_year=2020)
        response = self.client.post(reverse('candidates:education_edit', args=[edu.pk]), {
            'degree': 'B.Tech', 'field_of_study': 'CSE', 'institution': 'New Uni',
            'start_year': 2020, 'end_year': 2024, 'grade': '9.0',
        })
        self.assertEqual(response.status_code, 302)
        edu.refresh_from_db()
        self.assertEqual(edu.institution, 'New Uni')

    def test_edit_experience(self):
        exp = Experience.objects.create(
            candidate=self.profile, job_title='Intern', company_name='Old Co',
            start_date='2023-01-01', currently_working=True,
        )
        response = self.client.post(reverse('candidates:experience_edit', args=[exp.pk]), {
            'job_title': 'Senior Intern', 'company_name': 'Old Co',
            'start_date': '2023-01-01', 'currently_working': True, 'description': 'Promoted',
        })
        self.assertEqual(response.status_code, 302)
        exp.refresh_from_db()
        self.assertEqual(exp.job_title, 'Senior Intern')

    def test_cannot_edit_another_candidates_education(self):
        other_candidate = User.objects.create_user(
            username='other_edu_cand', email='otheredu@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        other_profile = CandidateProfile.objects.create(user=other_candidate)
        other_edu = Education.objects.create(candidate=other_profile, degree='M.Tech', institution='Y', start_year=2019)

        response = self.client.get(reverse('candidates:education_edit', args=[other_edu.pk]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_another_candidates_experience(self):
        other_candidate = User.objects.create_user(
            username='other_exp_cand', email='otherexp@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        other_profile = CandidateProfile.objects.create(user=other_candidate)
        other_exp = Experience.objects.create(
            candidate=other_profile, job_title='Dev', company_name='Z', start_date='2022-01-01'
        )

        self.client.post(reverse('candidates:experience_delete', args=[other_exp.pk]))
        self.assertTrue(Experience.objects.filter(pk=other_exp.pk).exists())  # untouched


class ProfileViewEditTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.candidate = User.objects.create_user(
            username='cand_pv', email='candpv@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.client.login(username='cand_pv', password='pass12345')
        self.profile = CandidateProfile.objects.create(user=self.candidate)

    def test_profile_view_loads(self):
        response = self.client.get(reverse('candidates:profile_view'))
        self.assertEqual(response.status_code, 200)

    def test_profile_edit_updates_fields(self):
        response = self.client.post(reverse('candidates:profile_edit'), {
            'headline': 'Aspiring Django Developer',
            'bio': 'I build web apps.',
            'location': 'Hyderabad',
            'linkedin_url': '', 'github_url': '', 'portfolio_url': '',
        })
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.headline, 'Aspiring Django Developer')
        self.assertEqual(self.profile.location, 'Hyderabad')


class SkillManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.candidate = User.objects.create_user(
            username='cand3', email='cand3@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.client.login(username='cand3', password='pass12345')
        self.profile = CandidateProfile.objects.create(user=self.candidate)

    def test_add_multiple_skills_comma_separated(self):
        response = self.client.post(reverse('candidates:skills_manage'), {
            'skills_input': 'Python, Django, SQL',
            'proficiency': 'intermediate',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CandidateSkill.objects.filter(candidate=self.profile).count(), 3)
        self.assertEqual(Skill.objects.count(), 3)

    def test_duplicate_skill_not_added_twice(self):
        skill = Skill.objects.create(name='Python')
        CandidateSkill.objects.create(candidate=self.profile, skill=skill, proficiency='beginner')
        self.client.post(reverse('candidates:skills_manage'), {
            'skills_input': 'Python',
            'proficiency': 'advanced',
        })
        self.assertEqual(CandidateSkill.objects.filter(candidate=self.profile, skill=skill).count(), 1)

    def test_remove_skill(self):
        skill = Skill.objects.create(name='Django')
        cs = CandidateSkill.objects.create(candidate=self.profile, skill=skill, proficiency='beginner')
        self.client.post(reverse('candidates:skill_remove', args=[cs.pk]))
        self.assertFalse(CandidateSkill.objects.filter(pk=cs.pk).exists())
