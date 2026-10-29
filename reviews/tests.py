from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from orders.models import Order, OrderItem
from products.models import Category, Product
from reviews.models import Review

User = get_user_model()


@pytest.fixture
def api_client():
	return APIClient()


@pytest.fixture
def customer(db):
	return User.objects.create_user(
		email="reviewer@example.com",
		full_name="Reviewer",
		password="StrongPass!234",
		role=User.Role.CUSTOMER,
	)


@pytest.fixture
def admin_user(db):
	return User.objects.create_user(
		email="mod@example.com",
		full_name="Moderator",
		password="StrongPass!234",
		role=User.Role.ADMIN,
	)


@pytest.fixture
def catalog(db, customer):
	category = Category.objects.create(name="Toys", is_active=True)
	product = Product.objects.create(
		category=category,
		name="Crochet Bear",
		description="Soft bear",
		price=Decimal("25.00"),
		is_active=True,
		status=Product.ProductStatus.ACTIVE,
	)
	order = Order.objects.create(
		user=customer,
		total_price=Decimal("25.00"),
		amount_paid=Decimal("25.00"),
		status=Order.Status.COMPLETED,
	)
	OrderItem.objects.create(
		order=order,
		product=product,
		product_name=product.name,
		unit_price=product.price,
		quantity=1,
		line_total=product.price,
	)
	return {"product": product, "order": order}


@pytest.mark.django_db
def test_wishlist_add_and_remove(api_client, customer, catalog):
	api_client.force_authenticate(user=customer)
	product = catalog["product"]
	added = api_client.post(
		reverse("reviews:wishlist"),
		{"product_id": product.id},
		format="json",
	)
	assert added.status_code == status.HTTP_201_CREATED

	listed = api_client.get(reverse("reviews:wishlist"))
	assert listed.status_code == status.HTTP_200_OK
	assert len(listed.data) == 1

	removed = api_client.delete(
		reverse("reviews:wishlist-remove", kwargs={"product_id": product.id})
	)
	assert removed.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_review_requires_completed_purchase_and_moderation(
	api_client, customer, admin_user, catalog
):
	api_client.force_authenticate(user=customer)
	product = catalog["product"]
	order = catalog["order"]

	created = api_client.post(
		reverse("reviews:review-list"),
		{
			"product": product.id,
			"order": order.id,
			"rating": 5,
			"comment": "Beautiful work",
		},
		format="json",
	)
	assert created.status_code == status.HTTP_201_CREATED
	review_id = created.data["id"]
	assert created.data["is_approved"] is False

	public = APIClient().get(reverse("reviews:review-list"), {"product": product.id})
	assert public.status_code == status.HTTP_200_OK
	assert public.data == []

	admin = APIClient()
	admin.force_authenticate(user=admin_user)
	moderated = admin.post(
		reverse("reviews:review-moderate", kwargs={"pk": review_id}),
		{"is_approved": True},
		format="json",
	)
	assert moderated.status_code == status.HTTP_200_OK
	assert Review.objects.get(pk=review_id).is_approved is True
