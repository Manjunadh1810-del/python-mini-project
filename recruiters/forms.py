from django import forms
from .models import RecruiterProfile


class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = ['designation']
        widgets = {
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. HR Manager'}),
        }
