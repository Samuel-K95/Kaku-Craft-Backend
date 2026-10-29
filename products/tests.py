import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from products.models import Category, Product

User = get_user_model()


@pytest.fixture
def api_client():
	return APIClient()


@pytest.fixture
def customer(db):
	return User.objects.create_user(
		email="customer2@example.com",
		full_name="Customer Two",
		password="StrongPass!234",
		role=User.Role.CUSTOMER,
	)


@pytest.fixture
def admin_user(db):
	return User.objects.create_user(
		email="admin2@example.com",
		full_name="Admin Two",
		password="StrongPass!234",
		role=User.Role.ADMIN,
	)


@pytest.fixture
def product_data(db):
	toys = Category.objects.create(name="Toys", description="Toys category", is_active=True)
	dolls = Category.objects.create(name="Dolls", description="Dolls category", is_active=True)
	Category.objects.create(name="Hidden", description="Hidden category", is_active=False)

	p1 = Product.objects.create(
		category=toys,
		name="Crochet Bear",
		description="Soft toy bear",
		price="10.00",
		size="S",
		sold_count=2,
		social_links={"instagram": "https://instagram.com/kaku_bear"},
	)
	p2 = Product.objects.create(
		category=dolls,
		name="Crochet Doll",
		description="Customizable doll",
		price="20.00",
		size="M",
		sold_count=8,
		social_links={"tiktok": "https://tiktok.com/@kaku_doll"},
	)
	Product.objects.create(
		category=toys,
		name="Draft Product",
		description="Should not be public",
		price="5.00",
		size="XS",
		status=Product.ProductStatus.DRAFT,
		is_active=False,
	)

	return {"categories": (toys, dolls), "products": (p1, p2)}


@pytest.mark.django_db
def test_public_categories_list_returns_only_active(api_client, product_data):
	response = api_client.get(reverse("products:categories-list"))

	assert response.status_code == status.HTTP_200_OK
	names = {item["name"] for item in response.data}
	assert names == {"Toys", "Dolls"}


@pytest.mark.django_db
def test_inactive_category_detail_hidden_from_public(api_client):
	inactive = Category.objects.create(name="Inactive", is_active=False)

	response = api_client.get(reverse("products:categories-detail", args=[inactive.slug]))

	assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_public_products_list_returns_only_active_products(api_client, product_data):
	response = api_client.get(reverse("products:products-list"))

	assert response.status_code == status.HTTP_200_OK
	names = {item["name"] for item in response.data}
	assert "Crochet Bear" in names
	assert "Crochet Doll" in names
	assert "Draft Product" not in names


@pytest.mark.django_db
def test_product_filters_by_category_price_search_and_ordering(api_client, product_data):
	dolls = product_data["categories"][1]

	by_category = api_client.get(reverse("products:products-list"), {"category": dolls.slug})
	assert by_category.status_code == status.HTTP_200_OK
	assert [item["name"] for item in by_category.data] == ["Crochet Doll"]

	by_price = api_client.get(reverse("products:products-list"), {"min_price": "15", "max_price": "25"})
	assert by_price.status_code == status.HTTP_200_OK
	assert [item["name"] for item in by_price.data] == ["Crochet Doll"]

	by_search = api_client.get(reverse("products:products-list"), {"search": "bear"})
	assert by_search.status_code == status.HTTP_200_OK
	assert [item["name"] for item in by_search.data] == ["Crochet Bear"]

	by_popularity = api_client.get(reverse("products:products-list"), {"ordering": "popularity"})
	assert by_popularity.status_code == status.HTTP_200_OK
	assert by_popularity.data[0]["name"] == "Crochet Doll"


@pytest.mark.django_db
def test_product_detail_uses_slug(api_client, product_data):
	product = product_data["products"][0]
	response = api_client.get(reverse("products:products-detail", args=[product.slug]))

	assert response.status_code == status.HTTP_200_OK
	assert response.data["name"] == "Crochet Bear"


@pytest.mark.django_db
def test_invalid_price_filter_returns_400(api_client, product_data):
	response = api_client.get(reverse("products:products-list"), {"min_price": "not-a-number"})

	assert response.status_code == status.HTTP_400_BAD_REQUEST
	assert "min_price" in response.data


@pytest.mark.django_db
def test_customer_cannot_create_category_or_product(api_client, customer, product_data):
	api_client.force_authenticate(user=customer)

	category_response = api_client.post(
		reverse("products:categories-list"),
		{"name": "Cardigans", "description": "Cardigan category", "is_active": True},
		format="json",
	)
	product_response = api_client.post(
		reverse("products:products-list"),
		{
			"category": product_data["categories"][0].id,
			"name": "Cardigan A",
			"description": "Warm cardigan",
			"price": "30.00",
			"size": "L",
			"status": Product.ProductStatus.ACTIVE,
			"is_active": True,
			"social_links": {"instagram": "https://instagram.com/cardigan_a"},
		},
		format="json",
	)

	assert category_response.status_code == status.HTTP_403_FORBIDDEN
	assert product_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_unauthenticated_cannot_create_category_or_product(api_client, product_data):
	category_response = api_client.post(
		reverse("products:categories-list"),
		{"name": "Scarves", "description": "Scarves category", "is_active": True},
		format="json",
	)
	product_response = api_client.post(
		reverse("products:products-list"),
		{
			"category": product_data["categories"][0].id,
			"name": "Scarf A",
			"description": "Warm scarf",
			"price": "12.00",
			"size": "M",
			"status": Product.ProductStatus.ACTIVE,
			"is_active": True,
		},
		format="json",
	)

	assert category_response.status_code == status.HTTP_401_UNAUTHORIZED
	assert product_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_admin_can_create_category_and_product(api_client, admin_user):
	api_client.force_authenticate(user=admin_user)

	category_response = api_client.post(
		reverse("products:categories-list"),
		{"name": "Cardigans", "description": "Cardigan category", "is_active": True},
		format="json",
	)
	assert category_response.status_code == status.HTTP_201_CREATED

	product_response = api_client.post(
		reverse("products:products-list"),
		{
			"category": category_response.data["id"],
			"name": "Blue Cardigan",
			"description": "Soft handmade cardigan",
			"price": "35.50",
			"size": "M",
			"status": Product.ProductStatus.ACTIVE,
			"is_active": True,
			"social_links": {
				"instagram": "https://instagram.com/blue_cardigan",
				"tiktok": "https://tiktok.com/@blue_cardigan",
			},
		},
		format="json",
	)

	assert product_response.status_code == status.HTTP_201_CREATED
	assert Category.objects.filter(name="Cardigans").exists()
	assert Product.objects.filter(name="Blue Cardigan").exists()


@pytest.mark.django_db
def test_slug_generation_handles_duplicate_names():
	category = Category.objects.create(name="Toys")

	p1 = Product.objects.create(
		category=category,
		name="Classic Doll",
		description="A",
		price="10.00",
	)
	p2 = Product.objects.create(
		category=category,
		name="Classic Doll",
		description="B",
		price="11.00",
	)

	assert p1.slug == "classic-doll"
	assert p2.slug == "classic-doll-2"


@pytest.mark.django_db
def test_social_links_validator_rejects_invalid_values():
	category = Category.objects.create(name="Cardigans")
	product = Product(
		category=category,
		name="Bad Social",
		description="Bad data",
		price="9.99",
		social_links={"instagram": "instagram.com/missing-protocol"},
	)

	with pytest.raises(ValidationError):
		product.full_clean()
