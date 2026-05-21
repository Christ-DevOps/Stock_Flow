from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.homepage, name="home"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
    path("password/change/", views.change_password_view, name="change_password"),
    path("password/reset/", views.password_reset_request, name="password_reset"),
]