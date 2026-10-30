import re

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Avg, Sum 
from django.shortcuts import (
    redirect,
    render,
    get_object_or_404,
)

from marketplace.models import Product, Review
from .models import (
    Profile,
    FarmerFollow,
)


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email')
        if username is None:
            return None

        user = None
        if '@' in username:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                user = None
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = None

        if user is not None and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None


def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', '').strip() or 'buyer'
        valid_roles = ["buyer", "farmer", "ngo"]
        if role not in valid_roles: role = "buyer"
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        organization = request.POST.get('organization', '').strip()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '').strip()
        bio = request.POST.get('bio', '').strip()
        province = request.POST.get('province', '').strip()
        district = request.POST.get('district', '').strip()
        sector = request.POST.get('sector', '').strip()
        cell = request.POST.get('cell', '').strip()
        village = request.POST.get('village', '').strip()

        if not email or not password1 or not password2:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'accounts/register.html', {'role': role})

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html', {'role': role})
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, "accounts/register.html", {"role": role})

        base_username = email.split('@')[0]
        username = re.sub(r'[^0-9A-Za-z_.-]+', '', base_username) or 'user'
        candidate = username
        counter = 1
        while User.objects.filter(username=candidate).exists():
            candidate = f'{username}{counter}'
            counter += 1

        user = User.objects.create_user(username=candidate, email=email, password=password1)
        user.first_name = first_name
        user.last_name = last_name
        user.save(update_fields=['first_name', 'last_name'])
        user.backend = 'accounts.views.EmailBackend'
        profile = user.profile
        profile.role = role
        profile.phone = phone
        profile.organization = organization
        profile.gender = gender
        profile.bio = bio
        profile.province = province
        profile.district = district
        profile.sector = sector
        profile.cell = cell
        profile.village = village
        profile.save()
        login(request, user)
        messages.success(request, 'Registration successful.')
        return redirect('marketplace:dashboard')

    return render(request, 'accounts/register.html', {'role': 'buyer'})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            user.backend = 'accounts.views.EmailBackend'
            login(request, user)
            return redirect('marketplace:dashboard')
        messages.error(request, 'Invalid email or password.')
    return render(request, 'accounts/login.html', {'form': None})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')

def farmer_store(request, slug):
    profile = get_object_or_404(
        Profile,
        store_slug=slug,
    )
    
    farmer = profile.user
    products = (
        Product.objects
        .filter(
            farmer=farmer,
            availability_status="available",
        )

        .order_by("-created_at")
    )

    stats = products.aggregate(
        total_views=Sum("views"),
    )
    
    average_rating = (
        Review.objects
        .filter(
            product__farmer=farmer,
            is_approved=True,
        )
        .aggregate(
        Avg("rating")
        )
        .get("rating__avg")
    )

    is_following = False

    if request.user.is_authenticated:

        is_following = FarmerFollow.objects.filter(
            follower=request.user,
            farmer=farmer,
        ).exists()

    followers_count = FarmerFollow.objects.filter(
        farmer=farmer,
    ).count()

    following_count = FarmerFollow.objects.filter(
        follower=farmer,
    ).count()

    is_following = False

    if request.user.is_authenticated:

        is_following = FarmerFollow.objects.filter(
            follower=request.user,
        farmer=farmer,
        ).exists()

    context = {
        "profile": profile,
        "farmer": farmer,
        "products": products,
        "product_count": products.count(),
        "average_rating": round(
            average_rating or 0,
            1
        ),
        "total_views": stats["total_views"] or 0,
        "is_following": is_following,
        "followers_count": followers_count,
        "following_count": following_count,
        "is_following": is_following,
    }

    return render(
        request,
            "accounts/farmer_store.html",
            context,
    )

from django.contrib.auth.decorators import login_required

@login_required
def toggle_follow(request, slug):

    profile = get_object_or_404(
        Profile,
        store_slug=slug,
    )

    farmer = profile.user

    if farmer == request.user:

        messages.error(
            request,
            "You cannot follow yourself."
        )

        return redirect(
            "accounts:farmer_store",
            slug=slug,
        )

    follow = FarmerFollow.objects.filter(
        follower=request.user,
        farmer=farmer,
    ).first()

    if follow:

        follow.delete()

        messages.success(
            request,
            "Farmer unfollowed."
        )

    else:

        FarmerFollow.objects.create(
            follower=request.user,
            farmer=farmer,
        )

        messages.success(
            request,
            "Farmer followed successfully."
        )

    return redirect(
        "accounts:farmer_store",
        slug=slug,
    )


@login_required
def following_list(request):

    following = (
        FarmerFollow.objects
        .filter(
            follower=request.user
        )
        .select_related(
            "farmer",
            "farmer__profile"
        )
    )

    return render(
        request,
        "accounts/following_list.html",
        {
            "following": following,
        },
    )