from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User, Profile

class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form with enhanced styling
    """
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Email or Username'),
                'autofocus': True
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Password')
            }
        )
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class RegistrationForm(UserCreationForm):
    """
    Form for registering a new user
    """
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Email Address')
            }
        )
    )
    username = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Username')
            }
        )
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('First Name')
            }
        )
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Last Name')
            }
        )
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Password')
            }
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Confirm Password')
            }
        )
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES[:-1],  # Exclude admin role
        required=True,
        initial=User.ROLE_BUYER,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'role')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('This email address is already in use.'))
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_('This username is already taken.'))
        return username

class ProfileForm(forms.ModelForm):
    """
    Form for updating user profile information
    """
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control date-picker',
                'type': 'date'
            }
        )
    )
    
    class Meta:
        model = Profile
        fields = ('date_of_birth', 'preferred_language', 'preferred_currency',
                 'facebook', 'twitter', 'instagram', 'linkedin', 'interests')
        widgets = {
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
            'preferred_currency': forms.Select(attrs={'class': 'form-select'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/username'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://twitter.com/username'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/username'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/username'}),
            'interests': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }

class UserForm(forms.ModelForm):
    """
    Form for updating user information
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'phone_number',
                 'bio', 'profile_image', 'country', 'city', 'company_name', 'website')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': True}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Custom password change form with enhanced styling
    """
    old_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Current Password')
            }
        )
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('New Password')
            }
        )
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('Confirm New Password')
            }
        )
    )

class TwoFactorSetupForm(forms.Form):
    """
    Form for setting up two-factor authentication
    """
    token = forms.CharField(
        required=True,
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control otp-input',
                'placeholder': _('Enter 6-digit code'),
                'autocomplete': 'off'
            }
        )
    )