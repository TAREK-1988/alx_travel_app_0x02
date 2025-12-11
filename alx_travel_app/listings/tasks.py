from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .models import Booking, Payment


@shared_task
def send_payment_confirmation_email(booking_id: int, payment_id: int) -> None:
    booking = Booking.objects.get(pk=booking_id)
    payment = Payment.objects.get(pk=payment_id)

    subject = "Your booking payment was successful"
    message = (
        f"Thank you for your payment.\n\n"
        f"Booking ID: {booking.id}\n"
        f"Listing: {booking.listing.title}\n"
        f"Transaction reference: {payment.tx_ref}\n"
        f"Amount: {payment.amount} {payment.currency}\n"
    )

    recipient = payment.customer_email
    if not recipient:
        return

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        fail_silently=True,
    )

