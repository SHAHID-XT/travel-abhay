from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import (
    UserSerializer, PackageSerializer, DestinationSerializer,
    BookingSerializer, ReviewSerializer, AvailabilitySerializer
)
from accounts.models import User
from packages.models import Package, Availability
from destinations.models import Destination, Region
from bookings.models import Booking
from reviews.models import Review
from .permissions import IsOwnerOrReadOnly, IsSellerOrReadOnly

class IsAdminUser(permissions.BasePermission):
    """
    Permission to only allow admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_admin()

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users.
    Admin users can view and edit all users.
    Regular users can only view and edit their own profile.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    def get_permissions(self):
        if self.action in ['list', 'create', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]

class PackageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for packages.
    Anyone can view active packages.
    Sellers can create and edit their own packages.
    Admins can view and edit all packages.
    """
    serializer_class = PackageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'destinations', 'duration_days', 'transportation_type', 
        'difficulty_level', 'is_active', 'featured'
    ]
    search_fields = ['title', 'description', 'short_description']
    ordering_fields = [
        'created_at', 'updated_at', 'base_price', 
        'discount_price', 'average_rating', 'review_count'
    ]
    
    def get_queryset(self):
        user = self.request.user
        
        # Determine the base queryset
        if user.is_authenticated:
            if user.is_admin():
                # Admin can see all packages
                queryset = Package.objects.all()
            elif user.is_seller():
                # Sellers can see their own packages (active or not) and other sellers' active packages
                queryset = Package.objects.filter(
                    Q(seller=user) | Q(is_active=True)
                )
            else:
                # Buyers can only see active packages
                queryset = Package.objects.filter(is_active=True)
        else:
            # Anonymous users can only see active packages
            queryset = Package.objects.filter(is_active=True)
        
        return queryset
    
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated, IsSellerOrReadOnly]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_featured(self, request, pk=None):
        """
        Toggle the featured status of a package.
        Only admins can use this endpoint.
        """
        package = self.get_object()
        
        if not request.user.is_admin():
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        package.featured = not package.featured
        package.save()
        
        return Response(
            {"status": "success", "featured": package.featured},
            status=status.HTTP_200_OK
        )

class DestinationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for destinations.
    Anyone can view destinations.
    Only admins can create, update, and delete destinations.
    """
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['region', 'interests', 'is_active', 'featured']
    search_fields = ['name', 'description', 'short_description']
    ordering_fields = ['name', 'created_at', 'updated_at', 'average_rating', 'review_count']
    
    def get_queryset(self):
        queryset = Destination.objects.all()
        
        # Filter by active status for non-admin users
        if not (self.request.user.is_authenticated and self.request.user.is_admin()):
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

class BookingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for bookings.
    Buyers can view and create their own bookings.
    Sellers can view bookings for their packages.
    Admins can view all bookings.
    """
    serializer_class = BookingSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'package']
    ordering_fields = ['created_at', 'updated_at', 'paid_at']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin():
            # Admin can see all bookings
            return Booking.objects.all()
        elif user.is_seller():
            # Sellers can see bookings for their packages
            return Booking.objects.filter(package__seller=user)
        else:
            # Buyers can see their own bookings
            return Booking.objects.filter(user=user)
    
    def perform_create(self, serializer):
        # Set the user to the current authenticated user
        serializer.save(user=self.request.user)

class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for reviews.
    Anyone can view reviews.
    Only the user who created the review can update or delete it.
    """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['package', 'user', 'rating']
    ordering_fields = ['created_at', 'updated_at', 'rating']
    
    def get_queryset(self):
        queryset = Review.objects.filter(is_published=True)
        
        # Admin can see unpublished reviews as well
        if self.request.user.is_authenticated and self.request.user.is_admin():
            queryset = Review.objects.all()
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AvailabilityViewSet(viewsets.ModelViewSet):
    """
    API endpoint for package availabilities.
    Anyone can view availabilities.
    Only the seller who owns the package can create, update, or delete availabilities.
    """
    serializer_class = AvailabilitySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['package', 'start_date', 'end_date', 'is_available']
    ordering_fields = ['start_date', 'end_date']
    
    def get_queryset(self):
        # Filter by date range if provided
        queryset = Availability.objects.all()
        start = self.request.query_params.get('start', None)
        end = self.request.query_params.get('end', None)
        
        if start:
            queryset = queryset.filter(start_date__gte=start)
        if end:
            queryset = queryset.filter(end_date__lte=end)
        
        # Show only available dates for non-admin users
        if not (self.request.user.is_authenticated and self.request.user.is_admin()):
            now = timezone.now().date()
            queryset = queryset.filter(
                end_date__gte=now,
                is_available=True,
                package__is_active=True
            )
        
        return queryset
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsSellerOrReadOnly]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        # Verify that the user is the seller of the package
        package_id = self.request.data.get('package')
        package = Package.objects.get(id=package_id)
        
        if package.seller != self.request.user and not self.request.user.is_admin():
            raise permissions.PermissionDenied(
                "You can only create availabilities for your own packages."
            )
        
        serializer.save()