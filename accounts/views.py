from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count
from .models import UserProfile, Role, AuditLog
from inventory.models import Notification
from .forms import LoginForm, CustomUserCreationForm, UserForm, UserProfileForm, RoleForm, SystemSettingsForm, PasswordResetRequestForm, ChangePasswordForm


def log_action(request, action, **kwargs):
    if request.user.is_authenticated:
        AuditLog.objects.create(
            user=request.user,
            action=action,
            ip_address=request.META.get("REMOTE_ADDR"),
            **kwargs,
        )


def homepage(request):
    if request.user.is_authenticated:
        if hasattr(request.user, "profile") and request.user.profile.role:
            role_name = request.user.profile.role.name
            if role_name == "Admin":
                return redirect("admin_dashboard")
            if role_name == "Manager":
                return redirect("dashboard")
            return redirect("customer_dashboard")
        return redirect("dashboard")
    return redirect("accounts:login")


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            log_action(request, "login")
            if hasattr(user, "profile"):
                up = user.profile
                up.last_login_ip = request.META.get("REMOTE_ADDR")
                up.save(update_fields=["last_login_ip"])
            role_name = getattr(user.profile.role, "name", "")
            if role_name == "Admin":
                return redirect("admin_dashboard")
            if role_name == "Manager":
                return redirect("dashboard")
            return redirect("customer_dashboard")
    else:
        form = LoginForm(request)
    return render(request, "accounts/login.html", {"form": form})


def signup_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Role.objects.get_or_create(name="Customer", defaults={"description": "Retail store customer"})
            customer_role, _ = Role.objects.get_or_create(name="Customer")
            user.profile.role = customer_role
            user.profile.save(update_fields=["role"])
            messages.success(request, "Account created! Please log in.")
            return redirect("accounts:login")
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})


def logout_view(request):
    log_action(request, "logout")
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


@login_required
def profile_view(request):
    user = request.user
    return render(request, "accounts/profile.html", {
        "user": user,
        "user_form": UserForm(instance=user, prefix="u"),
        "profile_form": UserProfileForm(instance=user.profile, prefix="p"),
    })


@login_required
def profile_edit_view(request):
    user = request.user
    if request.method == "POST":
        user_form    = UserForm(request.POST, instance=user, prefix="u")
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user.profile, prefix="p")
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        user_form    = UserForm(instance=user, prefix="u")
        profile_form = UserProfileForm(instance=user.profile, prefix="p")
    return render(request, "accounts/profile_edit.html", {
        "user_form": user_form, "profile_form": profile_form,
    })


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            current  = form.cleaned_data["current_password"]
            new_pass = form.cleaned_data["new_password1"]
            if not request.user.check_password(current):
                messages.error(request, "Current password is incorrect.")
            else:
                request.user.set_password(new_pass)
                request.user.save()
                update_session_auth_hash(request, request.user)
                log_action(request, "update", model_name="User", object_id=str(request.user.pk))
                messages.success(request, "Password changed successfully.")
                return redirect("profile")
    else:
        form = ChangePasswordForm()
    return render(request, "accounts/change_password.html", {"form": form})


@login_required
def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            users = User.objects.filter(email=email)
            if users.exists():
                user = users.first()
                token = default_token_generator.make_token(user)
                uid   = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = request.build_absolute_uri(f'/reset/{uid}/{token}/')
                try:
                    send_mail(
                        "Password Reset — StockPro",
                        f"Click to reset your password: {reset_url}",
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=True,
                    )
                except Exception:
                    pass
            messages.success(request, "If an account exists with this email, a reset link has been sent.")
            return redirect("accounts:login")
    else:
        form = PasswordResetRequestForm()
    return render(request, "accounts/password_reset.html", {"form": form})


@login_required
def customer_dashboard(request):
    products = Product.objects.filter(status="active").order_by("-quantity")
    return render(request, "accounts/customer_dashboard.html", {"products": products})


# Staff who don't yet have a role — safe redirect
@login_required
def homepage(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_dashboard")
        if request.user.is_staff:
            return redirect("dashboard")
        return redirect("customer_dashboard")
    return redirect("accounts:login")
