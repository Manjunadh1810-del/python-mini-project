from django import forms
from .models import Job


class JobForm(forms.ModelForm):
    required_skills_input = forms.CharField(
        label="Required Skills (comma-separated)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, Django, SQL'}),
        required=True,
    )
    preferred_skills_input = forms.CharField(
        label="Preferred / Nice-to-have Skills (comma-separated, optional)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Docker, AWS'}),
        required=False,
    )

    class Meta:
        model = Job
        fields = [
            'title', 'description', 'responsibilities', 'job_type', 'work_mode', 'location',
            'min_experience', 'max_experience', 'min_salary', 'max_salary',
            'status', 'application_deadline',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'responsibilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'work_mode': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'min_experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'application_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        min_exp = cleaned_data.get('min_experience')
        max_exp = cleaned_data.get('max_experience')
        if min_exp is not None and max_exp is not None and max_exp < min_exp:
            raise forms.ValidationError("Maximum experience cannot be less than minimum experience.")

        min_sal = cleaned_data.get('min_salary')
        max_sal = cleaned_data.get('max_salary')
        if min_sal is not None and max_sal is not None and max_sal < min_sal:
            raise forms.ValidationError("Maximum salary cannot be less than minimum salary.")
        return cleaned_data


class JobSearchForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Search job title, skill, or company'}))
    location = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Location'}))
    job_type = forms.ChoiceField(required=False, choices=[('', 'All Types')] + list(Job.JobType.choices),
                                  widget=forms.Select(attrs={'class': 'form-select'}))
    work_mode = forms.ChoiceField(required=False, choices=[('', 'All Modes')] + list(Job.WorkMode.choices),
                                   widget=forms.Select(attrs={'class': 'form-select'}))
