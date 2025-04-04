from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.core.paginator import Paginator
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from destinations.models import Destination, Region
from packages.models import Package
from reviews.models import Review
from .forms import ContactForm, NewsletterForm
from .models import NewsletterSubscription, Contact
from analytics.models import UserActivity, SearchTerm

def home(request):
    """
    Home page view with featured destinations and packages.
    """
    # Track user activity for analytics
    if not request.session.session_key:
        request.session.save()
    
    # Get featured destinations
    featured_destinations = Destination.objects.filter(
        is_active=True, 
        featured=True
    ).order_by('-average_rating')[:6]
    
    # Get popular packages
    popular_packages = Package.objects.filter(
        is_active=True
    ).order_by('-review_count', '-average_rating')[:6]
    
    # Get featured reviews
    featured_reviews = Review.objects.filter(
        is_published=True, 
        rating__gte=4
    ).select_related('user', 'package').order_by('-created_at')[:6]
    
    # Get regions for the search form
    regions = Region.objects.filter(is_active=True, parent__isnull=True)
    
    # Record user activity
    UserActivity.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_id=request.session.session_key,
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        action='view_homepage',
        page='home'
    )
    
    context = {
        'featured_destinations': featured_destinations,
        'popular_packages': popular_packages,
        'featured_reviews': featured_reviews,
        'regions': regions,
    }
    
    return render(request, 'home.html', context)

def about(request):
    """
    About page with company information.
    """
    return render(request, 'core/about.html')

def contact(request):
    """
    Contact page with contact form.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            messages.success(request, _('Your message has been sent successfully. We will contact you soon.'))
            return redirect('core:contact')
    else:
        form = ContactForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'core/contact.html', context)

def faq(request):
    """
    Frequently Asked Questions page.
    """
    return render(request, 'core/faq.html')

def terms(request):
    """
    Terms and Conditions page.
    """
    return render(request, 'core/terms.html')

def privacy(request):
    """
    Privacy Policy page.
    """
    return render(request, 'core/privacy.html')

def cookies(request):
    """
    Cookie Policy page.
    """
    return render(request, 'core/cookies.html')

def blog(request):
    """
    Blog listing page.
    """
    # Get blog posts (assuming you have a Blog model)
    # blog_posts = Blog.objects.filter(is_published=True).order_by('-published_at')
    
    # For demo, we'll use a placeholder
    blog_posts = []
    
    # Pagination
    paginator = Paginator(blog_posts, 9)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    context = {
        'posts': posts
    }
    
    return render(request, 'core/blog.html', context)

def blog_post(request, slug):
    """
    Individual blog post page.
    """
    # Get the blog post (assuming you have a Blog model)
    # post = get_object_or_404(Blog, slug=slug, is_published=True)
    
    # For demo, we'll use a placeholder
    post = None
    
    context = {
        'post': post
    }
    
    return render(request, 'core/blog_post.html', context)

@require_POST
def newsletter_subscribe(request):
    """
    Handle newsletter subscription.
    """
    form = NewsletterForm(request.POST)
    
    if form.is_valid():
        email = form.cleaned_data['email']
        consent = form.cleaned_data['consent']
        
        # Don't create duplicate subscriptions
        if not NewsletterSubscription.objects.filter(email=email).exists():
            NewsletterSubscription.objects.create(
                email=email,
                consent=consent,
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            messages.success(request, _('Thank you for subscribing to our newsletter!'))
        else:
            messages.info(request, _('You are already subscribed to our newsletter.'))
    else:
        messages.error(request, _('Please provide a valid email address.'))
    
    # Redirect back to the referring page
    referer = request.META.get('HTTP_REFERER', 'core:home')
    return redirect(referer)

def set_language(request):
    """
    Set the language preference in the session and redirect back.
    """
    response = set_language(request)
    
    # Update user's profile if they're logged in
    if request.user.is_authenticated and request.method == 'POST':
        language = request.POST.get('language')
        if language:
            profile = request.user.profile
            profile.preferred_language = language
            profile.save(update_fields=['preferred_language'])
    
    return response

@csrf_exempt
def track_search(request):
    """
    Track search terms for analytics.
    """
    if request.method == 'POST' and request.is_ajax():
        term = request.POST.get('term', '').strip()
        
        if term:
            # Check if this term already exists
            try:
                search_term = SearchTerm.objects.get(term__iexact=term)
                search_term.count += 1
                search_term.save(update_fields=['count', 'last_searched'])
            except SearchTerm.DoesNotExist:
                # Create a new search term
                SearchTerm.objects.create(term=term)
            
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

def handler404(request, exception=None):
    """
    Custom 404 error handler.
    """
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """
    Custom 500 error handler.
    """
    return render(request, 'errors/500.html', status=500)