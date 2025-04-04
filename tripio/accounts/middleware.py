from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model

User = get_user_model()

class UserActivityMiddleware(MiddlewareMixin):
    """
    Middleware to track when a user was last active.
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            # Update last_active timestamp
            User.objects.filter(pk=request.user.pk).update(last_active=timezone.now())