from decimal import Decimal

from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models

from products.models import Product


class Cart(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="cart",
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Cart<{self.user_id}>"

	@property
	def total_price(self):
		return sum((item.subtotal for item in self.items.select_related("product")), Decimal("0.00"))

	@property
	def item_count(self):
		return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
	cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
	quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["cart", "product"], name="uniq_cart_product"),
		]

	def __str__(self):
		return f"{self.product_id} x{self.quantity}"

	@property
	def unit_price(self):
		return self.product.price

	@property
	def subtotal(self):
		return self.unit_price * self.quantity


class Order(models.Model):
	class Status(models.TextChoices):
		PENDING_PAYMENT = "pending_payment", "Pending Payment"
		PAYMENT_SUBMITTED = "payment_submitted", "Payment Submitted"
		PAYMENT_VERIFIED = "payment_verified", "Payment Verified"
		IN_PROGRESS = "in_progress", "In Progress"
		DELIVERED = "delivered", "Delivered"
		COMPLETED = "completed", "Completed"
		CANCELLED = "cancelled", "Cancelled"

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="orders",
	)
	status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING_PAYMENT)
	total_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
	amount_paid = models.DecimalField(
		max_digits=12,
		decimal_places=2,
		default=Decimal("0.00"),
		validators=[MinValueValidator(0)],
	)
	notes = models.TextField(blank=True)
	shipping_address = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["status"]),
			models.Index(fields=["created_at"]),
			models.Index(fields=["user", "status"]),
		]

	def __str__(self):
		return f"Order#{self.pk} ({self.status})"

	@property
	def remaining_amount(self):
		remaining = self.total_price - self.amount_paid
		return remaining if remaining > 0 else Decimal("0.00")

	@property
	def deposit_required(self):
		return (self.total_price * Decimal("0.50")).quantize(Decimal("0.01"))

	@property
	def has_minimum_deposit(self):
		return self.amount_paid >= self.deposit_required

	@property
	def is_fully_paid(self):
		return self.amount_paid >= self.total_price


class OrderItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
	product = models.ForeignKey(
		Product,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="order_items",
	)
	product_name = models.CharField(max_length=180)
	unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
	quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	line_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

	def __str__(self):
		return f"{self.product_name} x{self.quantity}"


class PaymentProof(models.Model):
	class VerificationStatus(models.TextChoices):
		PENDING = "pending", "Pending"
		APPROVED = "approved", "Approved"
		REJECTED = "rejected", "Rejected"

	class PaymentKind(models.TextChoices):
		DEPOSIT = "deposit", "Deposit"
		REMAINING = "remaining", "Remaining"
		FULL = "full", "Full"

	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payment_proofs")
	uploaded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="payment_proofs",
	)
	image = models.ImageField(
		upload_to="payment_proofs/",
		validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
	)
	amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
	kind = models.CharField(max_length=20, choices=PaymentKind.choices, default=PaymentKind.DEPOSIT)
	status = models.CharField(
		max_length=20,
		choices=VerificationStatus.choices,
		default=VerificationStatus.PENDING,
	)
	admin_note = models.TextField(blank=True)
	reviewed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="reviewed_payment_proofs",
	)
	reviewed_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"PaymentProof#{self.pk} order={self.order_id} ({self.status})"


class CustomOrder(models.Model):
	class Status(models.TextChoices):
		PENDING_REVIEW = "pending_review", "Pending Review"
		APPROVED = "approved", "Approved"
		REJECTED = "rejected", "Rejected"
		AWAITING_PAYMENT = "awaiting_payment", "Awaiting Payment"
		PAYMENT_SUBMITTED = "payment_submitted", "Payment Submitted"
		IN_PROGRESS = "in_progress", "In Progress"
		COMPLETED = "completed", "Completed"

	customer = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="custom_orders",
	)
	reference_image = models.ImageField(
		upload_to="custom_orders/",
		validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
	)
	description = models.TextField()
	quoted_price = models.DecimalField(
		max_digits=12,
		decimal_places=2,
		null=True,
		blank=True,
		validators=[MinValueValidator(0)],
	)
	amount_paid = models.DecimalField(
		max_digits=12,
		decimal_places=2,
		default=Decimal("0.00"),
		validators=[MinValueValidator(0)],
	)
	status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING_REVIEW)
	admin_note = models.TextField(blank=True)
	customer_confirmed = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["status"]),
			models.Index(fields=["customer", "status"]),
		]

	def __str__(self):
		return f"CustomOrder#{self.pk} ({self.status})"

	@property
	def remaining_amount(self):
		if self.quoted_price is None:
			return None
		remaining = self.quoted_price - self.amount_paid
		return remaining if remaining > 0 else Decimal("0.00")

	@property
	def deposit_required(self):
		if self.quoted_price is None:
			return None
		return (self.quoted_price * Decimal("0.50")).quantize(Decimal("0.01"))

	@property
	def has_minimum_deposit(self):
		deposit = self.deposit_required
		return deposit is not None and self.amount_paid >= deposit


class CustomOrderPaymentProof(models.Model):
	class VerificationStatus(models.TextChoices):
		PENDING = "pending", "Pending"
		APPROVED = "approved", "Approved"
		REJECTED = "rejected", "Rejected"

	custom_order = models.ForeignKey(
		CustomOrder,
		on_delete=models.CASCADE,
		related_name="payment_proofs",
	)
	uploaded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="custom_payment_proofs",
	)
	image = models.ImageField(
		upload_to="custom_payment_proofs/",
		validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
	)
	amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
	status = models.CharField(
		max_length=20,
		choices=VerificationStatus.choices,
		default=VerificationStatus.PENDING,
	)
	admin_note = models.TextField(blank=True)
	reviewed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="reviewed_custom_payment_proofs",
	)
	reviewed_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]
