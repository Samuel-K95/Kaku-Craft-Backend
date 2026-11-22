"""Default ETB prices and production-day estimates by category slug."""

from __future__ import annotations

DEFAULT_PRICES_ETB: dict[str, int] = {
    "keychain-dolls": 200,
    "small-dolls": 450,
    "beanies": 350,
    "baby": 800,
    "handbags": 900,
    "scarves": 700,
    "gloves": 500,
    "socks": 450,
    "sweaters": 1200,
    "cardigans": 1800,
    "blankets": 2500,
}

DEFAULT_PRODUCTION_DAYS: dict[str, int] = {
    "keychain-dolls": 5,
    "small-dolls": 10,
    "beanies": 7,
    "baby": 10,
    "handbags": 12,
    "scarves": 8,
    "gloves": 7,
    "socks": 6,
    "sweaters": 16,
    "cardigans": 18,
    "blankets": 28,
}

SIZE_LABELS = ("Medium", "Large", "XL", "XXL")
DEFAULT_VARIANT_STOCK = 2


def price_for(category_slug: str, caption_price: int | None = None) -> int:
    if caption_price and caption_price > 0:
        return caption_price
    return DEFAULT_PRICES_ETB.get(category_slug, 1000)


def production_days_for(category_slug: str, override: int | None = None) -> int:
    if override and override > 0:
        return override
    return DEFAULT_PRODUCTION_DAYS.get(category_slug, 14)
