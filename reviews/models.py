from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from orders.models import Order
from products.models import Product


class WishlistItem(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="wishlist_items",
	)
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]
		constraints = [
			models.UniqueConstraint(fields=["user", "product"], name="uniq_wishlist_user_product"),
		]

	def __str__(self):
		return f"{self.user_id}:{self.product_id}"


class Review(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="reviews",
	)
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
	order = models.ForeignKey(
		Order,
		on_delete=models.CASCADE,
		related_name="reviews",
	)
	rating = models.PositiveSmallIntegerField(
		validators=[MinValueValidator(1), MaxValueValidator(5)]
	)
	comment = models.TextField(blank=True)
	is_approved = models.BooleanField(default=False)
	is_flagged = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]
		constraints = [
			models.UniqueConstraint(
				fields=["user", "product", "order"],
				name="uniq_review_per_order_product",
			),
		]
		indexes = [
			models.Index(fields=["product", "is_approved"]),
		]

	def __str__(self):
		return f"Review#{self.pk} product={self.product_id} rating={self.rating}"
