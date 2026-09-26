def unread_notifications(request):
    """Adds unread_notification_count to every template's context (for the navbar bell icon)."""
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        return {'unread_notification_count': count}
    return {'unread_notification_count': 0}
