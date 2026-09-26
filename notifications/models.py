from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        STATUS_CHANGE = 'status_change', 'Application Status Change'
        INTERVIEW_SCHEDULED = 'interview_scheduled', 'Interview Scheduled'
        NEW_APPLICATION = 'new_application', 'New Application'
        GENERAL = 'general', 'General'

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=25, choices=Type.choices, default=Type.GENERAL)
    link_url = models.CharField(max_length=255, blank=True, help_text="Where clicking this notification should take the user")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.username}: {self.message[:50]}"
