"""Upsert analyzed products into Django product tables."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from django.core.files import File
from django.db import transaction

from products.models import Category, Product, ProductImage, ProductSizeVariant

from .price_rules import DEFAULT_VARIANT_STOCK, SIZE_LABELS


def _ensure_category(slug: str) -> Category:
    pretty = slug.replace("-", " ").title()
    cat, _ = Category.objects.get_or_create(
        slug=slug,
        defaults={
            "name": pretty,
            "description": f"Handcrafted {pretty} from ከኩ craft.",
            "is_active": True,
        },
    )
    if not cat.is_active:
        cat.is_active = True
        cat.save(update_fields=["is_active", "updated_at"])
    return cat


def _sync_size_variants(product: Product, per_size_stock: int = DEFAULT_VARIANT_STOCK) -> int:
    total = 0
    for size in SIZE_LABELS:
        variant, _ = ProductSizeVariant.objects.update_or_create(
            product=product,
            size=size,
            defaults={"stock_quantity": per_size_stock},
        )
        total += variant.stock_quantity
    ProductSizeVariant.objects.filter(product=product).exclude(size__in=SIZE_LABELS).delete()
    return total


def _replace_images(product: Product, export_dir: Path, photo_rel_paths: list[str], alt: str) -> int:
    """Replace product images with export photos (idempotent re-run)."""
    product.images.all().delete()
    count = 0
    for index, rel in enumerate(photo_rel_paths):
        abs_path = (export_dir / rel).resolve()
        if not abs_path.exists():
            continue
        with abs_path.open("rb") as fh:
            image = ProductImage(
                product=product,
                alt_text=alt[:180],
                is_primary=(index == 0),
            )
            image.image.save(abs_path.name, File(fh), save=True)
        count += 1
    return count


@transaction.atomic
def upsert_product(item: dict[str, Any], export_dir: Path, dry_run: bool = False) -> dict[str, Any]:
    source_key = item["source_key"]
    category = _ensure_category(item["category_slug"])
    name = item["name"]
    description = item.get("description") or f"{name} — handmade by ከኩ craft."
    price = Decimal(str(item.get("price") or 0))
    production_days = int(item.get("production_days") or 14)
    size_note = item.get("size_note") or ", ".join(SIZE_LABELS)
    social_links = item.get("social_links") or {"telegram": "https://t.me/keku_craft"}
    photos = item.get("photo_rel_paths") or []

    existing = Product.objects.filter(source_key=source_key).first()
    action = "update" if existing else "create"

    if dry_run:
        return {
            "action": action,
            "source_key": source_key,
            "name": name,
            "category": category.slug,
            "price": str(price),
            "photos": len(photos),
        }

    if existing:
        product = existing
        product.category = category
        product.name = name
        product.description = description
        product.price = price
        product.size = size_note
        product.production_days = production_days
        product.social_links = social_links
        product.is_active = True
    else:
        product = Product(
            category=category,
            name=name,
            description=description,
            price=price,
            size=size_note,
            production_days=production_days,
            source_key=source_key,
            social_links=social_links,
            is_active=True,
        )

    total_stock = _sync_size_variants(product) if product.pk else DEFAULT_VARIANT_STOCK * len(SIZE_LABELS)
    # Save product first if new so variants/images can attach
    if not product.pk:
        product.stock_quantity = total_stock
        product.save()
        total_stock = _sync_size_variants(product)
    product.stock_quantity = total_stock
    product.save()

    image_count = _replace_images(product, export_dir, photos, alt=name)
    return {
        "action": action,
        "source_key": source_key,
        "slug": product.slug,
        "name": product.name,
        "category": category.slug,
        "price": str(product.price),
        "stock_quantity": product.stock_quantity,
        "images": image_count,
    }


def upsert_manifest(manifest: dict[str, Any], dry_run: bool = False) -> list[dict[str, Any]]:
    export_dir = Path(manifest["export_dir"]).resolve()
    results = []
    for item in manifest.get("products") or []:
        results.append(upsert_product(item, export_dir, dry_run=dry_run))
    return results
