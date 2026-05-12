import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ---- Stripe ----
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")


# ---- Database ----
DB_HOST = os.getenv("DB_HOST", "137.184.46.194")
DB_USER = os.getenv("DB_USER", "crsmcike_simplydb")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "crsmcike_simply_park")


# ---- Prices ----
DAILY_PERMIT_PRICE_CENTS = 600
SEMESTER_PERMIT_PRICE_CENTS = 25000

PAYG_FREE_MINUTES = 30
PAYG_RATE_PER_MINUTE_CENTS = 50


# ---- Stripe Redirect URLs ----
SUCCESS_URL = os.getenv(
    "STRIPE_SUCCESS_URL",
    "https://example.com/payment-success"
)

CANCEL_URL = os.getenv(
    "STRIPE_CANCEL_URL",
    "https://example.com/payment-cancel"
)