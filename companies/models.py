from django.conf import settings
from django.db import models


class Company(models.Model):
    class CompanySize(models.TextChoices):
        MICRO = '1-10', '1-10 employees'
        SMALL = '11-50', '11-50 employees'
        MEDIUM = '51-200', '51-200 employees'
        LARGE = '201-500', '201-500 employees'
        ENTERPRISE = '501+', '501+ employees'

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    industry = models.CharField(max_length=100, blank=True, help_text="e.g. IT Services, FinTech, E-commerce")
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    location = models.CharField(max_length=150, blank=True)
    company_size = models.CharField(max_length=20, choices=CompanySize.choices, blank=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='companies_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def __str__(self):
        return self.name

    def active_jobs_count(self):
        return self.jobs.filter(status='open').count() if hasattr(self, 'jobs') else 0
