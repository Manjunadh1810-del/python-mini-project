from django.db import models
from candidates.models import CandidateProfile
from jobs.models import Job


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = 'applied', 'Applied'
        UNDER_REVIEW = 'under_review', 'Under Review'
        SHORTLISTED = 'shortlisted', 'Shortlisted'
        INTERVIEW_SCHEDULED = 'interview_scheduled', 'Interview Scheduled'
        SELECTED = 'selected', 'Selected'
        REJECTED = 'rejected', 'Rejected'

    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.APPLIED)
    cover_note = models.TextField(blank=True, help_text="Optional note to the recruiter")

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('candidate', 'job')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.candidate.user.username} -> {self.job.title} ({self.get_status_display()})"

    # Ordered pipeline used to render a status timeline in templates.
    PIPELINE = [Status.APPLIED, Status.UNDER_REVIEW, Status.SHORTLISTED, Status.INTERVIEW_SCHEDULED, Status.SELECTED]

    def status_step_index(self):
        """Position in the pipeline (for a progress timeline). Rejected is handled separately."""
        try:
            return self.PIPELINE.index(self.status)
        except ValueError:
            return -1


class Interview(models.Model):
    class Mode(models.TextChoices):
        ONLINE = 'online', 'Online'
        IN_PERSON = 'in_person', 'In-Person'
        PHONE = 'phone', 'Phone'

    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='interview')
    scheduled_datetime = models.DateTimeField()
    mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.ONLINE)
    meeting_link = models.URLField(blank=True, help_text="Required for online interviews")
    location = models.CharField(max_length=255, blank=True, help_text="Required for in-person interviews")
    notes = models.TextField(blank=True, help_text="Instructions for the candidate (what to bring, round details, etc.)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Interview - {self.application}"

    def is_upcoming(self):
        from django.utils import timezone
        return self.scheduled_datetime >= timezone.now()
