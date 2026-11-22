import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Discount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("code", models.SlugField(max_length=40, unique=True)),
                (
                    "discount_type",
                    models.CharField(
                        choices=[("percent", "Percent"), ("amount", "Fixed amount")],
                        default="percent",
                        max_length=20,
                    ),
                ),
                (
                    "value",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("applies_to_all", models.BooleanField(default=False)),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "products",
                    models.ManyToManyField(blank=True, related_name="discounts", to="products.product"),
                ),
            ],
            options={
                "ordering": ["-starts_at"],
            },
        ),
    ]
