from django.contrib import admin
from .models import Job, JobSkill


class JobSkillInline(admin.TabularInline):
    model = JobSkill
    extra = 1


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'job_type', 'work_mode', 'status', 'posted_by', 'created_at']
    list_filter = ['status', 'job_type', 'work_mode']
    search_fields = ['title', 'company__name']
    inlines = [JobSkillInline]


admin.site.register(JobSkill)
