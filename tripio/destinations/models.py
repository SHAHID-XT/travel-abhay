from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models as gis_models
from django.conf import settings
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
import uuid

class TravelInterest(models.Model):
    """
    Categories of travel interests like adventure, cultural, family, etc.
    """
    name = models.CharField(_('name'), max_length=50)
    icon = models.CharField(_('icon'), max_length=50, help_text=_('CSS class name for the icon'))
    
    class Meta:
        verbose_name = _('travel interest')
        verbose_name_plural = _('travel interests')
    
    def __str__(self):
        return self.name

class Region(MPTTModel):
    """
    Hierarchical regions (continent -> country -> state/province -> city)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    code = models.CharField(_('code'), max_length=10, blank=True, help_text=_('Country/region code'))
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                            related_name='children', verbose_name=_('parent'))
    description = models.TextField(_('description'), blank=True)
    image = models.ImageField(_('image'), upload_to='regions/', blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    featured = models.BooleanField(_('featured'), default=False)
    
    class MPTTMeta:
        order_insertion_by = ['name']
        
    class Meta:
        verbose_name = _('region')
        verbose_name_plural = _('regions')
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('destinations:region_detail', kwargs={'slug': self.slug})

class Destination(models.Model):
    """
    Specific travel destinations (landmarks, attractions, natural sites, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='destinations',
                              verbose_name=_('region'))
    description = models.TextField(_('description'))
    short_description = models.CharField(_('short description'), max_length=200)
    location = gis_models.PointField(_('location'))
    address = models.CharField(_('address'), max_length=255, blank=True)
    
    # Media
    main_image = models.ImageField(_('main image'), upload_to='destinations/')
    
    # Meta information
    interests = models.ManyToManyField(TravelInterest, related_name='destinations',
                                      verbose_name=_('travel interests'))
    average_rating = models.DecimalField(_('average rating'), max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(_('review count'), default=0)
    
    # Status and visibility
    is_active = models.BooleanField(_('active'), default=True)
    featured = models.BooleanField(_('featured'), default=False)
    
    # SEO
    meta_title = models.CharField(_('meta title'), max_length=100, blank=True)
    meta_description = models.CharField(_('meta description'), max_length=200, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('destination')
        verbose_name_plural = _('destinations')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('destinations:destination_detail', kwargs={'slug': self.slug})

class DestinationImage(models.Model):
    """
    Additional images for a destination.
    """
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='images',
                                   verbose_name=_('destination'))
    image = models.ImageField(_('image'), upload_to='destinations/')
    title = models.CharField(_('title'), max_length=100, blank=True)
    is_featured = models.BooleanField(_('featured'), default=False)
    alt_text = models.CharField(_('alternative text'), max_length=100, blank=True)
    
    # Ordering
    order = models.PositiveIntegerField(_('order'), default=0)
    
    class Meta:
        verbose_name = _('destination image')
        verbose_name_plural = _('destination images')
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.destination.name}"