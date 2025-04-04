from django.conf import settings

def app_settings(request):
    """
    Makes application settings available to templates.
    """
    return {
        'APP_NAME': settings.APP_NAME,
        'LANGUAGES': settings.LANGUAGES,
    }