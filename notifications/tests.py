import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from notifications.models import Notification
from notifications.services import dispatch_event, ensure_telegram_link

User = get_user_model()


@pytest.fixture
def api_client():
	return APIClient()


@pytest.fixture
def customer(db):
	return User.objects.create_user(
		email="notify@example.com",
		full_name="Notify User",
		password="StrongPass!234",
		role=User.Role.CUSTOMER,
	)


@pytest.mark.django_db
def test_notification_list_and_telegram_link(api_client, customer):
	dispatch_event("order_placed", user=customer, order=type("O", (), {"pk": 1, "status": "pending_payment"})())
	api_client.force_authenticate(user=customer)

	listed = api_client.get(reverse("notifications:notification-list"))
	assert listed.status_code == status.HTTP_200_OK
	assert len(listed.data) == 1

	link = api_client.get(reverse("notifications:telegram-link"))
	assert link.status_code == status.HTTP_200_OK
	assert link.data["link_token"]

	token = ensure_telegram_link(customer).link_token
	with override_settings(TELEGRAM_WEBHOOK_SECRET="test-webhook-secret"):
		webhook = APIClient().post(
			reverse("notifications:telegram-webhook"),
			{"message": {"text": f"/start {token}", "chat": {"id": 12345}}},
			format="json",
			HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="test-webhook-secret",
		)
	assert webhook.status_code == status.HTTP_200_OK
	assert webhook.data["ok"] is True
