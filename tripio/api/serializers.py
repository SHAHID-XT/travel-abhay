from rest_framework import serializers
from django.contrib.auth import get_user_model
from packages.models import Package, Availability, Itinerary, PackageImage
from destinations.models import Destination, Region, TravelInterest, DestinationImage
from bookings.models import Booking, Traveler, Payment
from reviews.models import Review, ReviewImage

User = get_user_model()

class TravelInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelInterest
        fields = ['id', 'name', 'icon']

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name', 'slug', 'code', 'parent', 'description', 'image', 'is_active', 'featured']

class DestinationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationImage
        fields = ['id', 'image', 'title', 'is_featured', 'alt_text', 'order']

class DestinationSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    region_id = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(),
        source='region',
        write_only=True
    )
    interests = TravelInterestSerializer(many=True, read_only=True)
    interest_ids = serializers.PrimaryKeyRelatedField(
        queryset=TravelInterest.objects.all(),
        source='interests',
        write_only=True,
        many=True
    )
    images = DestinationImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Destination
        fields = [
            'id', 'name', 'slug', 'region', 'region_id', 'description', 'short_description',
            'location', 'address', 'main_image', 'interests', 'interest_ids', 'images',
            'average_rating', 'review_count', 'is_active', 'featured',
            'meta_title', 'meta_description', 'created_at', 'updated_at'
        ]

class ItinerarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Itinerary
        fields = ['id', 'day', 'title', 'description', 'accommodation', 'meals_included']

class PackageImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageImage
        fields = ['id', 'image', 'title', 'is_featured', 'alt_text', 'order']

class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = [
            'id', 'package', 'start_date', 'end_date',
            'available_slots', 'is_available', 'special_price'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """
        Check that start_date is before end_date.
        """
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date.")
        return data

class PackageSerializer(serializers.ModelSerializer):
    seller = serializers.StringRelatedField(read_only=True)
    destinations = DestinationSerializer(many=True, read_only=True)
    destination_ids = serializers.PrimaryKeyRelatedField(
        queryset=Destination.objects.all(),
        source='destinations',
        write_only=True,
        many=True
    )
    itinerary_days = ItinerarySerializer(many=True, read_only=True)
    images = PackageImageSerializer(many=True, read_only=True)
    availabilities = AvailabilitySerializer(many=True, read_only=True)
    
    class Meta:
        model = Package
        fields = [
            'id', 'title', 'slug', 'seller', 'description', 'short_description',
            'destinations', 'destination_ids', 'duration_days', 'max_travelers',
            'transportation_type', 'difficulty_level', 'base_price', 'discount_price',
            'currency', 'what_is_included', 'what_is_excluded', 'main_image',
            'is_active', 'featured', 'average_rating', 'review_count',
            'created_at', 'updated_at', 'itinerary_days', 'images', 'availabilities'
        ]
        read_only_fields = ['id', 'slug', 'average_rating', 'review_count', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'phone_number',
            'role', 'profile_image', 'bio', 'date_joined', 'last_active',
            'country', 'city', 'company_name', 'website'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'last_active']

class TravelerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Traveler
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'gender', 'passport_number', 'passport_expiry', 'nationality'
        ]

class BookingSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    package = PackageSerializer(read_only=True)
    package_id = serializers.PrimaryKeyRelatedField(
        queryset=Package.objects.all(),
        source='package',
        write_only=True
    )
    availability = AvailabilitySerializer(read_only=True)
    availability_id = serializers.PrimaryKeyRelatedField(
        queryset=Availability.objects.all(),
        source='availability',
        write_only=True
    )
    travelers = TravelerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'reference_id', 'user', 'package', 'package_id',
            'availability', 'availability_id', 'status', 'num_travelers',
            'contact_name', 'contact_email', 'contact_phone', 'special_requirements',
            'unit_price', 'total_price', 'currency', 'created_at', 'updated_at',
            'paid_at', 'cancelled_at', 'cancellation_reason', 'travelers'
        ]
        read_only_fields = [
            'id', 'reference_id', 'user', 'unit_price', 'total_price',
            'currency', 'created_at', 'updated_at', 'paid_at', 'cancelled_at'
        ]

class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'caption', 'order']

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    package = PackageSerializer(read_only=True)
    package_id = serializers.PrimaryKeyRelatedField(
        queryset=Package.objects.all(),
        source='package',
        write_only=True
    )
    booking = serializers.StringRelatedField(read_only=True)
    booking_id = serializers.PrimaryKeyRelatedField(
        queryset=Booking.objects.all(),
        source='booking',
        write_only=True,
        required=False
    )
    images = ReviewImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'package', 'package_id', 'booking', 'booking_id',
            'rating', 'title', 'content', 'has_images', 'is_published',
            'created_at', 'updated_at', 'images'
        ]
        read_only_fields = ['id', 'user', 'has_images', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Check that the user has booked the package or is an admin.
        """
        user = self.context['request'].user
        package = data.get('package')
        
        # Admins can review any package
        if user.is_admin():
            return data
        
        # Check if user has booked this package
        has_booking = Booking.objects.filter(
            user=user,
            package=package,
            status__in=[Booking.STATUS_COMPLETED, Booking.STATUS_PAID]
        ).exists()
        
        if not has_booking:
            raise serializers.ValidationError(
                "You can only review packages that you have booked and completed."
            )
        
        return data