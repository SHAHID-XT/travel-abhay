from django.http import HttpResponsePermanentRedirect
from django.conf import settings
import re

class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Content-Security-Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://www.googletagmanager.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "img-src 'self' data: https://res.cloudinary.com https://maps.googleapis.com; "
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
            "connect-src 'self' https://maps.googleapis.com; "
            "frame-src 'self' https://www.google.com https://js.stripe.com; "
            "object-src 'none';"
        )
        response['Content-Security-Policy'] = csp_policy
        
        # Other security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(self), camera=(), microphone=()'
        
        # Cache control for static assets
        if re.match(r'^/static/', request.path) or re.match(r'^/media/', request.path):
            response['Cache-Control'] = 'public, max-age=31536000'
        
        # Ensure session cookies are secure
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response

class SecureRequiredMiddleware:
    """
    Middleware to redirect all HTTP requests to HTTPS.
    Only active when DEBUG is False.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if not settings.DEBUG and not request.is_secure():
            url = request.build_absolute_uri(request.get_full_path())
            secure_url = url.replace('http://', 'https://')
            return HttpResponsePermanentRedirect(secure_url)
        
        return self.get_response(request)

class ContentSecurityPolicyReportingMiddleware:
    """
    Middleware to log Content Security Policy violations.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        return self.get_response(request)
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path == '/csp-report/' and request.method == 'POST':
            import json
            import logging
            
            logger = logging.getLogger('csp_violations')
            try:
                data = json.loads(request.body.decode('utf-8'))
                report = data.get('csp-report', {})
                logger.warning(f"CSP Violation: {report}")
            except Exception as e:
                logger.error(f"Error processing CSP report: {e}")