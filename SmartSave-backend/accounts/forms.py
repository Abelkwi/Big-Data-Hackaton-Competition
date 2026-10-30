from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import Profile


class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput()
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput()
    )

    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "store_name",
            "store_banner",
            "store_description",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()

        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2:

            if password1 != password2:
                raise ValidationError(
                    "Passwords do not match."
                )

        return cleaned_data

    def save(self, commit=True):

        user = User(
            username=self.cleaned_data["email"].split("@")[0],
            email=self.cleaned_data["email"].lower(),
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
        )

        user.set_password(
            self.cleaned_data["password1"]
        )

        if commit:
            user.save()

        return user


class UserLoginForm(AuthenticationForm):

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter your email"
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password"
            }
        )
    )


class ProfileUpdateForm(forms.ModelForm):

    class Meta:

        model = Profile

        fields = (
            "profile_photo",
            "phone",
            "organization",
            "gender",
            "bio",
            "store_name",
            "store_banner",
            "store_description",
            "province",
            "district",
            "sector",
            "cell",
            "village",
            )

        widgets = {

            "bio": forms.Textarea(
                attrs={
                    "rows": 4
                }
            ),
            "store_description": forms.Textarea(
                attrs={
                    "rows": 4
                }
            ),
        }