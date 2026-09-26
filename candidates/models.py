from django.conf import settings
from django.db import models


class Skill(models.Model):
    """
    Shared skill catalog. Used by CandidateSkill here and by JobSkill
    in the jobs app (Phase 5), so both candidates and job postings
    reference the same canonical skill names for accurate matching.
    """
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True, help_text="e.g. Programming, Database, Soft Skill")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CandidateProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='candidate_profile')
    headline = models.CharField(max_length=150, blank=True, help_text="e.g. 'Aspiring Python Developer'")
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    skills = models.ManyToManyField(Skill, through='CandidateSkill', related_name='candidates')

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def profile_completion_percentage(self):
        """
        Simple, explainable completion score across key sections.
        Each of the 6 checks below is worth ~16.67%.
        """
        checks = [
            bool(self.headline),
            bool(self.bio),
            bool(self.location),
            self.education_entries.exists(),
            self.experience_entries.exists(),
            self.candidateskill_set.exists(),
        ]
        completed = sum(1 for c in checks if c)
        return round((completed / len(checks)) * 100)


class Education(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='education_entries')
    degree = models.CharField(max_length=150, help_text="e.g. B.Tech, M.Sc")
    field_of_study = models.CharField(max_length=150, blank=True, help_text="e.g. Computer Science")
    institution = models.CharField(max_length=200)
    start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank if ongoing")
    grade = models.CharField(max_length=50, blank=True, help_text="e.g. 8.5 CGPA or 85%")

    class Meta:
        ordering = ['-start_year']

    def __str__(self):
        return f"{self.degree} - {self.institution}"


class Experience(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='experience_entries')
    job_title = models.CharField(max_length=150)
    company_name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    currently_working = models.BooleanField(default=False)
    description = models.TextField(blank=True, help_text="Key responsibilities and achievements")

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"


class CandidateSkill(models.Model):
    class Proficiency(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'
        EXPERT = 'expert', 'Expert'

    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency = models.CharField(max_length=20, choices=Proficiency.choices, default=Proficiency.INTERMEDIATE)

    class Meta:
        unique_together = ('candidate', 'skill')

    def __str__(self):
        return f"{self.candidate.user.username} - {self.skill.name} ({self.proficiency})"
