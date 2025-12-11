from django.db import models


class Listing(models.Model):
    """
    Basic listing model representing a property that can be booked.
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class BookingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"


class Booking(models.Model):
    """
    Booking for a given listing. In a real system the `user` field would be a
    ForeignKey to the User model, but for this milestone a simple identifier
    keeps the example self-contained.
    """

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    user = models.CharField(
        max_length=255,
        help_text="Identifier of the customer making the booking.",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=16,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Booking #{self.id} for {self.listing.title}"

    @property
    def nights(self) -> int:
        """
        Returns the number of nights for this booking.
        If end_date is not after start_date, zero is returned.
        """
        delta = self.end_date - self.start_date
        return max(delta.days, 0)


class Review(models.Model):
    """
    Simple review model attached to a listing.
    """

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    user = models.CharField(
        max_length=255,
        help_text="Identifier of the customer writing the review.",
    )
    rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Rating from 1 (worst) to 5 (best).",
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Review for {self.listing.title} by {self.user}"


class PaymentStatus(models.TextChoices):
    """
    Payment lifecycle as tracked inside the application.
    """

    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"


class Payment(models.Model):
    """
    Tracks a payment attempt for a booking handled through the Chapa API.
    """

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="payment",
    )
    tx_ref = models.CharField(
        max_length=128,
        unique=True,
        help_text="Merchant transaction reference sent to Chapa (tx_ref).",
    )
    chapa_reference = models.CharField(
        max_length=128,
        blank=True,
        help_text="Chapa internal reference id (ref_id) returned by the API.",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount charged to the customer.",
    )
    currency = models.CharField(
        max_length=8,
        default="ETB",
        help_text="Transaction currency (e.g. ETB).",
    )
    status = models.CharField(
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    checkout_url = models.URLField(
        blank=True,
        help_text="Chapa hosted payment page URL the customer is redirected to.",
    )
    raw_initialize_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw JSON payload returned by Chapa on initialize.",
    )
    raw_verify_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw JSON payload returned by Chapa on verify.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Payment {self.tx_ref} for booking #{self.booking_id}"
