from decimal import Decimal

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Discount


def get_active_discount(code: str) -> Discount:
    code = (code or "").strip()
    if not code:
        raise ValidationError({"discount_code": "Discount code is required."})
    try:
        discount = Discount.objects.prefetch_related("products").get(code__iexact=code)
    except Discount.DoesNotExist as exc:
        raise ValidationError({"discount_code": "Invalid discount code."}) from exc
    now = timezone.now()
    if not discount.is_active or not (discount.starts_at <= now <= discount.ends_at):
        raise ValidationError({"discount_code": "This discount is not active."})
    return discount


def compute_line_discount(discount: Discount, unit_price: Decimal, product_id: int) -> Decimal:
    if not discount.applies_to_product(product_id):
        return Decimal("0.00")
    if discount.discount_type == Discount.DiscountType.PERCENT:
        return (unit_price * discount.value / Decimal("100")).quantize(Decimal("0.01"))
    return min(unit_price, discount.value).quantize(Decimal("0.01"))


def preview_discount(discount: Discount, lines: list[tuple[int, Decimal, int]]) -> dict:
    """
    lines: list of (product_id, unit_price, quantity)
    """
    subtotal = Decimal("0.00")
    savings = Decimal("0.00")
    for product_id, unit_price, qty in lines:
        line = unit_price * qty
        subtotal += line
        per_unit = compute_line_discount(discount, unit_price, product_id)
        savings += per_unit * qty
    savings = min(savings, subtotal).quantize(Decimal("0.01"))
    return {
        "code": discount.code,
        "name": discount.name,
        "discount_type": discount.discount_type,
        "value": discount.value,
        "subtotal": subtotal,
        "savings": savings,
        "total": (subtotal - savings).quantize(Decimal("0.01")),
    }
