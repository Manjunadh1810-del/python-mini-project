from django import forms
from .models import CandidateProfile, Education, Experience, Skill


class CandidateProfileForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ['headline', 'bio', 'location', 'date_of_birth', 'profile_picture',
                  'linkedin_url', 'github_url', 'portfolio_url']
        widgets = {
            'headline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "e.g. Aspiring Python Developer"}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control'}),
        }


class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['degree', 'field_of_study', 'institution', 'start_year', 'end_year', 'grade']
        widgets = {
            'degree': forms.TextInput(attrs={'class': 'form-control'}),
            'field_of_study': forms.TextInput(attrs={'class': 'form-control'}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'start_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'end_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['job_title', 'company_name', 'start_date', 'end_date', 'currently_working', 'description']
        widgets = {
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'currently_working': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SkillAddForm(forms.Form):
    """Free-text, comma-separated skill entry - matched/created against the Skill catalog."""
    skills_input = forms.CharField(
        label="Add Skills (comma-separated)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, Django, SQL, Git'})
    )
    proficiency = forms.ChoiceField(
        choices=[
            ('beginner', 'Beginner'), ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'), ('expert', 'Expert'),
        ],
        initial='intermediate',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
