from django.contrib import admin
from .models import Skill, CandidateProfile, Education, Experience, CandidateSkill


class CandidateSkillInline(admin.TabularInline):
    model = CandidateSkill
    extra = 1


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 0


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'headline', 'location', 'created_at']
    search_fields = ['user__username', 'user__email', 'headline']
    inlines = [EducationInline, ExperienceInline, CandidateSkillInline]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    search_fields = ['name']


admin.site.register(Education)
admin.site.register(Experience)
admin.site.register(CandidateSkill)
