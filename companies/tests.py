from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from recruiters.models import RecruiterProfile
from .models import Company


class CompanyCreationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.recruiter = User.objects.create_user(
            username='recr1', email='recr1@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        self.candidate = User.objects.create_user(
            username='cand1', email='cand1@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.client.login(username='recr1', password='pass12345')

    def test_create_company(self):
        response = self.client.post(reverse('recruiters:company_create'), {
            'name': 'Test Corp', 'description': 'A test company',
            'industry': 'IT', 'website': 'https://testcorp.com',
            'location': 'Hyderabad', 'company_size': '11-50', 'founded_year': 2015,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Company.objects.filter(name='Test Corp').exists())
        profile = RecruiterProfile.objects.get(user=self.recruiter)
        self.assertEqual(profile.company.name, 'Test Corp')

    def test_candidate_cannot_create_company(self):
        self.client.logout()
        self.client.login(username='cand1', password='pass12345')
        response = self.client.get(reverse('recruiters:company_create'))
        self.assertRedirects(response, reverse('home'))

    def test_company_name_must_be_unique(self):
        Company.objects.create(name='Duplicate Co', created_by=self.recruiter)
        response = self.client.post(reverse('recruiters:company_create'), {
            'name': 'Duplicate Co', 'description': '', 'industry': '',
            'website': '', 'location': '', 'company_size': '', 'founded_year': '',
        })
        self.assertEqual(response.status_code, 200)  # form re-rendered with error
        self.assertEqual(Company.objects.filter(name='Duplicate Co').count(), 1)

    def test_edit_company_updates_fields(self):
        profile, _ = RecruiterProfile.objects.get_or_create(user=self.recruiter)
        company = Company.objects.create(name='EditMe Co', created_by=self.recruiter, description='Old description')
        profile.company = company
        profile.save()

        response = self.client.post(reverse('recruiters:company_edit'), {
            'name': 'EditMe Co', 'description': 'New description',
            'industry': 'FinTech', 'website': '', 'location': 'Pune',
            'company_size': '11-50', 'founded_year': 2020,
        })
        self.assertEqual(response.status_code, 302)
        company.refresh_from_db()
        self.assertEqual(company.description, 'New description')
        self.assertEqual(company.industry, 'FinTech')

    def test_edit_company_without_company_redirects_to_create(self):
        response = self.client.get(reverse('recruiters:company_edit'))
        self.assertRedirects(response, reverse('recruiters:company_create'))
