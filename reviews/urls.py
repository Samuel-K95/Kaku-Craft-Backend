from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
	path("wishlist/", views.WishlistListCreateView.as_view(), name="wishlist"),
	path(
		"wishlist/<int:product_id>/",
		views.WishlistRemoveView.as_view(),
		name="wishlist-remove",
	),
	path("", views.ReviewListCreateView.as_view(), name="review-list"),
	path("<int:pk>/", views.ReviewDetailView.as_view(), name="review-detail"),
	path("<int:pk>/moderate/", views.ReviewModerationView.as_view(), name="review-moderate"),
]
