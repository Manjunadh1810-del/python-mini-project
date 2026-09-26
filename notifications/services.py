"""
Small helper so any app can fire a notification without importing the
Notification model directly everywhere - keeps the creation logic (and any
future extension, like email dispatch) in one place.
"""
from .models import Notification


def notify(user, message, notification_type=Notification.Type.GENERAL, link_url=''):
    """Create a notification for a user. Never raises - a failed notification should never break the calling flow."""
    if not user:
        return None
    try:
        return Notification.objects.create(
            recipient=user, message=message,
            notification_type=notification_type, link_url=link_url,
        )
    except Exception:
        return None
