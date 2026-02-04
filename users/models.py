from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
	def create_user(self, email, password=None, role=None, **extra_fields):
		if not email:
			raise ValueError("Users must have an email address")

		email = self.normalize_email(email)
		extra_fields.setdefault("is_active", True)
		role = role or User.Role.CUSTOMER

		user = self.model(email=email, role=role, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault("is_staff", True)
		extra_fields.setdefault("is_superuser", True)

		if extra_fields.get("is_staff") is not True:
			raise ValueError("Superuser must have is_staff=True.")
		if extra_fields.get("is_superuser") is not True:
			raise ValueError("Superuser must have is_superuser=True.")

		return self.create_user(email, password, role=User.Role.ADMIN, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
	class Role(models.TextChoices):
		CUSTOMER = "customer", "Customer"
		ADMIN = "admin", "Admin"

	email = models.EmailField(unique=True)
	first_name = models.CharField(max_length=150, blank=True)
	last_name = models.CharField(max_length=150, blank=True)
	role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	telegram_id = models.CharField(max_length=100, blank=True, null=True)
	date_joined = models.DateTimeField(auto_now_add=True)

	objects = UserManager()

	USERNAME_FIELD = "email"
	REQUIRED_FIELDS = []

	def __str__(self):
		return self.email
