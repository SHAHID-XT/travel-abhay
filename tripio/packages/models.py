from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse
from destinations.models import Destination
import uuid

class Package(models.Model):
    """
    Travel packages offered by sellers.
    """
    TRANSPORTATION_CHOICES = (
        ('flight', _('Flight')),
        ('train', _('Train')),
        ('bus', _('Bus')),
        ('car', _('Car')),
        ('cruise', _('Cruise')),
        ('multiple', _('Multiple')),
        ('none', _('Not Included')),
    )
    
    DIFFICULTY_CHOICES = (
        ('easy', _('Easy')),
        ('moderate', _('Moderate')),
        ('challenging', _('Challenging')),
        ('difficult', _('Difficult')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                              related_name='packages', verbose_name=_('seller'))
    
    # Basic information
    description = models.TextField(_('description'))
    short_description = models.CharField(_('short description'), max_length=200)
    destinations = models.ManyToManyField(Destination, related_name='packages',
                                         verbose_name=_('destinations'))
    
    # Trip details
    duration_days = models.PositiveIntegerField(_('duration (days)'))
    max_travelers = models.PositiveIntegerField(_('maximum travelers'), default=10)
    transportation_type = models.CharField(_('transportation type'), max_length=20, 
                                          choices=TRANSPORTATION_CHOICES, default='multiple')
    difficulty_level = models.CharField(_('difficulty level'), max_length=20, 
                                       choices=DIFFICULTY_CHOICES, default='moderate')
    
    # Pricing
    base_price = models.DecimalField(_('base price'), max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(_('discount price'), max_digits=10, decimal_places=2, 
                                        null=True, blank=True)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    
    # Additional details
    what_is_included = models.TextField(_('what is included'))
    what_is_excluded = models.TextField(_('what is excluded'))
    
    # Media
    main_image = models.ImageField(_('main image'), upload_to='packages/')
    
    # Availability
    is_active = models.BooleanField(_('active'), default=True)
    featured = models.BooleanField(_('featured'), default=False)
    
    # Metadata
    average_rating = models.DecimalField(_('average rating'), max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(_('review count'), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('package')
        verbose_name_plural = _('packages')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('packages:package_detail', kwargs={'slug': self.slug})
    
    def get_current_price(self):
        if self.discount_price:
            return self.discount_price
        return self.base_price
    
    def get_discount_percentage(self):
        if not self.discount_price:
            return 0
        discount = ((self.base_price - self.discount_price) / self.base_price) * 100
        return round(discount)

class PackageImage(models.Model):
    """
    Additional images for a package.
    """
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='images',
                               verbose_name=_('package'))
    image = models.ImageField(_('image'), upload_to='packages/')
    title = models.CharField(_('title'), max_length=100, blank=True)
    is_featured = models.BooleanField(_('featured'), default=False)
    alt_text = models.CharField(_('alternative text'), max_length=100, blank=True)
    
    # Ordering
    order = models.PositiveIntegerField(_('order'), default=0)
    
    class Meta:
        verbose_name = _('package image')
        verbose_name_plural = _('package images')
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.package.title}"

class Itinerary(models.Model):
    """
    Daily itinerary for a package.
    """
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='itinerary_days',
                               verbose_name=_('package'))
    day = models.PositiveIntegerField(_('day'))
    title = models.CharField(_('title'), max_length=100)
    description = models.TextField(_('description'))
    
    # Location information
    accommodation = models.CharField(_('accommodation'), max_length=200, blank=True)
    meals_included = models.CharField(_('meals included'), max_length=100, blank=True,
                                     help_text=_('E.g., "Breakfast, Lunch"'))
    
    class Meta:
        verbose_name = _('itinerary day')
        verbose_name_plural = _('itinerary days')
        ordering = ['package', 'day']
        unique_together = ('package', 'day')
    
    def __str__(self):
        return f"{self.package.title} - Day {self.day}: {self.title}"

class Availability(models.Model):
    """
    Available dates for a package.
    """
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='availabilities',
                               verbose_name=_('package'))
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'))
    available_slots = models.PositiveIntegerField(_('available slots'))
    is_available = models.BooleanField(_('available'), default=True)
    
    # Special price for this specific date range (optional)
    special_price = models.DecimalField(_('special price'), max_digits=10, decimal_places=2, 
                                       null=True, blank=True)
    
    class Meta:
        verbose_name = _('availability')
        verbose_name_plural = _('availabilities')
        ordering = ['start_date']
    
    def __str__(self):
        return f"{self.package.title}: {self.start_date} to {self.end_date}"
    
    def get_duration(self):
        return (self.end_date - self.start_date).days + 1