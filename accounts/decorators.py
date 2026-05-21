from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(role_names):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect("accounts:login")
            if not hasattr(request.user, "profile") or not request.user.profile.role:
                messages.error(request, "Your account does not have an assigned role. Contact an administrator.")
                return redirect("accounts:login")
            user_role = request.user.profile.role.name
            if isinstance(role_names, (list, tuple)):
                if user_role not in role_names:
                    messages.error(request, f"Access denied. Required roles: {', '.join(role_names)}")
                    return redirect("dashboard")
            else:
                if user_role != role_names:
                    messages.error(request, f"Access denied. Required role: {role_names}")
                    return redirect("dashboard")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def admin_required(view_func=None, role_names=("Admin",)):
    if view_func:
        return role_required(role_names)(view_func)
    return role_required(role_names)


def manager_required(view_func):
    return role_required("Manager")(view_func)


def manager_or_admin_required(view_func):
    return role_required(["Manager", "Admin"])(view_func)


def has_role(user, role_name):
    if hasattr(user, "profile") and user.profile.role:
        return user.profile.role.name == role_name
    return False
