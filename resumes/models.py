import os
from django.db import models
from candidates.models import CandidateProfile


def resume_upload_path(instance, filename):
    return f"resumes/user_{instance.candidate.user.id}/{filename}"


class Resume(models.Model):
    """
    One active resume per candidate. Re-uploading replaces the file and
    re-triggers text extraction (old file is removed to avoid orphaned media).
    """
    candidate = models.OneToOneField(CandidateProfile, on_delete=models.CASCADE, related_name='resume')
    file = models.FileField(upload_to=resume_upload_path)
    original_filename = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=10, blank=True, help_text="pdf or docx")
    file_size_kb = models.PositiveIntegerField(default=0)

    extracted_text = models.TextField(blank=True)
    extraction_successful = models.BooleanField(default=False)
    extraction_error = models.CharField(max_length=255, blank=True)

    # Phase 8: AI analysis results, derived from extracted_text
    extracted_skills = models.JSONField(default=list, blank=True)
    extracted_education_hints = models.JSONField(default=list, blank=True)
    experience_years_hint = models.FloatField(null=True, blank=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Resume - {self.candidate.user.username}"

    def filename(self):
        return self.original_filename or os.path.basename(self.file.name)

    def is_analyzed(self):
        return self.analyzed_at is not None
