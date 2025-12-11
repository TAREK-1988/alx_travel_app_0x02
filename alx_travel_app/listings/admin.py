from __future__ import annotations

from django.contrib import admin

from .models import Booking, Listing, Payment, Review


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "location", "price_per_night", "created_at")
    search_fields = ("title", "location")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "listing", "user", "start_date", "end_date", "status")
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("user", "listing__title")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "listing", "user", "rating", "created_at")
    list_filter = ("rating",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "booking",
        "tx_ref",
        "amount",
        "currency",
        "customer_email",
        "status",
        "created_at",
    )
    list_filter = ("status", "currency")
    search_fields = ("tx_ref", "customer_email")

