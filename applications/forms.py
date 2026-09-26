from datetime import datetime
from django import forms
from .models import Application, Interview


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_note']
        widgets = {
            'cover_note': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Optional: tell the recruiter why you are a good fit (not required)'
            }),
        }


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class InterviewForm(forms.ModelForm):
    scheduled_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    scheduled_time = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}))

    class Meta:
        model = Interview
        fields = ['mode', 'meeting_link', 'location', 'notes']
        widgets = {
            'mode': forms.Select(attrs={'class': 'form-select'}),
            'meeting_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://meet.google.com/...'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Office address'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Instructions for the candidate'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get('mode')
        if mode == Interview.Mode.ONLINE and not cleaned_data.get('meeting_link'):
            raise forms.ValidationError("A meeting link is required for online interviews.")
        if mode == Interview.Mode.IN_PERSON and not cleaned_data.get('location'):
            raise forms.ValidationError("A location is required for in-person interviews.")
        return cleaned_data

    def save(self, commit=True):
        from django.utils import timezone
        interview = super().save(commit=False)
        date = self.cleaned_data['scheduled_date']
        time = self.cleaned_data['scheduled_time']
        naive_dt = datetime.combine(date, time)
        interview.scheduled_datetime = timezone.make_aware(naive_dt) if timezone.is_naive(naive_dt) else naive_dt
        if commit:
            interview.save()
        return interview
