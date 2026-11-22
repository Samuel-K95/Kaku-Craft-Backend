from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Product
from products.permissions import IsAdminOrSuperAdmin

from .models import Discount
from .serializers import DiscountSerializer, DiscountValidateSerializer
from .services import get_active_discount, preview_discount


class DiscountViewSet(viewsets.ModelViewSet):
    queryset = Discount.objects.prefetch_related("products").all()
    serializer_class = DiscountSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
    lookup_field = "pk"


class DiscountValidateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DiscountValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        discount = get_active_discount(serializer.validated_data["code"])
        product_ids = serializer.validated_data.get("product_ids") or []
        products = {
            p.id: p
            for p in Product.objects.filter(id__in=product_ids, is_active=True)
        }
        lines = [
            (pid, products[pid].price, 1)
            for pid in product_ids
            if pid in products
        ]
        if not lines and product_ids:
            return Response(
                {"detail": "No matching products for preview."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not lines:
            return Response(
                {
                    "code": discount.code,
                    "name": discount.name,
                    "discount_type": discount.discount_type,
                    "value": discount.value,
                    "valid": True,
                }
            )
        return Response(preview_discount(discount, lines))
