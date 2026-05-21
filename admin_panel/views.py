from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile, Role, AuditLog, SystemSettings
from accounts.forms import UserForm, UserProfileForm, RoleForm, SystemSettingsForm
from inventory.models import Product, Category, StockMovement, PurchaseOrder, Notification, Supplier

from admin_panel.apps import AdminPanelConfig


def _log_action(request, action, **kwargs):
    if not request.user.is_authenticated:
        return
    AuditLog.objects.create(
        user=request.user,
        action=action,
        ip_address=request.META.get("REMOTE_ADDR"),
        **kwargs,
    )


def admin_dashboard(request):
    today = timezone.localdate()
    seven_days_ago = today - timedelta(days=7)

    total_users   = User.objects.count()
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_movements = StockMovement.objects.count()

    total_value = Product.objects.aggregate(t=Sum("price", default=0))["t"]
    pending_pos = PurchaseOrder.objects.filter(status__in=["draft", "sent"]).count()
    low_stock   = Product.objects.filter(quantity__lte=F("low_stock_threshold")).count()
    supplier_count = Supplier.objects.count()
    unread_nots = Notification.objects.filter(is_read=False).count()

    recent_users = User.objects.order_by("-date_joined")[:5]
    recent_actions = AuditLog.objects.select_related("user").order_by("-timestamp")[:10]

    # Last-7-days movement chart data
    daily_in  = [0, 0, 0, 0, 0, 0, 0]
    daily_out = [0, 0, 0, 0, 0, 0, 0]
    day_labels = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_labels.append(d.strftime("%a"))
        mvs = StockMovement.objects.filter(date__date=d)
        daily_in[i]  = mvs.filter(movement_type="IN").aggregate(t=Sum("quantity"))["t"] or 0
        daily_out[i] = mvs.filter(movement_type="OUT").aggregate(t=Sum("quantity"))["t"] or 0

    day_labels = list(reversed(day_labels))
    daily_in  = list(reversed(daily_in))
    daily_out = list(reversed(daily_out))

    qs = StockMovement.objects.order_by("-date")[:200]
    category_counts = (
        Category.objects.annotate(n=Count("products"))
        .order_by("-n")[:8]
    )

    quick_actions = [
        {
            "title": "Manage Users",
            "url": reverse("admin_users"),
            "icon": "bi-people",
            "label": "Users",
            "value": total_users,
        },
        {
            "title": "Roles & Permissions",
            "url": reverse("admin_roles"),
            "icon": "bi-shield-check",
            "label": "Roles",
            "value": Role.objects.count(),
        },
        {
            "title": "Purchase Orders",
            "url": reverse("admin_purchase_orders"),
            "icon": "bi-receipt",
            "label": "Pending",
            "value": pending_pos,
        },
        {
            "title": "Suppliers",
            "url": reverse("supplier_list"),
            "icon": "bi-building",
            "label": "Suppliers",
            "value": supplier_count,
        },
        {
            "title": "Audit Log",
            "url": reverse("audit_log"),
            "icon": "bi-clock-history",
            "label": "Events",
            "value": recent_actions.count(),
        },
        {
            "title": "Reports",
            "url": reverse("reports"),
            "icon": "bi-bar-chart-line",
            "label": "Reports",
            "value": total_movements,
        },
        {
            "title": "Settings",
            "url": reverse("settings"),
            "icon": "bi-gear",
            "label": "Settings",
            "value": unread_nots,
        },
    ]

    context = {
        "total_users": total_users, "total_products": total_products,
        "total_categories": total_categories, "total_movements": total_movements,
        "total_value": total_value, "pending_pos": pending_pos,
        "low_stock": low_stock, "unread_nots": unread_nots,
        "recent_users": recent_users, "recent_actions": recent_actions,
        "day_labels": day_labels, "daily_in": daily_in, "daily_out": daily_out,
        "category_counts": category_counts,
        "movements_chart_data": qs,
        "quick_actions": quick_actions,
    }
    return render(request, "admin_panel/dashboard.html", context)


def user_list(request):
    q = request.GET.get("q", "")
    role_filter = request.GET.get("role", "")
    qs = User.objects.select_related("profile").annotate(
        mov=Count("profile__user__username"),  # placeholder
    )

    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
    if role_filter:
        qs = qs.filter(profile__role_id=role_filter)

    from django.core.paginator import Paginator
    paginator = Paginator(qs.order_by("-date_joined"), 8)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "admin_panel/users.html", {
        "users": page, "roles": Role.objects.all(),
        "q": q, "role_filter": role_filter,
    })


def user_create(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            email = form.cleaned_data.get("email") or user.username
            user.username = email
            user.set_password("StockPro@2024")
            user.save()
            _log_action(request, "create", model_name="User", object_id=str(user.pk), object_repr=user.username)
            messages.success(request, f"User '{user.username}' created. Default password: StockPro@2024")
            return redirect("admin_users")
    else:
        form = UserForm()
    return render(request, "admin_panel/user_form.html", {"form": form, "title": "Add User"})


def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=user.profile)
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            _log_action(request, "update", model_name="User", object_id=str(pk), object_repr=user.username)
            messages.success(request, f"User '{user.username}' updated.")
            return redirect("admin_users")
    else:
        form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=user.profile)
    return render(request, "admin_panel/user_form.html", {
        "form": form, "profile_form": profile_form,
        "user_obj": user, "title": f"Edit {user.username}",
    })


def user_deactivate(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user.is_active = False
        user.save()
        _log_action(request, "update", model_name="User", object_id=str(pk), object_repr=user.username)
        messages.success(request, f"User '{user.username}' deactivated.")
    return redirect("admin_users")


def user_activate(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user.is_active = True
        user.save()
        _log_action(request, "update", model_name="User", object_id=str(pk), object_repr=user.username)
        messages.success(request, f"User '{user.username}' activated.")
    return redirect("admin_users")


def role_list(request):
    qs = Role.objects.annotate(user_count=Count("userprofile")).order_by("name")
    return render(request, "admin_panel/roles.html", {"roles": qs})


def role_create(request):
    if request.method == "POST":
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Role created.")
            return redirect("admin_roles")
    else:
        form = RoleForm()
    return render(request, "admin_panel/role_form.html", {"form": form, "title": "Add Role"})


def role_edit(request, pk):
    role = get_object_or_404(Role, pk=pk)
    if request.method == "POST":
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, "Role updated.")
            return redirect("admin_roles")
    else:
        form = RoleForm(instance=role)
    return render(request, "admin_panel/role_form.html", {"form": form, "role": role, "title": f"Edit {role.name}"})


def admin_purchase_orders(request):
    qs = PurchaseOrder.objects.select_related("supplier", "product").order_by("-order_date")
    return render(request, "admin_panel/purchase_orders.html", {
        "orders": qs, "STATUS_CHOICES": PurchaseOrder.STATUS_CHOICES,
    })


def audit_log_list(request):
    qs = AuditLog.objects.select_related("user").order_by("-timestamp")
    if request.GET.get("user"):
        qs = qs.filter(user_id=request.GET["user"])
    if request.GET.get("action"):
        qs = qs.filter(action=request.GET["action"])
    from django.core.paginator import Paginator
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "admin_panel/audit_log.html", {
        "logs": page, "users": User.objects.all(),
        "ACTION_CHOICES": AuditLog.ACTION_CHOICES,
        "q_user": request.GET.get("user", ""),
        "q_action": request.GET.get("action", ""),
    })


def export_audit_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch

    qs = AuditLog.objects.select_related("user").order_by("-timestamp")
    if request.GET.get("user"):
        qs = qs.filter(user_id=request.GET["user"])
    if request.GET.get("action"):
        qs = qs.filter(action=request.GET["action"])

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=audit_log.pdf"

    doc = SimpleDocTemplate(response, pagesize=A4, topMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title = Paragraph("<b>StockPro Audit Log</b>", styles["Title"])
    story = [title, Spacer(1, 0.2 * inch)]

    data = [["User", "Action", "Object", "Details", "IP", "Time"]]
    for log in qs:
        data.append([
            log.user.username if log.user else "—",
            log.get_action_display(),
            log.object_repr or log.model_name or "—",
            log.changes or "—",
            log.ip_address or "—",
            log.timestamp.strftime("%Y-%m-%d %H:%M"),
        ])

    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9ff")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)
    doc.build(story)

    return response


def settings_view(request):
    settings = SystemSettings.get_settings()
    form = SystemSettingsForm(instance=settings)
    if request.method == "POST":
        form = SystemSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            _log_action(request, "update", model_name="SystemSettings", object_id=1)
            messages.success(request, "Settings updated successfully!")
            return redirect("settings")
    return render(request, "admin_panel/settings.html", {"form": form, "settings": settings})
