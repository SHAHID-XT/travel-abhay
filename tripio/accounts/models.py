from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.base_user import BaseUserManager
from django.conf import settings
import uuid

class UserManager(BaseUserManager):
    """
    Custom user manager for the User model.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', User.ROLE_ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with email as the username field.
    Includes role-based permissions for buyers, sellers, and admins.
    """
    ROLE_BUYER = 'buyer'
    ROLE_SELLER = 'seller'
    ROLE_ADMIN = 'admin'
    
    ROLE_CHOICES = (
        (ROLE_BUYER, _('Buyer')),
        (ROLE_SELLER, _('Seller')),
        (ROLE_ADMIN, _('Admin')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), max_length=30, unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_verified = models.BooleanField(_('verified'), default=False)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_active = models.DateTimeField(_('last active'), null=True, blank=True)
    
    role = models.CharField(_('role'), max_length=10, choices=ROLE_CHOICES, default=ROLE_BUYER)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    bio = models.TextField(_('bio'), blank=True)
    
    # 2FA settings
    two_factor_enabled = models.BooleanField(_('2FA enabled'), default=False)
    
    # Notification preferences
    email_notifications = models.BooleanField(_('email notifications'), default=True)
    push_notifications = models.BooleanField(_('push notifications'), default=True)
    
    # Location information
    country = models.CharField(_('country'), max_length=50, blank=True)
    city = models.CharField(_('city'), max_length=50, blank=True)
    
    # Additional fields for sellers
    company_name = models.CharField(_('company name'), max_length=100, blank=True)
    website = models.URLField(_('website'), blank=True)
    is_verified_seller = models.BooleanField(_('verified seller'), default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
    
    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    def is_buyer(self):
        return self.role == self.ROLE_BUYER
    
    def is_seller(self):
        return self.role == self.ROLE_SELLER
    
    def is_admin(self):
        return self.role == self.ROLE_ADMIN
    
    def __str__(self):
        return self.email

class Profile(models.Model):
    """
    Extended profile information for users.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    preferred_language = models.CharField(_('preferred language'), max_length=10, choices=settings.LANGUAGES, default='en')
    preferred_currency = models.CharField(_('preferred currency'), max_length=3, default='USD')
    
    # Social media links
    facebook = models.URLField(_('Facebook'), blank=True)
    twitter = models.URLField(_('Twitter'), blank=True)
    instagram = models.URLField(_('Instagram'), blank=True)
    linkedin = models.URLField(_('LinkedIn'), blank=True)
    
    # Travel preferences
    interests = models.ManyToManyField('destinations.TravelInterest', blank=True)
    
    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')
    
    def __str__(self):
        return f"Profile for {self.user.email}"