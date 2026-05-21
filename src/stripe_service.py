import os
import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

SUCCESS_URL = os.getenv(
    "STRIPE_SUCCESS_URL",
    "http://localhost:8765/success.html?session_id={CHECKOUT_SESSION_ID}",
)
CANCEL_URL = os.getenv(
    "STRIPE_CANCEL_URL",
    "http://localhost:8765/cancel.html",
)

DAILY_PERMIT_CENTS = 600
SEMESTER_PERMIT_CENTS = 25000


def _key():
    if not stripe.api_key:
        raise ValueError("Missing STRIPE_SECRET_KEY in .env")


def assert_test_mode():
    if not stripe.api_key:
        return
    if not stripe.api_key.startswith("sk_test_"):
        print("=" * 60)
        print("WARNING: STRIPE_SECRET_KEY is NOT a test key!")
        print("This means REAL CHARGES will be made.")
        print("For a college demo, use a sandbox/test key (sk_test_...).")
        print("=" * 60)


def _validate_checkout_url(url):
    if not url or not url.startswith("https://checkout.stripe.com/"):
        raise ValueError(f"Stripe did not return a real Checkout URL: {url!r}")


def _validate_return_urls():
    bad = "checkout.stripe.dev"
    if bad in SUCCESS_URL or bad in CANCEL_URL:
        raise ValueError(
            "STRIPE_SUCCESS_URL/STRIPE_CANCEL_URL must not use checkout.stripe.dev. "
            "Use http://localhost:8765/success.html or your own URL."
        )


def _success_url_with_type(payment_type):
    """Append payment_type so the success page can customize its headline."""
    sep = "&" if "?" in SUCCESS_URL else "?"
    return f"{SUCCESS_URL}{sep}type={payment_type}"


def _stripe_obj_to_dict(obj):
    """Safely convert StripeObject (or None) to a plain dict.

    On Python 3.14 with stripe-python 15.x, calling dict(stripe_object)
    raises KeyError(0). Use .to_dict() instead.
    """
    if obj is None:
        return {}
    if hasattr(obj, "to_dict"):
        try:
            return obj.to_dict()
        except Exception:
            pass
    try:
        return dict(obj)
    except Exception:
        return {}


def _checkout_session_to_tuple(session):
    _validate_checkout_url(session.url)
    return session.id, session.url


def create_daily_permit_checkout(user_id, plate):
    _key()
    _validate_return_urls()
    plate = (plate or "").strip().upper()
    if not user_id:
        raise ValueError("Missing user_id")
    if not plate:
        raise ValueError("Missing license plate")

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"Daily Parking Permit — {plate}"},
                "unit_amount": DAILY_PERMIT_CENTS,
            },
            "quantity": 1,
        }],
        metadata={
            "payment_type": "daily_permit",
            "user_id": str(user_id),
            "plate": plate,
            "amount": "6.00",
        },
        success_url=_success_url_with_type("daily"),
        cancel_url=CANCEL_URL,
    )
    return _checkout_session_to_tuple(session)


def create_semester_permit_checkout(user_id, plate, start_date, end_date):
    _key()
    _validate_return_urls()
    plate = (plate or "").strip().upper()
    if not user_id:
        raise ValueError("Missing user_id")
    if not plate:
        raise ValueError("Missing license plate")
    if not start_date or not end_date:
        raise ValueError("Missing start_date or end_date")

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"Semester Parking Permit — {plate}",
                    "description": f"Valid {start_date} to {end_date}",
                },
                "unit_amount": SEMESTER_PERMIT_CENTS,
            },
            "quantity": 1,
        }],
        metadata={
            "payment_type": "semester_permit",
            "user_id": str(user_id),
            "plate": plate,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "amount": "250.00",
        },
        success_url=_success_url_with_type("semester"),
        cancel_url=CANCEL_URL,
    )
    return _checkout_session_to_tuple(session)


def create_payg_checkout(user_id, plate, session_db_id, duration_minutes, amount):
    _key()
    _validate_return_urls()
    plate = (plate or "").strip().upper()
    cents = int(round(float(amount) * 100))
    if not plate:
        raise ValueError("Missing plate")
    if not session_db_id:
        raise ValueError("Missing session_db_id")
    if cents <= 0:
        raise ValueError("Amount must be > 0")

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"PAYG Parking Fee — {plate}",
                    "description": f"Duration: {duration_minutes} minutes",
                },
                "unit_amount": cents,
            },
            "quantity": 1,
        }],
        metadata={
            "payment_type": "payg",
            "user_id": str(user_id) if user_id else "",
            "plate": plate,
            "session_db_id": str(session_db_id),
            "duration_minutes": str(duration_minutes),
            "amount": f"{float(amount):.2f}",
        },
        success_url=_success_url_with_type("payg"),
        cancel_url=CANCEL_URL,
    )
    return _checkout_session_to_tuple(session)


def get_checkout_status(session_id):
    _key()
    if not session_id:
        raise ValueError("Missing session_id")

    session = stripe.checkout.Session.retrieve(session_id)
    metadata = _stripe_obj_to_dict(session.metadata)
    payment_intent = str(session.payment_intent) if session.payment_intent else None

    customer_email = None
    if session.customer_details is not None:
        try:
            customer_email = session.customer_details.email
        except AttributeError:
            customer_email = None

    return {
        "id": session.id,
        "payment_status": session.payment_status,
        "status": session.status,
        "amount_total": session.amount_total,
        "currency": session.currency,
        "payment_intent": payment_intent,
        "metadata": metadata,
        "customer_email": customer_email,
    }


def is_paid(session_id):
    return get_checkout_status(session_id)["payment_status"] == "paid"
