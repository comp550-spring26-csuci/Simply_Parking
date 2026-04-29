import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is optional; env vars can also come from the shell
    pass


# ---- Stripe keys ----
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

# ---- Database credentials (same DB as users.py, just loaded safely) ----
DB_HOST = os.getenv("DB_HOST", "137.184.46.194")
DB_USER = os.getenv("DB_USER", "crsmcike_simplydb")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "crsmcikesimply_park")

# ---- Prices (all in cents — Stripe expects integers, never floats) ----
DAILY_PERMIT_PRICE_CENTS = 500         # $5.00
SEMESTER_PERMIT_PRICE_CENTS = 25000    # $250.00

# Pay-as-you-go matches the existing payasgocharge.py logic:
#   first 30 minutes free, then $0.50/min after that
PAYG_FREE_MINUTES = 30
PAYG_RATE_PER_MINUTE_CENTS = 50        # $0.50/min

# ---- Checkout redirect URLs ----
SUCCESS_URL = "https://checkout.stripe.dev/success?session_id={CHECKOUT_SESSION_ID}"
CANCEL_URL = "https://checkout.stripe.dev/cancel"
