from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from packages.models import Package
from destinations.models import Destination

class UserActivity(models.Model):
    """
    Tracks user activity such as page views, click events, etc.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                           related_name='activities', verbose_name=_('user'),
                           null=True, blank=True)  # Allow anonymous tracking
    
    # Session information
    session_id = models.CharField(_('session ID'), max_length=50)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    
    # Activity details
    action = models.CharField(_('action'), max_length=50)
    page = models.CharField(_('page'), max_length=255)
    
    # Related models
    package = models.ForeignKey(Package, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name='activities',
                              verbose_name=_('package'))
    destination = models.ForeignKey(Destination, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='activities',
                                   verbose_name=_('destination'))
    
    # Additional data
    metadata = models.JSONField(_('metadata'), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('user activity')
        verbose_name_plural = _('user activities')
        ordering = ['-created_at']
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} - {self.action} - {self.created_at}"

class SellerStats(models.Model):
    """
    Aggregated statistics for sellers.
    """
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                             related_name='seller_stats', verbose_name=_('seller'))
    date = models.DateField(_('date'))
    
    # Package statistics
    package_views = models.PositiveIntegerField(_('package views'), default=0)
    package_bookings = models.PositiveIntegerField(_('package bookings'), default=0)
    total_sales = models.DecimalField(_('total sales'), max_digits=12, decimal_places=2, default=0)
    
    # Activity metrics
    inquiry_count = models.PositiveIntegerField(_('inquiry count'), default=0)
    response_time_avg = models.DurationField(_('average response time'), null=True, blank=True)
    
    # Revenue
    commission_amount = models.DecimalField(_('commission amount'), max_digits=12, decimal_places=2, default=0)
    net_earnings = models.DecimalField(_('net earnings'), max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = _('seller stats')
        verbose_name_plural = _('seller stats')
        ordering = ['-date']
        unique_together = [('seller', 'date')]
    
    def __str__(self):
        return f"Stats for {self.seller.username} on {self.date}"

class SearchTerm(models.Model):
    """
    Tracks search terms and their frequency.
    """
    term = models.CharField(_('term'), max_length=255)
    count = models.PositiveIntegerField(_('count'), default=1)
    last_searched = models.DateTimeField(_('last searched'), auto_now=True)
    first_searched = models.DateTimeField(_('first searched'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('search term')
        verbose_name_plural = _('search terms')
        ordering = ['-count']
    
    def __str__(self):
        return f"{self.term} (searched {self.count} times)"