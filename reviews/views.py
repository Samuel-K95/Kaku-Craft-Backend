from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Product
from products.permissions import IsAdminOrSuperAdmin

from .models import Review, WishlistItem
from .serializers import (
	ReviewCreateSerializer,
	ReviewModerationSerializer,
	ReviewSerializer,
	WishlistAddSerializer,
	WishlistItemSerializer,
)


class WishlistListCreateView(APIView):
	def get(self, request):
		items = (
			WishlistItem.objects.filter(user=request.user)
			.select_related("product", "product__category")
			.prefetch_related("product__images")
		)
		return Response(WishlistItemSerializer(items, many=True).data)

	def post(self, request):
		serializer = WishlistAddSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		product = get_object_or_404(Product, pk=serializer.validated_data["product_id"])
		item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
		return Response(
			WishlistItemSerializer(item).data,
			status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
		)


class WishlistRemoveView(APIView):
	def delete(self, request, product_id):
		deleted, _ = WishlistItem.objects.filter(
			user=request.user, product_id=product_id
		).delete()
		if not deleted:
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
		return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewListCreateView(generics.ListCreateAPIView):
	def get_permissions(self):
		if self.request.method == "GET":
			return [AllowAny()]
		return [IsAuthenticated()]

	def get_serializer_class(self):
		if self.request.method == "POST":
			return ReviewCreateSerializer
		return ReviewSerializer

	def get_queryset(self):
		qs = Review.objects.select_related("user", "product", "order")
		product = self.request.query_params.get("product")
		if product:
			if product.isdigit():
				qs = qs.filter(product_id=product)
			else:
				qs = qs.filter(product__slug=product)

		user = self.request.user
		if getattr(user, "is_authenticated", False) and getattr(user, "role", None) in {
			"admin",
			"super_admin",
		}:
			return qs
		return qs.filter(is_approved=True)

	def create(self, request, *args, **kwargs):
		serializer = ReviewCreateSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		review = serializer.save(user=request.user, is_approved=False)
		return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ReviewDetailView(APIView):
	def get_object(self, request, pk):
		return get_object_or_404(Review, pk=pk, user=request.user)

	def get(self, request, pk):
		return Response(ReviewSerializer(self.get_object(request, pk)).data)

	def patch(self, request, pk):
		review = self.get_object(request, pk)
		rating = request.data.get("rating", review.rating)
		comment = request.data.get("comment", review.comment)
		if rating is not None:
			try:
				rating = int(rating)
			except (TypeError, ValueError) as exc:
				raise ValidationError({"rating": "Must be an integer 1-5."}) from exc
			if rating < 1 or rating > 5:
				raise ValidationError({"rating": "Must be between 1 and 5."})
		review.rating = rating
		review.comment = comment if comment is not None else review.comment
		review.is_approved = False
		review.save()
		return Response(ReviewSerializer(review).data)


class ReviewModerationView(APIView):
	permission_classes = [IsAdminOrSuperAdmin]

	def post(self, request, pk):
		review = get_object_or_404(Review, pk=pk)
		serializer = ReviewModerationSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		for field in ("is_approved", "is_flagged"):
			if field in serializer.validated_data:
				setattr(review, field, serializer.validated_data[field])
		review.save()
		return Response(ReviewSerializer(review).data)
