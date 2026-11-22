from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.models import Product

from .models import Cart, CartItem, CustomOrder, Order, OrderItem, PaymentProof


ALLOWED_ORDER_TRANSITIONS = {
	Order.Status.PENDING_PAYMENT: {
		Order.Status.PAYMENT_SUBMITTED,
		Order.Status.CANCELLED,
	},
	Order.Status.PAYMENT_SUBMITTED: {
		Order.Status.PAYMENT_VERIFIED,
		Order.Status.PENDING_PAYMENT,
		Order.Status.CANCELLED,
	},
	Order.Status.PAYMENT_VERIFIED: {
		Order.Status.IN_PROGRESS,
		Order.Status.CANCELLED,
	},
	Order.Status.IN_PROGRESS: {
		Order.Status.DELIVERED,
		Order.Status.CANCELLED,
	},
	Order.Status.DELIVERED: {
		Order.Status.COMPLETED,
	},
	Order.Status.COMPLETED: set(),
	Order.Status.CANCELLED: set(),
}


def get_or_create_cart(user):
	cart, _ = Cart.objects.get_or_create(user=user)
	return cart


def add_to_cart(user, product_id, quantity=1):
	if quantity < 1:
		raise ValidationError({"quantity": "Quantity must be at least 1."})

	try:
		product = Product.objects.get(
			pk=product_id,
			is_active=True,
			status=Product.ProductStatus.ACTIVE,
		)
	except Product.DoesNotExist as exc:
		raise ValidationError({"product_id": "Product not found or unavailable."}) from exc

	cart = get_or_create_cart(user)
	item, created = CartItem.objects.get_or_create(
		cart=cart,
		product=product,
		defaults={"quantity": quantity},
	)
	if not created:
		item.quantity += quantity
		item.save(update_fields=["quantity", "updated_at"])
	return item


@transaction.atomic
def create_order_from_cart(user, *, shipping_address="", notes="", discount_code=""):
	cart = get_or_create_cart(user)
	items = list(cart.items.select_related("product"))
	if not items:
		raise ValidationError({"cart": "Cart is empty."})

	for item in items:
		product = item.product
		if not product.is_active or product.status != Product.ProductStatus.ACTIVE:
			raise ValidationError(
				{"cart": f"Product '{product.name}' is no longer available."}
			)

	discount = None
	if discount_code:
		from discounts.services import compute_line_discount, get_active_discount

		discount = get_active_discount(discount_code)

	order_items = []
	total = Decimal("0.00")
	for item in items:
		unit = item.product.price
		if discount:
			unit = (unit - compute_line_discount(discount, unit, item.product_id)).quantize(
				Decimal("0.01")
			)
		line_total = (unit * item.quantity).quantize(Decimal("0.01"))
		total += line_total
		order_items.append(
			OrderItem(
				order=None,  # set after create
				product=item.product,
				product_name=item.product.name,
				unit_price=unit,
				quantity=item.quantity,
				line_total=line_total,
			)
		)

	note_bits = [notes or ""]
	if discount:
		note_bits.append(f"Discount applied: {discount.code}")
	order = Order.objects.create(
		user=user,
		total_price=total,
		amount_paid=Decimal("0.00"),
		shipping_address=shipping_address or "",
		notes="\n".join(b for b in note_bits if b).strip(),
		status=Order.Status.PENDING_PAYMENT,
	)

	for oi in order_items:
		oi.order = order
	OrderItem.objects.bulk_create(order_items)
	cart.items.all().delete()
	return order


def assert_order_transition(order, new_status):
	allowed = ALLOWED_ORDER_TRANSITIONS.get(order.status, set())
	if new_status not in allowed:
		raise ValidationError(
			{
				"status": (
					f"Cannot move order from '{order.status}' to '{new_status}'."
				)
			}
		)


@transaction.atomic
def apply_payment_proof_decision(proof, *, approved, reviewer, admin_note=""):
	if proof.status != PaymentProof.VerificationStatus.PENDING:
		raise ValidationError({"status": "This payment proof was already reviewed."})

	order = Order.objects.select_for_update().get(pk=proof.order_id)
	proof.reviewed_by = reviewer
	proof.reviewed_at = timezone.now()
	proof.admin_note = admin_note or ""

	if approved:
		proof.status = PaymentProof.VerificationStatus.APPROVED
		proof.save(update_fields=["status", "reviewed_by", "reviewed_at", "admin_note"])

		order.amount_paid = (order.amount_paid + proof.amount).quantize(Decimal("0.01"))
		update_fields = ["amount_paid", "updated_at"]

		if order.status == Order.Status.PAYMENT_SUBMITTED:
			assert_order_transition(order, Order.Status.PAYMENT_VERIFIED)
			order.status = Order.Status.PAYMENT_VERIFIED
			update_fields.append("status")

		if order.has_minimum_deposit and order.status == Order.Status.PAYMENT_VERIFIED:
			assert_order_transition(order, Order.Status.IN_PROGRESS)
			order.status = Order.Status.IN_PROGRESS
			update_fields.append("status")

		if order.is_fully_paid and order.status == Order.Status.DELIVERED:
			assert_order_transition(order, Order.Status.COMPLETED)
			order.status = Order.Status.COMPLETED
			update_fields.append("status")

		order.save(update_fields=list(dict.fromkeys(update_fields)))
	else:
		proof.status = PaymentProof.VerificationStatus.REJECTED
		proof.save(update_fields=["status", "reviewed_by", "reviewed_at", "admin_note"])
		if order.status == Order.Status.PAYMENT_SUBMITTED:
			order.status = Order.Status.PENDING_PAYMENT
			order.save(update_fields=["status", "updated_at"])

	return proof


@transaction.atomic
def mark_order_delivered(order):
	assert_order_transition(order, Order.Status.DELIVERED)
	order.status = Order.Status.DELIVERED
	order.save(update_fields=["status", "updated_at"])
	if order.is_fully_paid:
		assert_order_transition(order, Order.Status.COMPLETED)
		order.status = Order.Status.COMPLETED
		order.save(update_fields=["status", "updated_at"])
	return order


def _bump_sold_counts(order):
	from django.db.models import F

	for item in order.items.select_related("product"):
		if item.product_id:
			Product.objects.filter(pk=item.product_id).update(
				sold_count=F("sold_count") + item.quantity
			)


@transaction.atomic
def complete_order_if_paid(order):
	if order.status != Order.Status.DELIVERED:
		raise ValidationError({"status": "Order must be delivered before completion."})
	if not order.is_fully_paid:
		raise ValidationError(
			{"amount_paid": "Order must be fully paid before completion."}
		)
	assert_order_transition(order, Order.Status.COMPLETED)
	order.status = Order.Status.COMPLETED
	order.save(update_fields=["status", "updated_at"])
	_bump_sold_counts(order)
	return order


def custom_order_deposit_ok(custom_order: CustomOrder) -> bool:
	return custom_order.has_minimum_deposit
