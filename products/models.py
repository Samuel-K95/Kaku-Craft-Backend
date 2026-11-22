from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


def validate_social_links(value):
	if value is None:
		return
	if not isinstance(value, dict):
		raise ValidationError("Social links must be a JSON object of key-value pairs.")

	for key, link in value.items():
		if not isinstance(key, str) or not key.strip():
			raise ValidationError("Each social link key must be a non-empty string.")
		if not isinstance(link, str) or not link.strip():
			raise ValidationError("Each social link value must be a non-empty URL string.")
		if not (link.startswith("http://") or link.startswith("https://")):
			raise ValidationError("Social link values must start with http:// or https://.")


def build_unique_slug(model_class, value, current_pk=None):
	base_slug = slugify(value) or "item"
	slug = base_slug
	counter = 2

	while model_class.objects.filter(slug=slug).exclude(pk=current_pk).exists():
		slug = f"{base_slug}-{counter}"
		counter += 1

	return slug


class Category(models.Model):
	name = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(max_length=140, unique=True, blank=True)
	description = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["name"]

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = build_unique_slug(Category, self.name, self.pk)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class Product(models.Model):
	class ProductStatus(models.TextChoices):
		DRAFT = "draft", "Draft"
		ACTIVE = "active", "Active"
		OUT_OF_STOCK = "out_of_stock", "Out of Stock"
		ARCHIVED = "archived", "Archived"

	category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
	name = models.CharField(max_length=180)
	slug = models.SlugField(max_length=200, unique=True, blank=True)
	description = models.TextField()
	price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
	size = models.CharField(max_length=80, blank=True)
	stock_quantity = models.PositiveIntegerField(default=0)
	production_days = models.PositiveIntegerField(default=14)
	source_key = models.CharField(max_length=120, unique=True, null=True, blank=True)
	status = models.CharField(max_length=20, choices=ProductStatus.choices, default=ProductStatus.ACTIVE)
	is_active = models.BooleanField(default=True)
	sold_count = models.PositiveIntegerField(default=0)
	social_links = models.JSONField(default=dict, blank=True, validators=[validate_social_links])
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["is_active", "status"]),
			models.Index(fields=["price"]),
			models.Index(fields=["created_at"]),
			models.Index(fields=["sold_count"]),
		]

	def sync_stock_status(self):
		"""Keep status in sync with total stock when not draft/archived."""
		if self.status in (self.ProductStatus.DRAFT, self.ProductStatus.ARCHIVED):
			return
		self.status = (
			self.ProductStatus.ACTIVE
			if self.stock_quantity > 0
			else self.ProductStatus.OUT_OF_STOCK
		)

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = build_unique_slug(Product, self.name, self.pk)
		self.sync_stock_status()
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class ProductSizeVariant(models.Model):
	class Size(models.TextChoices):
		MEDIUM = "Medium", "Medium"
		LARGE = "Large", "Large"
		XL = "XL", "XL"
		XXL = "XXL", "XXL"

	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="size_variants")
	size = models.CharField(max_length=16, choices=Size.choices)
	stock_quantity = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ["id"]
		unique_together = [("product", "size")]

	def __str__(self):
		return f"{self.product.name} — {self.size}"


class ProductImage(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
	image = models.ImageField(upload_to="products/")
	alt_text = models.CharField(max_length=180, blank=True)
	is_primary = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-is_primary", "id"]

	def __str__(self):
		return f"{self.product.name} image"
