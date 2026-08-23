import os
from pathlib import Path

import stripe
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
stripe.api_key = os.environ["SOVEREIGN_STRIPE_KEY"]

CATALOG = [
    {
        "emergent_product_id": "professional_licence",
        "name": "Sovereign Quant — Professional Licence (Annual)",
        "tax_code": "txcd_10103001",
        "prices": [
            {"lookup_key": "professional_annual", "amount": 49900, "currency": "usd", "interval": "year"},
        ],
    },
    {
        "emergent_product_id": "institutional_licence",
        "name": "Sovereign Quant — Institutional Licence (Annual)",
        "tax_code": "txcd_10103001",
        "prices": [
            {"lookup_key": "institutional_annual", "amount": 199900, "currency": "usd", "interval": "year"},
        ],
    },
]


def ensure_tax_settings():
    s = stripe.tax.Settings.retrieve()
    if s.head_office and getattr(s.head_office, "address", None):
        return
    stripe.tax.Settings.modify(
        head_office={"address": {
            "country": "US", "line1": "1 Sovereign Way", "city": "New York",
            "state": "NY", "postal_code": "10007",
        }},
        defaults={"tax_behavior": "exclusive"},
    )


def get_or_create_product(entry):
    for p in stripe.Product.list(active=True).auto_paging_iter():
        if p.to_dict().get("metadata", {}).get("emergent_product_id") == entry["emergent_product_id"]:
            return p
    return stripe.Product.create(
        name=entry["name"], tax_code=entry.get("tax_code"),
        metadata={"managed_by": "emergent", "emergent_product_id": entry["emergent_product_id"]},
    )


def ensure_price(product, p):
    existing = stripe.Price.list(lookup_keys=[p["lookup_key"]], active=True, limit=1).data
    if existing and (existing[0].unit_amount != p["amount"] or existing[0].currency != p["currency"]):
        stripe.Price.modify(existing[0].id, active=False)
        existing = []
    if not existing:
        kwargs = dict(
            product=product.id, unit_amount=p["amount"], currency=p["currency"],
            lookup_key=p["lookup_key"], transfer_lookup_key=True,
        )
        if p.get("interval"):
            kwargs["recurring"] = {"interval": p["interval"]}
        stripe.Price.create(**kwargs)


if __name__ == "__main__":
    account = stripe.Account.retrieve()
    print("account:", account["id"], "country:", account["country"], "charges_enabled:", account["charges_enabled"])
    for entry in CATALOG:
        product = get_or_create_product(entry)
        for price in entry["prices"]:
            ensure_price(product, price)
        print("ok:", entry["name"])
