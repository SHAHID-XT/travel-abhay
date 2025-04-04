from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language
from django.views.generic import TemplateView
from core.views import home, set_language, handler404, handler500

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Core app
    path('', home, name='home'),
    path('', include('core.urls')),
    
    # User accounts
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Social authentication
    path('social-auth/', include('social_django.urls', namespace='social')),
    
    # Apps
    path('destinations/', include('destinations.urls')),
    path('packages/', include('packages.urls')),
    path('bookings/', include('bookings.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('chat/', include('chat.urls')),
    path('reviews/', include('reviews.urls')),
    
    # API
    path('api/', include('api.urls')),
    
    # Language selector
    path('i18n/setlang/', set_language, name='set_language'),
    
    # Sitemap
    path('sitemap.xml', include('django.contrib.sitemaps.urls')),
    
    # Security
    path('csp-report/', TemplateView.as_view(template_name='blank.html'), name='csp_report'),
    
    # PWA manifest
    path('manifest.json', TemplateView.as_view(
        template_name='manifest.json',
        content_type='application/json'
    ), name='manifest'),
    
    # Service worker
    path('serviceworker.js', TemplateView.as_view(
        template_name='serviceworker.js',
        content_type='application/javascript'
    ), name='serviceworker'),
]

# Add static and media URLs in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Add debug toolbar URLs in debug mode
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

# Custom error handlers
handler404 = handler404
handler500 = handler500