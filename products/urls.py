from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ProductImageUploadView, ProductViewSet

app_name = "products"

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="categories")
router.register("items", ProductViewSet, basename="products")

urlpatterns = [
	path(
		"items/<slug:slug>/images/",
		ProductImageUploadView.as_view(),
		name="product-images",
	),
	path(
		"items/<slug:slug>/images/<int:image_id>/",
		ProductImageUploadView.as_view(),
		name="product-image-detail",
	),
	path("", include(router.urls)),
]
