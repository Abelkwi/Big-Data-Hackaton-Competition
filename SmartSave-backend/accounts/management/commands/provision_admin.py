from getpass import getpass

from django.conf import settings
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


User = get_user_model()


class Command(BaseCommand):
    help = "Provision the single administrator account configured by ADMIN_LOGIN_EMAIL."

    @transaction.atomic
    def handle(self, *args, **options):
        email = getattr(settings, "ADMIN_LOGIN_EMAIL", "")
        if not email:
            raise CommandError("Set ADMIN_LOGIN_EMAIL in the backend environment first.")

        password = getpass("New administrator password: ")
        confirmation = getpass("Confirm administrator password: ")
        if not password or password != confirmation:
            raise CommandError("Passwords must match and cannot be empty.")

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            base_username = email.split("@", 1)[0][:150] or "administrator"
            username = base_username
            suffix = 1
            while User.objects.filter(username=username).exists():
                suffix_text = str(suffix)
                username = f"{base_username[:150 - len(suffix_text)]}{suffix_text}"
                suffix += 1
            user = User(username=username, email=email)

        try:
            password_validation.validate_password(password, user=user)
        except ValidationError as error:
            raise CommandError(str(error)) from error

        user.email = email
        user.role = "admin"
        user.is_active = True
        user.is_staff = True
        user.is_superuser = False
        user.is_verified = True
        user.set_password(password)
        user.save()
        self.stdout.write(
            self.style.SUCCESS(
                "Administrator account provisioned with a hashed password."
            )
        )
