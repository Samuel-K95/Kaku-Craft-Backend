import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
	return APIClient()


@pytest.fixture
def customer(db):
	return User.objects.create_user(
		email="chatuser@example.com",
		full_name="Chat User",
		password="StrongPass!234",
		role=User.Role.CUSTOMER,
	)


@pytest.fixture
def admin_user(db):
	return User.objects.create_user(
		email="chatadmin@example.com",
		full_name="Chat Admin",
		password="StrongPass!234",
		role=User.Role.ADMIN,
	)


@pytest.mark.django_db
def test_conversation_polling_flow(api_client, customer, admin_user):
	api_client.force_authenticate(user=customer)
	created = api_client.post(
		reverse("messaging:conversation-list"),
		{"subject": "Support", "body": "Hello admin"},
		format="json",
	)
	assert created.status_code == status.HTTP_201_CREATED
	conversation_id = created.data["id"]

	admin = APIClient()
	admin.force_authenticate(user=admin_user)
	reply = admin.post(
		reverse("messaging:conversation-messages", kwargs={"pk": conversation_id}),
		{"body": "Hi, how can we help?"},
		format="json",
	)
	assert reply.status_code == status.HTTP_201_CREATED

	marked = api_client.post(
		reverse("messaging:conversation-read", kwargs={"pk": conversation_id})
	)
	assert marked.status_code == status.HTTP_200_OK
	assert marked.data["marked_read"] >= 1
