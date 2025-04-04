from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from packages.models import Package, Availability
import uuid

class Booking(models.Model):
    """
    A booking made by a user for a specific package.
    """
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PAID = 'paid'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_REFUNDED = 'refunded'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, _('Pending')),
        (STATUS_CONFIRMED, _('Confirmed')),
        (STATUS_PAID, _('Paid')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_CANCELLED, _('Cancelled')),
        (STATUS_REFUNDED, _('Refunded')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_id = models.CharField(_('reference ID'), max_length=15, unique=True, editable=False)
    
    # Relationships
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, 
                            related_name='bookings', verbose_name=_('user'))
    package = models.ForeignKey(Package, on_delete=models.PROTECT, 
                              related_name='bookings', verbose_name=_('package'))
    availability = models.ForeignKey(Availability, on_delete=models.PROTECT, 
                                    related_name='bookings', verbose_name=_('availability'))
    
    # Booking details
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    num_travelers = models.PositiveIntegerField(_('number of travelers'), default=1)
    
    # Traveler information
    contact_name = models.CharField(_('contact name'), max_length=100)
    contact_email = models.EmailField(_('contact email'))
    contact_phone = models.CharField(_('contact phone'), max_length=20)
    special_requirements = models.TextField(_('special requirements'), blank=True)
    
    # Price information
    unit_price = models.DecimalField(_('unit price'), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_('total price'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    paid_at = models.DateTimeField(_('paid at'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('cancelled at'), null=True, blank=True)
    
    # If cancelled, store reason
    cancellation_reason = models.TextField(_('cancellation reason'), blank=True)
    
    class Meta:
        verbose_name = _('booking')
        verbose_name_plural = _('bookings')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reference_id} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.reference_id:
            # Generate a unique reference ID
            import random
            import string
            prefix = 'BK'
            random_str = ''.join(random.choices(string.digits, k=8))
            self.reference_id = f"{prefix}{random_str}"
        
        # Calculate total price
        self.total_price = self.unit_price * self.num_travelers
        
        super().save(*args, **kwargs)

class Traveler(models.Model):
    """
    Information about each traveler in a booking.
    """
    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
    )
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, 
                               related_name='travelers', verbose_name=_('booking'))
    first_name = models.CharField(_('first name'), max_length=50)
    last_name = models.CharField(_('last name'), max_length=50)
    email = models.EmailField(_('email'), blank=True)
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    date_of_birth = models.DateField(_('date of birth'))
    gender = models.CharField(_('gender'), max_length=1, choices=GENDER_CHOICES)
    passport_number = models.CharField(_('passport number'), max_length=50, blank=True)
    passport_expiry = models.DateField(_('passport expiry'), null=True, blank=True)
    nationality = models.CharField(_('nationality'), max_length=50, blank=True)
    
    class Meta:
        verbose_name = _('traveler')
        verbose_name_plural = _('travelers')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Payment(models.Model):
    """
    Payment details for a booking.
    """
    PAYMENT_STATUS_PENDING = 'pending'
    PAYMENT_STATUS_COMPLETED = 'completed'
    PAYMENT_STATUS_FAILED = 'failed'
    PAYMENT_STATUS_REFUNDED = 'refunded'
    
    PAYMENT_STATUS_CHOICES = (
        (PAYMENT_STATUS_PENDING, _('Pending')),
        (PAYMENT_STATUS_COMPLETED, _('Completed')),
        (PAYMENT_STATUS_FAILED, _('Failed')),
        (PAYMENT_STATUS_REFUNDED, _('Refunded')),
    )
    
    PAYMENT_METHOD_CREDIT_CARD = 'credit_card'
    PAYMENT_METHOD_PAYPAL = 'paypal'
    PAYMENT_METHOD_BANK_TRANSFER = 'bank_transfer'
    PAYMENT_METHOD_CRYPTO = 'crypto'
    
    PAYMENT_METHOD_CHOICES = (
        (PAYMENT_METHOD_CREDIT_CARD, _('Credit Card')),
        (PAYMENT_METHOD_PAYPAL, _('PayPal')),
        (PAYMENT_METHOD_BANK_TRANSFER, _('Bank Transfer')),
        (PAYMENT_METHOD_CRYPTO, _('Cryptocurrency')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, 
                              related_name='payments', verbose_name=_('booking'))
    
    # Payment information
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    payment_method = models.CharField(_('payment method'), max_length=20, 
                                     choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(_('payment status'), max_length=20, 
                                     choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING)
    
    # Transaction details
    transaction_id = models.CharField(_('transaction ID'), max_length=100, blank=True)
    payment_gateway_response = models.JSONField(_('payment gateway response'), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} for Booking {self.booking.reference_id}"