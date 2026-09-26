import os
from django import forms
from django.conf import settings
from .models import Resume


class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.docx'}),
        }

    def clean_file(self):
        file = self.cleaned_data['file']
        ext = os.path.splitext(file.name)[1].lower()

        if ext not in settings.ALLOWED_RESUME_EXTENSIONS:
            raise forms.ValidationError(
                f"Unsupported file format '{ext}'. Please upload a PDF or DOCX file."
            )

        max_size_bytes = settings.MAX_RESUME_SIZE_MB * 1024 * 1024
        if file.size > max_size_bytes:
            raise forms.ValidationError(
                f"File too large ({file.size / (1024*1024):.1f} MB). Maximum allowed size is {settings.MAX_RESUME_SIZE_MB} MB."
            )

        return file
