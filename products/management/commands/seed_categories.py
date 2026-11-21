"""
Management command: seed_categories
Seeds the standard product categories in PostgreSQL.
"""

from django.core.management.base import BaseCommand
from products.models import Category

CATEGORIES = [
    {"name": "Cardigans", "slug": "cardigans", "description": "Hand-knitted and crocheted artisan cardigans."},
    {"name": "Sweaters", "slug": "sweaters", "description": "Cozy bespoke wool sweaters and jumpers."},
    {"name": "Handbags", "slug": "handbags", "description": "Structured and slouchy hand-woven crochet bags."},
    {"name": "Beanies", "slug": "beanies", "description": "Warm artisanal beanies, berets, and winter hats."},
    {"name": "Small Dolls", "slug": "small-dolls", "description": "Intricate collectible handmade crochet dolls."},
    {"name": "Keychain Dolls", "slug": "keychain-dolls", "description": "Handcrafted miniature crochet keychain charms."},
    {"name": "Blankets", "slug": "blankets", "description": "Heirloom crochet throws and bed blankets."},
    {"name": "Scarves", "slug": "scarves", "description": "Soft textured crochet scarves and wraps."},
    {"name": "Gloves", "slug": "gloves", "description": "Fingerless and full-stitch wool gloves."},
    {"name": "Socks & Booties", "slug": "socks", "description": "Chunky knit socks and cozy crochet slippers."},
    {"name": "Baby Clothes", "slug": "baby", "description": "Gentle organic baby cardigans, hats, and sets."},
]


class Command(BaseCommand):
    help = "Seed standard product categories."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete and recreate all categories.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Reset existing categories."))

        created_count = 0
        for cat_data in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                slug=cat_data["slug"],
                defaults={
                    "name": cat_data["name"],
                    "description": cat_data["description"],
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✔ Created Category: {cat.name} ({cat.slug})"))
            else:
                self.stdout.write(f"  — Category exists: {cat.name} ({cat.slug})")

        self.stdout.write(self.style.SUCCESS(f"\nDone. Seeded {created_count} new categories (total: {Category.objects.count()})."))
