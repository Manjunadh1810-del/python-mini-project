from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'location', 'company_size', 'created_by', 'created_at']
    search_fields = ['name', 'industry', 'location']
    list_filter = ['industry', 'company_size']
