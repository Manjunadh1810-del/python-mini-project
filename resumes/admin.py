from django.contrib import admin
from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'original_filename', 'file_type', 'file_size_kb', 'extraction_successful', 'is_analyzed', 'uploaded_at']
    list_filter = ['file_type', 'extraction_successful']
    search_fields = ['candidate__user__username']
    readonly_fields = ['extracted_text', 'extracted_skills', 'extracted_education_hints']
