from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DiscountValidateView, DiscountViewSet

app_name = "discounts"

router = DefaultRouter()
router.register(r"items", DiscountViewSet, basename="discount")

urlpatterns = [
    path("validate/", DiscountValidateView.as_view(), name="validate"),
    path("", include(router.urls)),
]
