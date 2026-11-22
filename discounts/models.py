from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from products.models import Product


class Discount(models.Model):
    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Percent"
        AMOUNT = "amount", "Fixed amount"

    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=40, unique=True)
    discount_type = models.CharField(
        max_length=20, choices=DiscountType.choices, default=DiscountType.PERCENT
    )
    value = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    applies_to_all = models.BooleanField(default=False)
    products = models.ManyToManyField(Product, blank=True, related_name="discounts")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-starts_at"]

    def __str__(self):
        return f"{self.code} ({self.name})"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.discount_type == self.DiscountType.PERCENT and self.value > 100:
            raise ValidationError({"value": "Percent discount cannot exceed 100."})
        if self.ends_at and self.starts_at and self.ends_at < self.starts_at:
            raise ValidationError({"ends_at": "End must be after start."})

    @property
    def is_currently_valid(self):
        now = timezone.now()
        return (
            self.is_active
            and self.starts_at <= now <= self.ends_at
        )

    def applies_to_product(self, product_id: int) -> bool:
        if self.applies_to_all:
            return True
        return self.products.filter(pk=product_id).exists()
