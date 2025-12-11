from __future__ annotations

from django.urls import path

from .views import (
    BookingListCreateAPIView,
    InitializeChapaPaymentAPIView,
    ListingListCreateAPIView,
    ReviewListCreateAPIView,
    VerifyChapaPaymentAPIView,
)

app_name = "listings"

urlpatterns = [
    path("listings/", ListingListCreateAPIView.as_view(), name="listing-list-create"),
    path("bookings/", BookingListCreateAPIView.as_view(), name="booking-list-create"),
    path("reviews/", ReviewListCreateAPIView.as_view(), name="review-list-create"),
    path(
        "payments/chapa/init/",
        InitializeChapaPaymentAPIView.as_view(),
        name="chapa-payment-init",
    ),
    path(
        "payments/chapa/verify/<str:tx_ref>/",
        VerifyChapaPaymentAPIView.as_view(),
        name="chapa-payment-verify",
    ),
]

