from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.validators import validate_image_upload

from .models import Category, Product, ProductImage
from .permissions import IsAdminOrSuperAdmin
from .serializers import (
	CategorySerializer,
	ProductImageSerializer,
	ProductImageWriteSerializer,
	ProductSerializer,
	ProductWriteSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer
	lookup_field = "slug"

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [AllowAny()]
		return [IsAdminOrSuperAdmin()]

	def get_queryset(self):
		queryset = Category.objects.all()
		if self.action in ["list", "retrieve"]:
			queryset = queryset.filter(is_active=True)
		return queryset


class ProductViewSet(viewsets.ModelViewSet):
	queryset = Product.objects.select_related("category").prefetch_related(
		"images", "size_variants"
	)
	lookup_field = "slug"

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [AllowAny()]
		return [IsAdminOrSuperAdmin()]

	def get_serializer_class(self):
		if self.action in ["create", "update", "partial_update"]:
			return ProductWriteSerializer
		return ProductSerializer

	def get_queryset(self):
		queryset = Product.objects.select_related("category").prefetch_related(
			"images", "size_variants"
		)

		if self.action in ["list", "retrieve"]:
			# Include out_of_stock so pre-order items remain shoppable.
			queryset = queryset.filter(
				is_active=True,
				status__in=[
					Product.ProductStatus.ACTIVE,
					Product.ProductStatus.OUT_OF_STOCK,
				],
			)

		category = self.request.query_params.get("category")
		if category:
			if category.isdigit():
				queryset = queryset.filter(category_id=int(category))
			else:
				queryset = queryset.filter(category__slug=category)

		min_price = self.request.query_params.get("min_price")
		if min_price:
			try:
				queryset = queryset.filter(price__gte=Decimal(min_price))
			except InvalidOperation as exc:
				raise ValidationError({"min_price": "Must be a valid decimal number."}) from exc

		max_price = self.request.query_params.get("max_price")
		if max_price:
			try:
				queryset = queryset.filter(price__lte=Decimal(max_price))
			except InvalidOperation as exc:
				raise ValidationError({"max_price": "Must be a valid decimal number."}) from exc

		search = self.request.query_params.get("search")
		if search:
			search_term = search.strip()
			queryset = queryset.filter(
				Q(name__icontains=search_term)
				| Q(description__icontains=search_term)
				| Q(category__name__icontains=search_term)
				| Q(category__slug__icontains=search_term)
				| Q(size__icontains=search_term)
			).distinct()

		ordering = self.request.query_params.get("ordering")
		if ordering == "price":
			queryset = queryset.order_by("price")
		elif ordering == "-price":
			queryset = queryset.order_by("-price")
		elif ordering == "popularity":
			queryset = queryset.order_by("-sold_count", "-created_at")
		else:
			queryset = queryset.order_by("-created_at")

		return queryset


class ProductImageUploadView(APIView):
	permission_classes = [IsAdminOrSuperAdmin]
	parser_classes = [MultiPartParser, FormParser]

	def post(self, request, slug):
		product = get_object_or_404(Product, slug=slug)
		serializer = ProductImageWriteSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		validate_image_upload(serializer.validated_data["image"])
		image = serializer.save(product=product)
		if image.is_primary:
			ProductImage.objects.filter(product=product).exclude(pk=image.pk).update(
				is_primary=False
			)
		return Response(ProductImageSerializer(image).data, status=status.HTTP_201_CREATED)

	def delete(self, request, slug, image_id):
		product = get_object_or_404(Product, slug=slug)
		image = get_object_or_404(ProductImage, pk=image_id, product=product)
		image.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)
