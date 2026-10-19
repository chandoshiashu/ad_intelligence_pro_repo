"""Clearly synthetic sample ads for local UI and API testing only."""


def sample_ads(brand: str, competitor: bool = False) -> list[dict]:
    if competitor:
        texts = [
            ("Make every craving count", "Discover something delicious today. Explore our menu."),
            ("Food that fits your day", "Find your favourites and enjoy a convenient order."),
            ("Your next meal, sorted", "Explore meals for every mood. Order today."),
            ("A little joy in every bite", "Discover new favourites with friends and family."),
        ]
    else:
        texts = [
            ("Your next favourite meal awaits", "Enjoy special offers and order your favourite food today."),
            ("Good food, great deals", "Save on selected meals. Check out today's offer."),
            ("Cravings, meet convenience", "Quick delivery and delicious choices, right at your doorstep."),
            ("Make room for something delicious", "Explore new meals and discover your next favourite."),
        ]
    return [
        {
            "advertiser_name": brand,
            "ad_archive_id": f"demo-{brand.lower().replace(' ', '-')}-{i+1}",
            "ad_text": body,
            "headline": headline,
            "start_date": None,
            "platforms": ["Instagram" if i % 2 == 0 else "Facebook"],
            "media_type": "unknown",
            "landing_page_url": None,
            "ad_library_url": None,
            "image_url": None,
            "source_verified": False,
        }
        for i, (headline, body) in enumerate(texts)
    ]
