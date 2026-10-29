from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
	return APIClient()


@pytest.fixture
def user(db):
	return User.objects.create_user(
		email="customer@example.com",
		full_name="Customer User",
		password="Str0ngPass!234",
		role=User.Role.CUSTOMER,
	)


@pytest.fixture
def super_admin(db):
	return User.objects.create_user(
		email="owner@example.com",
		full_name="Owner User",
		password="Str0ngPass!234",
		role=User.Role.SUPER_ADMIN,
	)


@pytest.mark.django_db
def test_signup_creates_customer_user(api_client):
	payload = {
		"email": "newcustomer@example.com",
		"full_name": "New Customer",
		"password": "An0therStrong!234",
	}

	response = api_client.post(reverse("users:signup"), payload, format="json")

	assert response.status_code == status.HTTP_201_CREATED
	created = User.objects.get(email="newcustomer@example.com")
	assert created.role == User.Role.CUSTOMER
	assert created.check_password("An0therStrong!234")


@pytest.mark.django_db
def test_signup_rejects_non_customer_role_for_unauthenticated(api_client):
	payload = {
		"email": "adminrequest@example.com",
		"full_name": "Role Escalation",
		"password": "An0therStrong!234",
		"role": User.Role.ADMIN,
	}

	response = api_client.post(reverse("users:signup"), payload, format="json")

	assert response.status_code == status.HTTP_400_BAD_REQUEST
	assert "role" in response.data


@pytest.mark.django_db
def test_signup_rejects_weak_password(api_client):
	payload = {
		"email": "weakpass@example.com",
		"full_name": "Weak Password",
		"password": "password",
	}

	response = api_client.post(reverse("users:signup"), payload, format="json")

	assert response.status_code == status.HTTP_400_BAD_REQUEST
	assert "password" in response.data


@pytest.mark.django_db
def test_signup_allows_super_admin_to_create_admin(api_client, super_admin):
	api_client.force_authenticate(user=super_admin)
	payload = {
		"email": "admincreated@example.com",
		"full_name": "New Admin",
		"password": "An0therStrong!234",
		"role": User.Role.ADMIN,
	}

	response = api_client.post(reverse("users:signup"), payload, format="json")

	assert response.status_code == status.HTTP_201_CREATED
	assert User.objects.get(email="admincreated@example.com").role == User.Role.ADMIN


@pytest.mark.django_db
def test_admin_cannot_create_admin_user(api_client):
	admin = User.objects.create_user(
		email="existingadmin@example.com",
		full_name="Existing Admin",
		password="Str0ngPass!234",
		role=User.Role.ADMIN,
	)
	api_client.force_authenticate(user=admin)

	payload = {
		"email": "anotheradmin@example.com",
		"full_name": "Another Admin",
		"password": "An0therStrong!234",
		"role": User.Role.ADMIN,
	}

	response = api_client.post(reverse("users:signup"), payload, format="json")

	assert response.status_code == status.HTTP_400_BAD_REQUEST
	assert "role" in response.data


@pytest.mark.django_db
def test_signin_returns_tokens_and_user_payload(api_client, user):
	payload = {"email": user.email, "password": "Str0ngPass!234"}

	response = api_client.post(reverse("users:signin"), payload, format="json")

	assert response.status_code == status.HTTP_200_OK
	assert "access" in response.data
	assert "refresh" in response.data
	assert response.data["user"]["email"] == user.email
	assert response.data["user"]["role"] == User.Role.CUSTOMER


@pytest.mark.django_db
def test_token_refresh_works(api_client, user):
	signin = api_client.post(
		reverse("users:signin"),
		{"email": user.email, "password": "Str0ngPass!234"},
		format="json",
	)

	response = api_client.post(
		reverse("users:refresh"),
		{"refresh": signin.data["refresh"]},
		format="json",
	)

	assert response.status_code == status.HTTP_200_OK
	assert "access" in response.data


@pytest.mark.django_db
def test_profile_endpoint_requires_authentication(api_client):
	response = api_client.get(reverse("users:profile"))

	assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_profile_endpoint_returns_current_user(api_client, user):
	api_client.force_authenticate(user=user)

	response = api_client.get(reverse("users:profile"))

	assert response.status_code == status.HTTP_200_OK
	assert response.data["email"] == user.email
	assert response.data["full_name"] == user.full_name


@pytest.mark.django_db
def test_profile_edit_updates_name_and_avatar(api_client, user):
	api_client.force_authenticate(user=user)

	image_io = BytesIO()
	Image.new("RGB", (2, 2), color=(255, 0, 0)).save(image_io, format="PNG")
	image_io.seek(0)
	avatar = SimpleUploadedFile("avatar.png", image_io.read(), content_type="image/png")

	response = api_client.patch(
		reverse("users:edit-profile"),
		{"full_name": "Updated Name", "profile_picture": avatar},
		format="multipart",
	)

	assert response.status_code == status.HTTP_200_OK
	user.refresh_from_db()
	assert user.full_name == "Updated Name"
	assert user.profile_picture


@pytest.mark.django_db
def test_change_password_updates_credentials(api_client, user):
	api_client.force_authenticate(user=user)

	response = api_client.post(
		reverse("users:change-password"),
		{"old_password": "Str0ngPass!234", "new_password": "N3wStrongPass!345"},
		format="json",
	)

	assert response.status_code == status.HTTP_200_OK

	api_client.force_authenticate(user=None)
	old_login = api_client.post(
		reverse("users:signin"),
		{"email": user.email, "password": "Str0ngPass!234"},
		format="json",
	)
	new_login = api_client.post(
		reverse("users:signin"),
		{"email": user.email, "password": "N3wStrongPass!345"},
		format="json",
	)

	assert old_login.status_code == status.HTTP_401_UNAUTHORIZED
	assert new_login.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_change_password_requires_correct_old_password(api_client, user):
	api_client.force_authenticate(user=user)

	response = api_client.post(
		reverse("users:change-password"),
		{"old_password": "wrong-pass", "new_password": "N3wStrongPass!345"},
		format="json",
	)

	assert response.status_code == status.HTTP_400_BAD_REQUEST
	assert "old_password" in response.data
