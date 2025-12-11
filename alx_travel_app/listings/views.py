import logging
import uuid
from decimal import Decimal

import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking, BookingStatus, Payment, PaymentStatus

logger = logging.getLogger(__name__)

# Celery task is optional – if the module does not exist we simply log.
try:
    from .tasks import send_payment_confirmation_email
except Exception:  # noqa: BLE001
    send_payment_confirmation_email = None


def _get_chapa_secret_key() -> str:
    """
    Reads the Chapa secret key from Django settings. Raises a clear error
    if it is not configured.
    """
    secret = getattr(settings, "CHAPA_SECRET_KEY", None)
    if not secret:
        raise RuntimeError("CHAPA_SECRET_KEY is not configured in settings.")
    return secret


def _get_chapa_base_url() -> str:
    """
    Returns the Chapa base URL. By default uses the production/sandbox
    endpoint: https://api.chapa.co/v1
    """
    return getattr(settings, "CHAPA_BASE_URL", "https://api.chapa.co/v1")


def _calculate_booking_amount(booking: Booking) -> Decimal:
    """
    Calculates the amount to charge for a booking based on the
    number of nights and the listing price per night.
    """
    nights = booking.nights or 1
    price_per_night = booking.listing.price_per_night
    amount = price_per_night * nights
    # Normalize to 2 decimal places
    return amount.quantize(Decimal("0.01"))


class InitializeChapaPaymentAPIView(APIView):
    """
    POST /api/payments/chapa/init/

    Initializes a Chapa payment for an existing booking and returns
    the hosted checkout URL to the client.

    Expected request payload:
    {
        "booking_id": 1,
        "email": "customer@example.com",
        "first_name": "John",      # optional
        "last_name": "Doe"         # optional
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        booking_id = request.data.get("booking_id")
        email = request.data.get("email")
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")

        if not booking_id:
            return Response(
                {"detail": "booking_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking = get_object_or_404(Booking, pk=booking_id)

        # Fallback to authenticated user data if available
        if not email:
            email = getattr(request.user, "email", None)

        if not email:
            return Response(
                {
                    "detail": "Customer email is required either in the payload or from the authenticated user."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not first_name:
            first_name = getattr(request.user, "first_name", "") or "Customer"
        if not last_name:
            last_name = getattr(request.user, "last_name", "") or "Booking"

        # Prevent duplicate successful payments for the same booking
        try:
            existing_payment = booking.payment
        except Payment.DoesNotExist:
            existing_payment = None

        if existing_payment and existing_payment.status == PaymentStatus.SUCCESS:
            return Response(
                {
                    "detail": "This booking already has a successful payment.",
                    "tx_ref": existing_payment.tx_ref,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = _calculate_booking_amount(booking)
        tx_ref = f"booking-{booking.id}-{uuid.uuid4().hex[:8]}"

        callback_url = getattr(
            settings,
            "CHAPA_CALLBACK_URL",
            "https://example.com/api/payments/chapa/callback/",
        )
        return_url = getattr(
            settings,
            "CHAPA_RETURN_URL",
            "https://example.com/payments/complete/",
        )

        payload = {
            "amount": str(amount),
            "currency": getattr(settings, "CHAPA_CURRENCY", "ETB"),
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": tx_ref,
            "callback_url": callback_url,
            "return_url": return_url,
            "customization": {
                "title": "Travel booking payment",
                "description": f"Payment for booking #{booking.id} on {booking.listing.title}",
            },
        }

        secret_key = _get_chapa_secret_key()
        base_url = _get_chapa_base_url()

        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                f"{base_url}/transaction/initialize",
                json=payload,
                headers=headers,
                timeout=30,
            )
        except requests.RequestException as exc:
            logger.exception("Error while initializing payment with Chapa: %s", exc)
            return Response(
                {
                    "detail": "Could not reach Chapa payment gateway. Please try again later."
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if response.status_code not in (200, 201):
            logger.error(
                "Chapa initialize returned non-success HTTP status. "
                "status=%s, body=%s",
                response.status_code,
                response.text,
            )
            return Response(
                {"detail": "Failed to initialize payment with Chapa."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        data = response.json()
        if data.get("status") != "success" or "data" not in data:
            logger.error("Unexpected Chapa initialize payload: %s", data)
            return Response(
                {"detail": "Unexpected response from Chapa while initializing payment."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        chapa_data = data["data"]
        checkout_url = chapa_data.get("checkout_url", "")
        chapa_reference = chapa_data.get("reference", "")
        currency = chapa_data.get("currency") or payload["currency"]

        payment = Payment.objects.create(
            booking=booking,
            tx_ref=tx_ref,
            chapa_reference=chapa_reference,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            checkout_url=checkout_url,
            raw_initialize_response=data,
        )

        # Booking is now in a pending payment state
        booking.status = BookingStatus.PENDING
        booking.save(update_fields=["status"])

        return Response(
            {
                "message": "Payment initialized successfully.",
                "checkout_url": payment.checkout_url,
                "tx_ref": payment.tx_ref,
                "booking_id": booking.id,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "status": payment.status,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyChapaPaymentAPIView(APIView):
    """
    GET /api/payments/chapa/verify/<tx_ref>/

    Verifies a Chapa payment using the tx_ref that was used
    during initialization. Updates the Payment and Booking records
    based on the gateway response.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, tx_ref: str, *args, **kwargs):
        payment = get_object_or_404(Payment, tx_ref=tx_ref)

        base_url = _get_chapa_base_url()
        secret_key = _get_chapa_secret_key()

        url = f"{base_url}/transaction/verify/{payment.tx_ref}"
        headers = {
            "Authorization": f"Bearer {secret_key}",
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException as exc:
            logger.exception("Error while verifying Chapa payment: %s", exc)
            return Response(
                {"detail": "Could not verify payment with Chapa at this time."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if response.status_code != 200:
            logger.error(
                "Chapa verify returned non-success HTTP status. "
                "status=%s, body=%s",
                response.status_code,
                response.text,
            )
            return Response(
                {"detail": "Failed to verify payment with Chapa."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        data = response.json()
        payment.raw_verify_response = data

        chapa_status = data.get("status")
        chapa_data = data.get("data") or {}
        chapa_tx_status = chapa_data.get("status")

        if chapa_status == "success" and chapa_tx_status == "success":
            # Mark payment as successful
            payment.status = PaymentStatus.SUCCESS
            payment.chapa_reference = (
                chapa_data.get("reference") or payment.chapa_reference
            )
            payment.save(
                update_fields=[
                    "status",
                    "chapa_reference",
                    "raw_verify_response",
                    "updated_at",
                ]
            )

            # Mark booking as confirmed
            booking = payment.booking
            booking.status = BookingStatus.CONFIRMED
            booking.save(update_fields=["status"])

            # Enqueue confirmation email if Celery task is available
            if send_payment_confirmation_email is not None:
                try:
                    send_payment_confirmation_email.delay(
                        booking_id=booking.id,
                        tx_ref=payment.tx_ref,
                    )
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "Failed to enqueue payment confirmation email for booking %s",
                        booking.id,
                    )

            return Response(
                {
                    "message": "Payment verified successfully.",
                    "status": payment.status,
                    "booking_id": payment.booking_id,
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                    "chapa_reference": payment.chapa_reference,
                },
                status=status.HTTP_200_OK,
            )

        # Payment failed or still pending
        payment.status = PaymentStatus.FAILED
        payment.save(
            update_fields=[
                "status",
                "raw_verify_response",
                "updated_at",
            ]
        )

        # Keep booking in pending or allow your business logic to cancel it
        return Response(
            {
                "message": "Payment verification failed or not successful.",
                "status": payment.status,
                "booking_id": payment.booking_id,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "raw_chapa_status": chapa_tx_status,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
