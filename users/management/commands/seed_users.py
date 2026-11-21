"""
Management command: seed_users
-------------------------------
Creates one seeded account per role if it doesn't already exist.
Also ensures the system_admin account has can_impersonate=True.

Usage:
    python manage.py seed_users
    python manage.py seed_users --reset   # deletes & re-creates all seed accounts
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

SEED_ACCOUNTS = [
    {
        "email": "user@kakucraft.com",
        "full_name": "Demo User",
        "password": "KakuUser2024!",
        "role": "user",
        "is_staff": False,
        "is_superuser": False,
        "can_impersonate": False,
    },
    {
        "email": "customer@kakucraft.com",
        "full_name": "Demo Customer",
        "password": "KakuCustomer2024!",
        "role": "customer",
        "is_staff": False,
        "is_superuser": False,
        "can_impersonate": False,
    },
    {
        "email": "expert@kakucraft.com",
        "full_name": "Demo Expert",
        "password": "KakuExpert2024!",
        "role": "expert",
        "is_staff": False,
        "is_superuser": False,
        "can_impersonate": False,
    },
    {
        "email": "admin@kakucraft.com",
        "full_name": "Demo Admin",
        "password": "KakuAdmin2024!",
        "role": "admin",
        "is_staff": True,
        "is_superuser": False,
        "can_impersonate": False,
    },
    {
        "email": "superadmin@kakucraft.com",
        "full_name": "Super Admin",
        "password": "KakuSuperAdmin2024!",
        "role": "super_admin",
        "is_staff": True,
        "is_superuser": True,
        "can_impersonate": False,
    },
    {
        "email": "system@kakucraft.com",
        "full_name": "System Admin",
        "password": "KakuSystem2024!",
        "role": "system_admin",
        "is_staff": True,
        "is_superuser": True,
        "can_impersonate": True,  # <-- can sign in as any user
    },
]


class Command(BaseCommand):
    help = "Seed one account per role (user, customer, expert, admin, super_admin, system_admin)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing seed accounts and re-create them.",
        )

    def handle(self, *args, **options):
        reset = options["reset"]

        for account in SEED_ACCOUNTS:
            email = account["email"]

            if reset:
                deleted, _ = User.objects.filter(email=email).delete()
                if deleted:
                    self.stdout.write(self.style.WARNING(f"  Deleted existing: {email}"))

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": account["full_name"],
                    "role": account["role"],
                    "is_staff": account["is_staff"],
                    "is_superuser": account["is_superuser"],
                    "can_impersonate": account["can_impersonate"],
                    "is_active": True,
                },
            )

            if created:
                user.set_password(account["password"])
                user.save(update_fields=["password"])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✔ Created [{account['role']:12s}] {email}  (pw: {account['password']})"
                    )
                )
            else:
                # Ensure can_impersonate is always up-to-date even on existing accounts
                if user.can_impersonate != account["can_impersonate"]:
                    user.can_impersonate = account["can_impersonate"]
                    user.save(update_fields=["can_impersonate"])
                self.stdout.write(f"  — Already exists: {email} (skipped)")

        self.stdout.write(self.style.SUCCESS("\nDone. All seed accounts are ready."))
