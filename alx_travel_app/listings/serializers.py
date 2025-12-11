from __future__ import annotations

from rest_framework import serializers

from .models import Booking, Listing, Payment, Review


class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ("id", "title", "description", "price_per_night", "location")


class BookingSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.all(),
        source="listing",
        write_only=True,
    )

    class Meta:
        model = Booking
        fields = (
            "id",
            "listing",
            "listing_id",
            "user",
            "start_date",
            "end_date",
            "status",
            "created_at",
        )
        read_only_fields = ("status", "created_at")


class ReviewSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.all(),
        source="listing",
        write_only=True,
    )

    class Meta:
        model = Review
        fields = ("id", "listing", "listing_id", "user", "rating", "comment", "created_at")
        read_only_fields = ("created_at",)


class PaymentSerializer(serializers.ModelSerializer):
    booking = BookingSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "booking",
            "tx_ref",
            "chapa_reference",
            "amount",
            "currency",
            "customer_email",
            "customer_name",
            "status",
            "checkout_url",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "tx_ref",
            "chapa_reference",
            "status",
            "checkout_url",
            "created_at",
            "updated_at",
        )

