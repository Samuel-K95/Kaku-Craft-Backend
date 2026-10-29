from decimal import Decimal
from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from orders.models import Order, PaymentProof
from products.models import Category, Product

User = get_user_model()


@pytest.fixture
def api_client():
	return APIClient()


@pytest.fixture
def customer(db):
	return User.objects.create_user(
		email="buyer@example.com",
		full_name="Buyer",
		password="StrongPass!234",
		role=User.Role.CUSTOMER,
	)


@pytest.fixture
def admin_user(db):
	return User.objects.create_user(
		email="admin@example.com",
		full_name="Admin",
		password="StrongPass!234",
		role=User.Role.ADMIN,
	)


@pytest.fixture
def product(db):
	category = Category.objects.create(name="Cardigans", is_active=True)
	return Product.objects.create(
		category=category,
		name="Crochet Cardigan",
		description="Handmade cardigan",
		price=Decimal("100.00"),
		status=Product.ProductStatus.ACTIVE,
		is_active=True,
	)


def _auth(client, user):
	client.force_authenticate(user=user)
	return client


def _image_upload(name="proof.png"):
	buffer = BytesIO()
	Image.new("RGB", (32, 32), color="red").save(buffer, format="PNG")
	return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@pytest.mark.django_db
def test_cart_add_update_remove(api_client, customer, product):
	client = _auth(api_client, customer)
	add = client.post(
		reverse("orders:cart-add"),
		{"product_id": product.id, "quantity": 2},
		format="json",
	)
	assert add.status_code == status.HTTP_201_CREATED
	assert add.data["cart"]["item_count"] == 2
	item_id = add.data["item"]["id"]

	updated = client.patch(
		reverse("orders:cart-item", kwargs={"item_id": item_id}),
		{"quantity": 3},
		format="json",
	)
	assert updated.status_code == status.HTTP_200_OK
	assert updated.data["item"]["quantity"] == 3

	removed = client.delete(reverse("orders:cart-item", kwargs={"item_id": item_id}))
	assert removed.status_code == status.HTTP_200_OK
	assert removed.data["item_count"] == 0


@pytest.mark.django_db
def test_order_payment_flow_fifty_percent_rule(api_client, customer, admin_user, product):
	buyer = _auth(api_client, customer)
	buyer.post(
		reverse("orders:cart-add"),
		{"product_id": product.id, "quantity": 1},
		format="json",
	)
	created = buyer.post(reverse("orders:order-list"), {}, format="json")
	assert created.status_code == status.HTTP_201_CREATED
	order_id = created.data["id"]
	assert created.data["status"] == Order.Status.PENDING_PAYMENT
	assert Decimal(created.data["deposit_required"]) == Decimal("50.00")

	upload = buyer.post(
		reverse("orders:order-payment-proof-upload", kwargs={"order_id": order_id}),
		{"image": _image_upload(), "amount": "50.00", "kind": "deposit"},
		format="multipart",
	)
	assert upload.status_code == status.HTTP_201_CREATED
	proof_id = upload.data["id"]

	order = Order.objects.get(pk=order_id)
	assert order.status == Order.Status.PAYMENT_SUBMITTED

	admin = APIClient()
	admin.force_authenticate(user=admin_user)
	reviewed = admin.post(
		reverse("orders:order-payment-proof-review", kwargs={"proof_id": proof_id}),
		{"approve": True},
		format="json",
	)
	assert reviewed.status_code == status.HTTP_200_OK

	order.refresh_from_db()
	assert order.amount_paid == Decimal("50.00")
	assert order.status == Order.Status.IN_PROGRESS


@pytest.mark.django_db
def test_admin_cannot_skip_deposit_for_in_progress(api_client, customer, admin_user, product):
	buyer = _auth(api_client, customer)
	buyer.post(
		reverse("orders:cart-add"),
		{"product_id": product.id, "quantity": 1},
		format="json",
	)
	created = buyer.post(reverse("orders:order-list"), {}, format="json")
	order_id = created.data["id"]

	admin = APIClient()
	admin.force_authenticate(user=admin_user)
	# Force payment_verified without deposit via direct status abuse path.
	order = Order.objects.get(pk=order_id)
	order.status = Order.Status.PAYMENT_VERIFIED
	order.save(update_fields=["status"])

	response = admin.post(
		reverse("orders:order-status", kwargs={"order_id": order_id}),
		{"status": Order.Status.IN_PROGRESS},
		format="json",
	)
	assert response.status_code == status.HTTP_400_BAD_REQUEST
