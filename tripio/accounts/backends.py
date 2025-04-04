from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django_otp import verify_token, devices_for_user

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentication backend that allows login with either email or username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to fetch the user by email or username
            user = User.objects.get(Q(username=username) | Q(email=username))
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        
    def verify_otp(self, user, token):
        """
        Verify the provided OTP token for the given user.
        """
        if not user.two_factor_enabled:
            return True
            
        for device in devices_for_user(user):
            if device.is_verified() and verify_token(user, device, token):
                return True
        return False