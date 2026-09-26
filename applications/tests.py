from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from candidates.models import CandidateProfile
from companies.models import Company
from recruiters.models import RecruiterProfile
from jobs.models import Job
from .models import Application


class ApplyToJobTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.candidate = User.objects.create_user(
            username='cand_app', email='candapp@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.candidate_profile = CandidateProfile.objects.create(user=self.candidate)

        self.recruiter = User.objects.create_user(
            username='recr_app', email='recrapp@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        self.company = Company.objects.create(name='AppCo', created_by=self.recruiter)
        self.job = Job.objects.create(company=self.company, posted_by=self.recruiter, title='Dev Role', description='x', status='open')

        self.client.login(username='cand_app', password='pass12345')

    def test_apply_to_open_job(self):
        response = self.client.post(reverse('applications:job_apply', args=[self.job.pk]), {
            'cover_note': 'I am a great fit',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Application.objects.filter(candidate=self.candidate_profile, job=self.job).exists())

    def test_cannot_apply_twice(self):
        Application.objects.create(candidate=self.candidate_profile, job=self.job)
        response = self.client.get(reverse('applications:job_apply', args=[self.job.pk]))
        self.assertEqual(response.status_code, 302)  # redirected to existing application
        self.assertEqual(Application.objects.filter(candidate=self.candidate_profile, job=self.job).count(), 1)

    def test_cannot_apply_to_closed_job(self):
        self.job.status = 'closed'
        self.job.save()
        response = self.client.post(reverse('applications:job_apply', args=[self.job.pk]), {'cover_note': ''})
        self.assertFalse(Application.objects.filter(candidate=self.candidate_profile, job=self.job).exists())

    def test_recruiter_cannot_apply(self):
        self.client.logout()
        self.client.login(username='recr_app', password='pass12345')
        response = self.client.get(reverse('applications:job_apply', args=[self.job.pk]))
        self.assertRedirects(response, reverse('home'))


class ApplicationStatusTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.candidate = User.objects.create_user(
            username='cand_stat', email='candstat@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.candidate_profile = CandidateProfile.objects.create(user=self.candidate)

        self.recruiter = User.objects.create_user(
            username='recr_stat', email='recrstat@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        self.company = Company.objects.create(name='StatCo', created_by=self.recruiter)
        RecruiterProfile.objects.create(user=self.recruiter, company=self.company)
        self.job = Job.objects.create(company=self.company, posted_by=self.recruiter, title='QA Role', description='x', status='open')
        self.application = Application.objects.create(candidate=self.candidate_profile, job=self.job)

    def test_recruiter_can_view_applicants(self):
        self.client.login(username='recr_stat', password='pass12345')
        response = self.client.get(reverse('applications:job_applicants', args=[self.job.pk]))
        self.assertContains(response, 'cand_stat')

    def test_recruiter_can_update_application_status(self):
        self.client.login(username='recr_stat', password='pass12345')
        response = self.client.post(reverse('applications:applicant_detail', args=[self.application.pk]), {
            'status': 'shortlisted',
        })
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'shortlisted')

    def test_other_recruiter_cannot_view_applicant(self):
        other_recruiter = User.objects.create_user(
            username='other_recr2', email='other2@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        self.client.login(username='other_recr2', password='pass12345')
        response = self.client.get(reverse('applications:applicant_detail', args=[self.application.pk]))
        self.assertEqual(response.status_code, 404)

    def test_candidate_sees_own_application_status(self):
        self.client.login(username='cand_stat', password='pass12345')
        response = self.client.get(reverse('applications:application_detail', args=[self.application.pk]))
        self.assertEqual(response.status_code, 200)

    def test_candidate_cannot_see_others_application(self):
        other_candidate = User.objects.create_user(
            username='other_cand', email='othercand@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.client.login(username='other_cand', password='pass12345')
        response = self.client.get(reverse('applications:application_detail', args=[self.application.pk]))
        self.assertEqual(response.status_code, 404)


class InterviewSchedulingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.candidate = User.objects.create_user(
            username='cand_interview', email='candinterview@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.candidate_profile = CandidateProfile.objects.create(user=self.candidate)

        self.recruiter = User.objects.create_user(
            username='recr_interview', email='recrinterview@test.com', password='pass12345', role=User.Role.RECRUITER
        )
        self.company = Company.objects.create(name='InterviewCo', created_by=self.recruiter)
        RecruiterProfile.objects.create(user=self.recruiter, company=self.company)
        self.job = Job.objects.create(company=self.company, posted_by=self.recruiter, title='Dev Role', description='x', status='open')
        self.application = Application.objects.create(candidate=self.candidate_profile, job=self.job)
        self.client.login(username='recr_interview', password='pass12345')

    def test_schedule_online_interview_requires_meeting_link(self):
        response = self.client.post(reverse('applications:schedule_interview', args=[self.application.pk]), {
            'scheduled_date': '2026-12-01', 'scheduled_time': '10:00',
            'mode': 'online', 'meeting_link': '', 'location': '', 'notes': '',
        })
        self.assertEqual(response.status_code, 200)  # form re-rendered with error
        from applications.models import Interview
        self.assertFalse(Interview.objects.filter(application=self.application).exists())

    def test_schedule_online_interview_success(self):
        response = self.client.post(reverse('applications:schedule_interview', args=[self.application.pk]), {
            'scheduled_date': '2026-12-01', 'scheduled_time': '10:00',
            'mode': 'online', 'meeting_link': 'https://meet.google.com/abc', 'location': '', 'notes': 'Bring laptop',
        })
        self.assertEqual(response.status_code, 302)
        from applications.models import Interview
        interview = Interview.objects.get(application=self.application)
        self.assertEqual(interview.mode, 'online')

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'interview_scheduled')

    def test_schedule_interview_notifies_candidate(self):
        from notifications.models import Notification
        self.client.post(reverse('applications:schedule_interview', args=[self.application.pk]), {
            'scheduled_date': '2026-12-01', 'scheduled_time': '10:00',
            'mode': 'online', 'meeting_link': 'https://meet.google.com/abc', 'location': '', 'notes': '',
        })
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.candidate, notification_type=Notification.Type.INTERVIEW_SCHEDULED
            ).exists()
        )

    def test_cancel_interview(self):
        from applications.models import Interview
        from django.utils import timezone
        Interview.objects.create(application=self.application, scheduled_datetime=timezone.now(), mode='online', meeting_link='https://x.com')
        self.client.get(reverse('applications:cancel_interview', args=[self.application.pk]))
        self.assertFalse(Interview.objects.filter(application=self.application).exists())

    def test_status_change_notifies_candidate(self):
        from notifications.models import Notification
        self.client.post(reverse('applications:applicant_detail', args=[self.application.pk]), {
            'status': 'shortlisted',
        })
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.candidate, notification_type=Notification.Type.STATUS_CHANGE
            ).exists()
        )

    def test_new_application_notifies_recruiter(self):
        from notifications.models import Notification
        job2 = Job.objects.create(company=self.company, posted_by=self.recruiter, title='Second Role', description='y', status='open')
        self.client.logout()
        self.client.login(username='cand_interview', password='pass12345')
        self.client.post(reverse('applications:job_apply', args=[job2.pk]), {'cover_note': ''})
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.recruiter, notification_type=Notification.Type.NEW_APPLICATION
            ).exists()
        )
