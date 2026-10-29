from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek, TruncYear
from django.utils import timezone
from django.utils.dateparse import parse_date

from orders.models import CustomOrder, Order
from products.models import Product


def _parse_range(params):
	now = timezone.now()
	range_key = (params.get("range") or "monthly").lower()
	start = params.get("start")
	end = params.get("end")

	if start or end:
		start_date = parse_date(start) if start else None
		end_date = parse_date(end) if end else None
		start_dt = (
			timezone.make_aware(datetime.combine(start_date, time.min))
			if start_date
			else now - timedelta(days=30)
		)
		end_dt = (
			timezone.make_aware(datetime.combine(end_date, time.max))
			if end_date
			else now
		)
		return start_dt, end_dt, "custom"

	if range_key == "weekly":
		return now - timedelta(days=7), now, "weekly"
	if range_key == "yearly":
		return now - timedelta(days=365), now, "yearly"
	return now - timedelta(days=30), now, "monthly"


def _truncator(range_key: str):
	if range_key == "weekly":
		return TruncWeek
	if range_key == "yearly":
		return TruncYear
	if range_key == "custom":
		return TruncDate
	return TruncMonth


def build_analytics(params):
	start_dt, end_dt, range_key = _parse_range(params)
	orders = Order.objects.filter(created_at__gte=start_dt, created_at__lte=end_dt)
	completed = orders.filter(status=Order.Status.COMPLETED)
	revenue = completed.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")

	trunc = _truncator(range_key)
	timeseries = (
		orders.annotate(bucket=trunc("created_at"))
		.values("bucket")
		.annotate(orders=Count("id"), revenue=Sum("amount_paid"))
		.order_by("bucket")
	)

	popular_products = list(
		Product.objects.filter(is_active=True)
		.order_by("-sold_count", "-created_at")
		.values("id", "name", "slug", "sold_count", "price")[:10]
	)

	pending_custom = CustomOrder.objects.filter(
		status=CustomOrder.Status.PENDING_REVIEW
	).count()

	return {
		"range": range_key,
		"start": start_dt.isoformat(),
		"end": end_dt.isoformat(),
		"totals": {
			"orders": orders.count(),
			"completed_orders": completed.count(),
			"revenue": str(revenue),
			"pending_custom_orders": pending_custom,
		},
		"timeseries": [
			{
				"bucket": row["bucket"].isoformat() if row["bucket"] else None,
				"orders": row["orders"],
				"revenue": str(row["revenue"] or Decimal("0.00")),
			}
			for row in timeseries
		],
		"popular_products": popular_products,
	}
