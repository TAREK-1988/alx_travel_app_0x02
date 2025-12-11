from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from .models import Listing


class ListingTests(TestCase):
    def test_create_listing(self) -> None:
        listing = Listing.objects.create(
            title="Test listing",
            description="Test description",
            price_per_night=100,
            location="Test city",
        )
        self.assertIsNotNone(listing.id)

    def test_list_listings_endpoint(self) -> None:
        Listing.objects.create(
            title="Test listing",
            description="Test description",
            price_per_night=100,
            location="Test city",
        )
        url = reverse("listings:listing-list-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
