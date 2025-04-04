from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from packages.models import Package
from bookings.models import Booking

class Review(models.Model):
    """
    Review for a package by a user who has booked it.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                            related_name='reviews', verbose_name=_('user'))
    package = models.ForeignKey(Package, on_delete=models.CASCADE, 
                              related_name='reviews', verbose_name=_('package'))
    booking = models.OneToOneField(Booking, on_delete=models.SET_NULL, 
                                 null=True, blank=True, related_name='review', 
                                 verbose_name=_('booking'))
    
    # Review content
    rating = models.PositiveSmallIntegerField(_('rating'), 
                                            validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(_('title'), max_length=100)
    content = models.TextField(_('content'))
    
    # Images (optional)
    has_images = models.BooleanField(_('has images'), default=False)
    
    # Status
    is_published = models.BooleanField(_('published'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        ordering = ['-created_at']
        # Ensure a user can only review a specific package once
        unique_together = ('user', 'package')
    
    def __str__(self):
        return f"Review by {self.user.username} for {self.package.title}"
    
    def save(self, *args, **kwargs):
        # Update the has_images field based on whether there are any related images
        if self.pk:
            self.has_images = self.images.exists()
        super().save(*args, **kwargs)
        
        # Update package rating statistics
        self.update_package_ratings()
    
    def update_package_ratings(self):
        """
        Update the average rating and review count for the associated package.
        """
        package = self.package
        reviews = package.reviews.filter(is_published=True)
        count = reviews.count()
        
        if count > 0:
            avg = sum(r.rating for r in reviews) / count
            package.average_rating = round(avg, 2)
        else:
            package.average_rating = 0
            
        package.review_count = count
        package.save(update_fields=['average_rating', 'review_count'])

class ReviewImage(models.Model):
    """
    Images attached to a review.
    """
    review = models.ForeignKey(Review, on_delete=models.CASCADE, 
                              related_name='images', verbose_name=_('review'))
    image = models.ImageField(_('image'), upload_to='reviews/')
    caption = models.CharField(_('caption'), max_length=100, blank=True)
    
    # Ordering
    order = models.PositiveIntegerField(_('order'), default=0)
    
    class Meta:
        verbose_name = _('review image')
        verbose_name_plural = _('review images')
        ordering = ['order']
    
    def __str__(self):
        return f"Image for review #{self.review.id}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the has_images field on the related review
        self.review.has_images = True
        self.review.save(update_fields=['has_images'])