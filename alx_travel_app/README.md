# alx_travel_app_0x02 – Milestone 4: Payment Integration with Chapa API

## Overview

This project is a Django-based travel booking API built for the ALX backend curriculum.

Milestone **4** focuses on integrating the **Chapa Payment Gateway** to allow users
to pay for their bookings securely. The implementation covers:

- Initializing payments via Chapa
- Redirecting users to a hosted payment page
- Verifying payment status after checkout
- Persisting payment information in the database
- Sending confirmation emails via Celery after successful payments

The code in this repository assumes previous milestones have already set up:

- Django project structure
- REST API with Django REST Framework
- Database configuration (PostgreSQL)
- Celery and a running message broker (e.g. RabbitMQ or Redis)

---

## Tech Stack

- **Django**
- **Django REST Framework**
- **PostgreSQL**
- **Celery** (for background tasks)
- **RabbitMQ / Redis** (Celery broker)
- **Chapa Payment Gateway**
- **requests** (for calling Chapa API)

---

## Project Structure (Relevant Parts)

```text
alx_travel_app_0x02/
└── alx_travel_app/
    ├── manage.py
    ├── requirement.txt
    ├── .env.example
    ├── README.md
    ├── alx_travel_app/
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── celery.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── listings/
        ├── __init__.py
        ├── admin.py
        ├── apps.py
        ├── migrations/
        │   └── __init__.py
        ├── models.py      # Listing, Booking, Review, Payment
        ├── serializers.py
        ├── tasks.py       # Celery payment email (optional file)
        ├── urls.py
        └── views.py       # Payment initialization + verification
