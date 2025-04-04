from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from datetime import timedelta
from analytics.models import SellerStats
from packages.models import Package, Availability
from bookings.models import Booking
from reviews.models import Review
from chat.models import Conversation, Message

# Buyer dashboard views
@login_required
def buyer_dashboard(request):
    """
    Dashboard for buyers showing their bookings, reviews, and saved packages.
    """
    # Get recent bookings
    recent_bookings = Booking.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get upcoming trips
    now = timezone.now().date()
    upcoming_trips = Booking.objects.filter(
        user=request.user,
        availability__start_date__gte=now,
        status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PAID]
    ).order_by('availability__start_date')[:5]
    
    # Get reviews left by user
    reviews = Review.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get unread messages
    unread_messages_count = Message.objects.filter(
    conversation__in=Conversation.objects.filter(
        Q(initiator=request.user) | Q(receiver=request.user)
    ),
    is_read=False
).exclude(sender=request.user).count()
    
    context = {
        'recent_bookings': recent_bookings,
        'upcoming_trips': upcoming_trips,
        'reviews': reviews,
        'unread_messages_count': unread_messages_count,
    }
    
    return render(request, 'dashboard/buyer/dashboard.html', context)

class BuyerBookingListView(LoginRequiredMixin, ListView):
    """
    Display all bookings for a buyer.
    """
    model = Booking
    template_name = 'dashboard/buyer/bookings.html'
    context_object_name = 'bookings'
    paginate_by = 10
    
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_bookings'] = self.get_queryset().filter(
            status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PAID]
        ).count()
        return context

class BuyerBookingDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Display detailed information about a booking.
    """
    model = Booking
    template_name = 'dashboard/buyer/booking_detail.html'
    context_object_name = 'booking'
    
    def test_func(self):
        booking = self.get_object()
        return booking.user == self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the package and itinerary information
        booking = self.get_object()
        context['package'] = booking.package
        context['itinerary'] = booking.package.itinerary_days.all().order_by('day')
        
        # Check if there's a review for this booking
        try:
            context['review'] = Review.objects.get(booking=booking)
        except Review.DoesNotExist:
            context['review'] = None
        
        return context

# Seller dashboard views
class SellerRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure a user is a seller.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_seller()

@login_required
def seller_dashboard(request):
    """
    Dashboard for sellers showing their packages, bookings, and stats.
    """
    # Only allow sellers to access this dashboard
    if not request.user.is_seller():
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    # Get recent bookings for seller's packages
    recent_bookings = Booking.objects.filter(
        package__seller=request.user
    ).order_by('-created_at')[:5]
    
    # Get package statistics
    packages = Package.objects.filter(seller=request.user)
    package_count = packages.count()
    active_package_count = packages.filter(is_active=True).count()
    
    # Get booking statistics
    now = timezone.now().date()
    bookings = Booking.objects.filter(package__seller=request.user)
    upcoming_bookings_count = bookings.filter(
        availability__start_date__gte=now,
        status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PAID]
    ).count()
    
    # Get earnings for current month
    first_day_of_month = now.replace(day=1)
    earnings_this_month = bookings.filter(
        status=Booking.STATUS_PAID,
        paid_at__gte=first_day_of_month
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # Get unread messages
    unread_messages_count = Message.objects.filter(
    conversation__in=Conversation.objects.filter(
        Q(initiator=request.user) | Q(receiver=request.user)
    ),
    is_read=False
).exclude(sender=request.user).count()
    
    # Get seller stats for the last 30 days
    thirty_days_ago = now - timedelta(days=30)
    stats = SellerStats.objects.filter(
        seller=request.user,
        date__gte=thirty_days_ago
    ).order_by('date')
    
    # Prepare chart data
    dates = [stat.date.strftime('%Y-%m-%d') for stat in stats]
    views = [stat.package_views for stat in stats]
    bookings_data = [stat.package_bookings for stat in stats]
    sales = [float(stat.total_sales) for stat in stats]
    
    chart_data = {
        'dates': dates,
        'views': views,
        'bookings': bookings_data,
        'sales': sales,
    }
    
    context = {
        'recent_bookings': recent_bookings,
        'package_count': package_count,
        'active_package_count': active_package_count,
        'upcoming_bookings_count': upcoming_bookings_count,
        'earnings_this_month': earnings_this_month,
        'unread_messages_count': unread_messages_count,
        'chart_data': chart_data,
    }
    
    return render(request, 'dashboard/seller/dashboard.html', context)

class SellerPackageListView(LoginRequiredMixin, SellerRequiredMixin, ListView):
    """
    Display all packages for a seller.
    """
    model = Package
    template_name = 'dashboard/seller/packages.html'
    context_object_name = 'packages'
    paginate_by = 10
    
    def get_queryset(self):
        return Package.objects.filter(seller=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_packages'] = self.get_queryset().filter(is_active=True).count()
        return context

class SellerPackageCreateView(LoginRequiredMixin, SellerRequiredMixin, CreateView):
    """
    Create a new package.
    """
    model = Package
    template_name = 'dashboard/seller/package_form.html'
    fields = [
        'title', 'description', 'short_description', 'destinations',
        'duration_days', 'max_travelers', 'transportation_type',
        'difficulty_level', 'base_price', 'discount_price', 'currency',
        'what_is_included', 'what_is_excluded', 'main_image',
    ]
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        # Generate a slug from the title
        from django.utils.text import slugify
        form.instance.slug = slugify(form.instance.title)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('dashboard:seller_package_detail', kwargs={'pk': self.object.pk})

class SellerPackageUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update an existing package.
    """
    model = Package
    template_name = 'dashboard/seller/package_form.html'
    fields = [
        'title', 'description', 'short_description', 'destinations',
        'duration_days', 'max_travelers', 'transportation_type',
        'difficulty_level', 'base_price', 'discount_price', 'currency',
        'what_is_included', 'what_is_excluded', 'main_image',
        'is_active', 'featured',
    ]
    
    def test_func(self):
        package = self.get_object()
        return package.seller == self.request.user
    
    def get_success_url(self):
        return reverse('dashboard:seller_package_detail', kwargs={'pk': self.object.pk})

# Admin dashboard views
class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure a user is an admin.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()

@login_required
def admin_dashboard(request):
    """
    Dashboard for admins showing platform statistics.
    """
    # Only allow admins to access this dashboard
    if not request.user.is_admin():
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    # Get platform statistics
    user_count = User.objects.count()
    seller_count = User.objects.filter(role=User.ROLE_SELLER).count()
    buyer_count = User.objects.filter(role=User.ROLE_BUYER).count()
    
    package_count = Package.objects.count()
    active_package_count = Package.objects.filter(is_active=True).count()
    
    booking_count = Booking.objects.count()
    
    # Get earnings for current month
    now = timezone.now().date()
    first_day_of_month = now.replace(day=1)
    earnings_this_month = Booking.objects.filter(
        status=Booking.STATUS_PAID,
        paid_at__gte=first_day_of_month
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # Get recent bookings
    recent_bookings = Booking.objects.order_by('-created_at')[:10]
    
    # Get user signup statistics for the last 30 days
    thirty_days_ago = now - timedelta(days=30)
    new_users = User.objects.filter(date_joined__gte=thirty_days_ago).order_by('date_joined')
    
    # Group by day
    from django.db.models.functions import TruncDay
    new_users_by_day = new_users.annotate(
        day=TruncDay('date_joined')
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Prepare chart data
    days = [user['day'].strftime('%Y-%m-%d') for user in new_users_by_day]
    counts = [user['count'] for user in new_users_by_day]
    
    user_chart_data = {
        'days': days,
        'counts': counts,
    }
    
    context = {
        'user_count': user_count,
        'seller_count': seller_count,
        'buyer_count': buyer_count,
        'package_count': package_count,
        'active_package_count': active_package_count,
        'booking_count': booking_count,
        'earnings_this_month': earnings_this_month,
        'recent_bookings': recent_bookings,
        'user_chart_data': user_chart_data,
    }
    
    return render(request, 'dashboard/admin/dashboard.html', context)