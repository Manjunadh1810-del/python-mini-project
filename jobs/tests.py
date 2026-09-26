from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from companies.models import Company
from recruiters.models import RecruiterProfile
from candidates.models import Skill
from .models import Job, JobSkill


class JobPostingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.recruiter = User.objects.create_user(
            username='recr_job', email='recrjob@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        self.company = Company.objects.create(name='JobCo', created_by=self.recruiter)
        self.profile = RecruiterProfile.objects.create(user=self.recruiter, company=self.company)
        self.client.login(username='recr_job', password='pass12345')

    def test_post_job_with_skills(self):
        response = self.client.post(reverse('jobs:job_create'), {
            'title': 'Python Developer',
            'description': 'Build backend systems',
            'responsibilities': '',
            'job_type': 'full_time',
            'work_mode': 'remote',
            'location': 'Hyderabad',
            'min_experience': 1,
            'max_experience': 3,
            'min_salary': 500000,
            'max_salary': 800000,
            'required_skills_input': 'Python, Django, SQL',
            'preferred_skills_input': 'Docker',
            'status': 'open',
        })
        self.assertEqual(response.status_code, 302)
        job = Job.objects.get(title='Python Developer')
        self.assertEqual(job.company, self.company)
        self.assertEqual(job.mandatory_skills().count(), 3)
        self.assertEqual(job.preferred_skills().count(), 1)

    def test_job_requires_company(self):
        RecruiterProfile.objects.filter(user=self.recruiter).update(company=None)
        response = self.client.get(reverse('jobs:job_create'))
        self.assertRedirects(response, reverse('recruiters:company_create'))

    def test_max_experience_less_than_min_rejected(self):
        response = self.client.post(reverse('jobs:job_create'), {
            'title': 'Bad Job', 'description': 'x', 'responsibilities': '',
            'job_type': 'full_time', 'work_mode': 'remote', 'location': 'X',
            'min_experience': 5, 'max_experience': 2,
            'required_skills_input': 'Python', 'preferred_skills_input': '',
            'status': 'open',
        })
        self.assertEqual(response.status_code, 200)  # form re-rendered with error
        self.assertFalse(Job.objects.filter(title='Bad Job').exists())

    def test_candidate_cannot_post_job(self):
        candidate = User.objects.create_user(
            username='cand_job', email='candjob@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.client.logout()
        self.client.login(username='cand_job', password='pass12345')
        response = self.client.get(reverse('jobs:job_create'))
        self.assertRedirects(response, reverse('home'))

    def test_recruiter_cannot_edit_other_companys_job(self):
        other_recruiter = User.objects.create_user(
            username='other_recr', email='other@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        other_company = Company.objects.create(name='OtherCo', created_by=other_recruiter)
        job = Job.objects.create(company=other_company, posted_by=other_recruiter, title='Other Job', description='x')
        response = self.client.get(reverse('jobs:job_edit', args=[job.pk]))
        self.assertEqual(response.status_code, 404)

    def test_job_detail_recruiter_view_accessible_for_own_job(self):
        job = Job.objects.create(company=self.company, posted_by=self.recruiter, title='My Job', description='x')
        response = self.client.get(reverse('jobs:job_detail_recruiter', args=[job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Job')

    def test_job_detail_recruiter_view_blocked_for_other_companys_job(self):
        other_recruiter = User.objects.create_user(
            username='other_recr2', email='other2@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        other_company = Company.objects.create(name='OtherCo2', created_by=other_recruiter)
        job = Job.objects.create(company=other_company, posted_by=other_recruiter, title='Not Mine', description='x')
        response = self.client.get(reverse('jobs:job_detail_recruiter', args=[job.pk]))
        self.assertEqual(response.status_code, 404)


class JobCloseReopenTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.recruiter = User.objects.create_user(
            username='recr_close', email='recrclose@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        self.company = Company.objects.create(name='CloseCo', created_by=self.recruiter)
        RecruiterProfile.objects.create(user=self.recruiter, company=self.company)
        self.job = Job.objects.create(company=self.company, posted_by=self.recruiter, title='Test Job', description='x', status='open')
        self.client.login(username='recr_close', password='pass12345')

    def test_close_job(self):
        self.client.get(reverse('jobs:job_close', args=[self.job.pk]))
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'closed')

    def test_reopen_job(self):
        self.job.status = 'closed'
        self.job.save()
        self.client.get(reverse('jobs:job_reopen', args=[self.job.pk]))
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'open')

    def test_delete_job(self):
        self.client.get(reverse('jobs:job_delete', args=[self.job.pk]))
        self.assertFalse(Job.objects.filter(pk=self.job.pk).exists())


class PublicJobListingTests(TestCase):
    def setUp(self):
        self.client = Client()
        recruiter = User.objects.create_user(
            username='recr_pub', email='recrpub@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        company = Company.objects.create(name='PubCo', created_by=recruiter)
        self.open_job = Job.objects.create(company=company, posted_by=recruiter, title='Open Job', description='x', status='open')
        self.closed_job = Job.objects.create(company=company, posted_by=recruiter, title='Closed Job', description='x', status='closed')

    def test_public_listing_shows_only_open_jobs(self):
        response = self.client.get(reverse('jobs:job_list_public'))
        self.assertContains(response, 'Open Job')
        self.assertNotContains(response, 'Closed Job')

    def test_job_search_by_title(self):
        response = self.client.get(reverse('jobs:job_list_public'), {'q': 'Open'})
        self.assertContains(response, 'Open Job')

    def test_public_job_detail_accessible_without_login(self):
        response = self.client.get(reverse('jobs:job_detail_public', args=[self.open_job.pk]))
        self.assertEqual(response.status_code, 200)

    def test_public_job_detail_shows_match_score_for_logged_in_candidate(self):
        candidate = User.objects.create_user(
            username='pub_detail_cand', email='pubdetailcand@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.client.login(username='pub_detail_cand', password='pass12345')
        response = self.client.get(reverse('jobs:job_detail_public', args=[self.open_job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('match', response.context)
        self.assertIn('match_score', response.context['match'])

    def test_job_search_by_location_filters_correctly(self):
        self.open_job.location = 'Hyderabad'
        self.open_job.save()
        response = self.client.get(reverse('jobs:job_list_public'), {'location': 'Hyderabad'})
        self.assertContains(response, 'Open Job')
        response2 = self.client.get(reverse('jobs:job_list_public'), {'location': 'Mumbai'})
        self.assertNotContains(response2, 'Open Job')

    def test_job_search_by_job_type_filters_correctly(self):
        self.open_job.job_type = 'internship'
        self.open_job.save()
        response = self.client.get(reverse('jobs:job_list_public'), {'job_type': 'internship'})
        self.assertContains(response, 'Open Job')
        response2 = self.client.get(reverse('jobs:job_list_public'), {'job_type': 'contract'})
        self.assertNotContains(response2, 'Open Job')

    def test_job_search_by_work_mode_filters_correctly(self):
        self.open_job.work_mode = 'remote'
        self.open_job.save()
        response = self.client.get(reverse('jobs:job_list_public'), {'work_mode': 'remote'})
        self.assertContains(response, 'Open Job')
        response2 = self.client.get(reverse('jobs:job_list_public'), {'work_mode': 'onsite'})
        self.assertNotContains(response2, 'Open Job')

    def test_job_search_by_skill_keyword(self):
        from candidates.models import Skill
        from jobs.models import JobSkill
        skill = Skill.objects.create(name='Kubernetes')
        JobSkill.objects.create(job=self.open_job, skill=skill, is_mandatory=True)
        response = self.client.get(reverse('jobs:job_list_public'), {'q': 'Kubernetes'})
        self.assertContains(response, 'Open Job')
