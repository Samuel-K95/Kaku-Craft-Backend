from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
	path("cart/", views.CartDetailView.as_view(), name="cart-detail"),
	path("cart/items/", views.CartAddItemView.as_view(), name="cart-add"),
	path("cart/items/<int:item_id>/", views.CartItemDetailView.as_view(), name="cart-item"),
	path("expert/jobs/", views.ExpertJobListView.as_view(), name="expert-jobs"),
	path("", views.OrderListCreateView.as_view(), name="order-list"),
	path("<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
	path(
		"<int:order_id>/payment-proofs/",
		views.OrderPaymentProofUploadView.as_view(),
		name="order-payment-proof-upload",
	),
	path(
		"payment-proofs/<int:proof_id>/review/",
		views.OrderPaymentProofReviewView.as_view(),
		name="order-payment-proof-review",
	),
	path(
		"<int:order_id>/status/",
		views.AdminOrderStatusUpdateView.as_view(),
		name="order-status",
	),
	path(
		"<int:order_id>/assign-expert/",
		views.AssignExpertView.as_view(),
		name="assign-expert",
	),
	path(
		"<int:order_id>/expert/start/",
		views.ExpertStartView.as_view(),
		name="expert-start",
	),
	path(
		"<int:order_id>/expert/complete/",
		views.ExpertCompleteView.as_view(),
		name="expert-complete",
	),
	path("custom/", views.CustomOrderListCreateView.as_view(), name="custom-order-list"),
	path("custom/<int:pk>/", views.CustomOrderDetailView.as_view(), name="custom-order-detail"),
	path(
		"custom/<int:pk>/decision/",
		views.CustomOrderDecisionView.as_view(),
		name="custom-order-decision",
	),
	path(
		"custom/<int:pk>/quote/",
		views.CustomOrderQuoteView.as_view(),
		name="custom-order-quote",
	),
	path(
		"custom/<int:pk>/confirm/",
		views.CustomOrderConfirmView.as_view(),
		name="custom-order-confirm",
	),
	path(
		"custom/<int:pk>/payment-proofs/",
		views.CustomOrderPaymentUploadView.as_view(),
		name="custom-order-payment-upload",
	),
	path(
		"custom/payment-proofs/<int:proof_id>/review/",
		views.CustomOrderPaymentReviewView.as_view(),
		name="custom-order-payment-review",
	),
	path(
		"custom/<int:pk>/status/",
		views.CustomOrderStatusUpdateView.as_view(),
		name="custom-order-status",
	),
]
