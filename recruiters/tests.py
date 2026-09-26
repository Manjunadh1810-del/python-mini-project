from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from companies.models import Company
from .models import RecruiterProfile


class RecruiterDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.recruiter = User.objects.create_user(
            username='recr2', email='recr2@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        self.client.login(username='recr2', password='pass12345')

    def test_dashboard_prompts_company_creation_when_none_exists(self):
        response = self.client.get(reverse('recruiters:dashboard'))
        self.assertContains(response, "Create Company Profile")

    def test_dashboard_shows_company_once_created(self):
        profile, _ = RecruiterProfile.objects.get_or_create(user=self.recruiter)
        company = Company.objects.create(name='My Co', created_by=self.recruiter)
        profile.company = company
        profile.save()
        response = self.client.get(reverse('recruiters:dashboard'))
        self.assertContains(response, 'My Co')

    def test_company_detail_redirects_if_no_company(self):
        response = self.client.get(reverse('recruiters:company_detail'))
        self.assertRedirects(response, reverse('recruiters:company_create'))

    def test_recruiter_profile_auto_created(self):
        self.assertFalse(RecruiterProfile.objects.filter(user=self.recruiter).exists())
        self.client.get(reverse('recruiters:dashboard'))
        self.assertTrue(RecruiterProfile.objects.filter(user=self.recruiter).exists())

    def test_dashboard_shows_shortlisted_and_interview_counts(self):
        from candidates.models import CandidateProfile
        from applications.models import Application

        profile, _ = RecruiterProfile.objects.get_or_create(user=self.recruiter)
        company = Company.objects.create(name='StatDashCo', created_by=self.recruiter)
        profile.company = company
        profile.save()

        candidate_user = User.objects.create_user(
            username='dash_applicant', email='dashapplicant@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        candidate_profile = CandidateProfile.objects.create(user=candidate_user)

        from jobs.models import Job
        job = Job.objects.create(company=company, posted_by=self.recruiter, title='Dev', description='x', status='open')
        Application.objects.create(candidate=candidate_profile, job=job, status='shortlisted')

        response = self.client.get(reverse('recruiters:dashboard'))
        self.assertEqual(response.context['shortlisted_count'], 1)
        self.assertIsNotNone(response.context['avg_match_score'])

    def test_delete_company_allows_recreation(self):
        profile, _ = RecruiterProfile.objects.get_or_create(user=self.recruiter)
        company = Company.objects.create(name='Old Co', created_by=self.recruiter)
        profile.company = company
        profile.save()

        response = self.client.post(reverse('recruiters:company_delete'))
        self.assertRedirects(response, reverse('recruiters:company_create'))
        self.assertFalse(Company.objects.filter(name='Old Co').exists())

        profile.refresh_from_db()
        self.assertIsNone(profile.company)

        # Now recreate
        response = self.client.post(reverse('recruiters:company_create'), {
            'name': 'New Co', 'description': '', 'industry': '',
            'website': '', 'location': '', 'company_size': '', 'founded_year': '',
        })
        self.assertEqual(response.status_code, 302)
        profile.refresh_from_db()
        self.assertEqual(profile.company.name, 'New Co')
