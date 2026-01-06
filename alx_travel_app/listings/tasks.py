from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

@shared_task
def send_booking_confirmation_email(email, booking_id):
    send_mail(
        "Booking Confirmation",
        f"Your booking with ID {booking_id} has been confirmed.",
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
