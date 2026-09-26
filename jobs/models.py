from django.conf import settings
from django.db import models
from companies.models import Company
from candidates.models import Skill


class Job(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full-time'
        PART_TIME = 'part_time', 'Part-time'
        INTERNSHIP = 'internship', 'Internship'
        CONTRACT = 'contract', 'Contract'

    class WorkMode(models.TextChoices):
        REMOTE = 'remote', 'Remote'
        ONSITE = 'onsite', 'Onsite'
        HYBRID = 'hybrid', 'Hybrid'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        OPEN = 'open', 'Open'
        CLOSED = 'closed', 'Closed'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='jobs_posted')

    title = models.CharField(max_length=200)
    description = models.TextField()
    responsibilities = models.TextField(blank=True)

    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME)
    work_mode = models.CharField(max_length=20, choices=WorkMode.choices, default=WorkMode.ONSITE)
    location = models.CharField(max_length=150, blank=True)

    min_experience = models.PositiveIntegerField(default=0, help_text="Minimum years of experience required")
    max_experience = models.PositiveIntegerField(null=True, blank=True)

    min_salary = models.PositiveIntegerField(null=True, blank=True, help_text="Annual, in your local currency")
    max_salary = models.PositiveIntegerField(null=True, blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    application_deadline = models.DateField(null=True, blank=True)

    skills = models.ManyToManyField(Skill, through='JobSkill', related_name='jobs')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company.name}"

    def is_open(self):
        return self.status == self.Status.OPEN

    def mandatory_skills(self):
        return self.jobskill_set.filter(is_mandatory=True).select_related('skill')

    def preferred_skills(self):
        return self.jobskill_set.filter(is_mandatory=False).select_related('skill')

    def applicant_count(self):
        return self.applications.count() if hasattr(self, 'applications') else 0


class JobSkill(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    is_mandatory = models.BooleanField(default=True)

    class Meta:
        unique_together = ('job', 'skill')

    def __str__(self):
        req = "Required" if self.is_mandatory else "Preferred"
        return f"{self.job.title} - {self.skill.name} ({req})"
