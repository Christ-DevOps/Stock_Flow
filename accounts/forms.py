from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from .models import UserProfile, Role, SystemSettings


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Enter your password"})
    )


class CustomUserCreationForm(UserCreationForm):
    name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your full name"}),
        label="Full Name",
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter your email"}),
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False,
    )

    class Meta:
        model = User
        fields = ("name", "email", "role", "password1", "password2")

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        if email:
            cleaned_data["username"] = email
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data.get("email")
        full_name = self.cleaned_data.get("name", "").strip()
        if email:
            user.username = email
        if full_name:
            parts = full_name.split()
            user.first_name = parts[0]
            user.last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        if commit:
            user.save()
        return user


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_active", "is_staff", "is_superuser"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_superuser": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["phone", "role", "avatar", "is_active"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone number"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "avatar": forms.FileInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["phone", "avatar"]
        widgets = {
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter phone number (optional)"}
            ),
            "avatar": forms.FileInput(attrs={"class": "form-control-classic"}),
        }


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ["name", "description", "permissions"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "permissions": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": '{"can_manage_users": true}'}),
        }

    def clean_permissions(self):
        import json
        data = self.cleaned_data.get("permissions", {})
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return {}
        return data


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = "__all__"
        widgets = {
            "store_name": forms.TextInput(attrs={"class": "form-control"}),
            "store_address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "store_phone": forms.TextInput(attrs={"class": "form-control"}),
            "store_email": forms.EmailInput(attrs={"class": "form-control"}),
            "currency": forms.TextInput(attrs={"class": "form-control", "maxlength": 3}),
            "tax_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "low_stock_threshold": forms.NumberInput(attrs={"class": "form-control"}),
            "smtp_host": forms.TextInput(attrs={"class": "form-control"}),
            "smtp_port": forms.NumberInput(attrs={"class": "form-control"}),
            "smtp_username": forms.TextInput(attrs={"class": "form-control"}),
            "smtp_password": forms.PasswordInput(attrs={"class": "form-control"}),
            "enable_alerts": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter your email"})
    )


class SetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="New Password",
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="Confirm New Password",
    )


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Current password"}),
        label="Current Password",
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "New password"}),
        label="New Password",
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm new password"}),
        label="Confirm Password",
    )
