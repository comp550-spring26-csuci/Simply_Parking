# stripe_payments.py
# Simply Parking - Stripe payment functions
# Author: Param
#
# This file does all the Stripe and MySQL stuff. The Tkinter UI
# (stripe_ui.py) calls these functions to create checkouts, check
# payment status, and save permits/sessions to the database.

import stripe
import mysql.connector
from datetime import datetime, timedelta

# load all the settings from stripe_config.py
from stripe_config import (
    STRIPE_SECRET_KEY,
    DB_HOST, DB_USER, DB_PASSWORD, DB_NAME,
    DAILY_PERMIT_PRICE_CENTS, SEMESTER_PERMIT_PRICE_CENTS,
    PAYG_FREE_MINUTES, PAYG_RATE_PER_MINUTE_CENTS,
    SUCCESS_URL, CANCEL_URL,
)

# tell the stripe library our API key
stripe.api_key = STRIPE_SECRET_KEY


# helper function to connect to the database
def get_db():
    db = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )
    return db


# ----------- PERMIT PURCHASE (Daily and Semester) -----------

# creates a Stripe Checkout page for a permit
# returns the session id and the URL to open in browser
def create_permit_checkout(permit_type, license_plate, user_id):
    permit_type = permit_type.lower()

    # figure out the price based on permit type
    if permit_type == "daily":
        amount = DAILY_PERMIT_PRICE_CENTS
        name = "Daily Parking Permit"
    elif permit_type == "semester":
        amount = SEMESTER_PERMIT_PRICE_CENTS
        name = "Semester Parking Permit"
    else:
        # bad permit type, throw an error
        raise ValueError("Unknown permit type: " + permit_type)

    print("Creating Stripe checkout for", permit_type, "- $", amount/100)

    # call Stripe to make the checkout session
    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": name},
                "unit_amount": amount,
            },
            "quantity": 1,
        }],
        # store extra info we need later when payment is done
        metadata={
            "kind": "permit",
            "permit_type": permit_type,
            "user_id": str(user_id),
            "license_plate": license_plate,
        },
        success_url=SUCCESS_URL,
        cancel_url=CANCEL_URL,
    )

    return session.id, session.url


# checks Stripe to see if a session is paid yet
# returns a dictionary with the status info
def get_session_status(session_id):
    session = stripe.checkout.Session.retrieve(session_id)

    info = {
        "payment_status": session.payment_status,
        "status": session.status,
        "amount_total": session.amount_total,
        "payment_intent": session.payment_intent,
        "metadata": dict(session.metadata or {}),
    }
    return info


# called after Stripe says payment is done
# saves the permit row in the database
def activate_permit_after_payment(session_id):
    # double check that it's actually paid
    info = get_session_status(session_id)
    if info["payment_status"] != "paid":
        print("Payment is not paid yet, status =", info["payment_status"])
        return False

    # get the info we saved when we made the checkout
    meta = info["metadata"]
    permit_type = meta.get("permit_type")
    user_id = int(meta.get("user_id"))
    license_plate = meta.get("license_plate")
    pi_id = info["payment_intent"]

    # connect to the database
    db = get_db()
    cursor = db.cursor()

    try:
        # check if we already saved this permit (avoid duplicates)
        cursor.execute(
            "SELECT id FROM permits WHERE stripe_payment_intent_id = %s",
            (pi_id,)
        )
        if cursor.fetchone():
            print("Permit already exists for this payment, skipping")
            return False

        # insert daily permit
        if permit_type == "daily":
            sql = """
                INSERT INTO permits
                    (user_id, permit_type, license_plate, permit_date,
                     stripe_payment_intent_id, payment_status, amount_cents)
                VALUES (%s, 'daily', %s, CURDATE(), %s, 'paid', %s)
            """
            values = (user_id, license_plate, pi_id, info["amount_total"])
            cursor.execute(sql, values)

        # insert semester permit (good for 120 days)
        elif permit_type == "semester":
            start = datetime.now().date()
            end = start + timedelta(days=120)
            sql = """
                INSERT INTO permits
                    (user_id, permit_type, license_plate, start_date, end_date,
                     stripe_payment_intent_id, payment_status, amount_cents)
                VALUES (%s, 'semester', %s, %s, %s, %s, 'paid', %s)
            """
            values = (user_id, license_plate, start, end, pi_id,
                      info["amount_total"])
            cursor.execute(sql, values)

        else:
            print("Unknown permit type:", permit_type)
            return False

        # save the changes
        db.commit()
        print("Permit saved to database")
        return True

    except mysql.connector.Error as e:
        print("Database error:", e)
        return False

    finally:
        # always close the connection
        cursor.close()
        db.close()


# ----------- PAY-AS-YOU-GO EXIT -----------

# looks up the active parking session and calculates how much they owe
# returns (amount_cents, minutes, session_id) or (None, 0, None) if no session
def compute_payg_amount(license_plate):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # find the most recent open session for this plate
    sql = """
        SELECT id, TIMESTAMPDIFF(MINUTE, entry_time, NOW()) AS minutes
        FROM parking_sessions
        WHERE license_plate = %s AND exit_time IS NULL
        ORDER BY entry_time DESC
        LIMIT 1
    """
    cursor.execute(sql, (license_plate,))
    row = cursor.fetchone()
    cursor.close()
    db.close()

    # no active session found
    if row is None:
        return None, 0, None

    minutes = row["minutes"]
    if minutes is None:
        minutes = 0

    # first 30 mins are free, then $0.50/min
    billable_minutes = minutes - PAYG_FREE_MINUTES
    if billable_minutes < 0:
        billable_minutes = 0

    amount = billable_minutes * PAYG_RATE_PER_MINUTE_CENTS
    return amount, minutes, row["id"]


# creates a Stripe checkout for the exit fee
# returns (session_id, url, amount_cents, minutes)
def create_payg_exit_checkout(license_plate):
    amount, minutes, session_db_id = compute_payg_amount(license_plate)

    # case 1: no active session for this plate
    if amount is None:
        return None, None, 0, 0

    # case 2: under 30 min, no charge - just close the session
    if amount == 0:
        print("Free exit (under 30 min), closing session")
        db = get_db()
        cursor = db.cursor()
        try:
            sql = """
                UPDATE parking_sessions
                SET exit_time = NOW(),
                    total_minutes = %s,
                    amount_due = 0,
                    payment_status = 'paid'
                WHERE id = %s
            """
            cursor.execute(sql, (minutes, session_db_id))
            db.commit()
        finally:
            cursor.close()
            db.close()
        return None, None, 0, minutes

    # case 3: need to charge - make a Stripe checkout
    print("Creating exit fee checkout: $", amount/100, "for", minutes, "min")
    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "Parking - " + str(minutes) + " min"},
                "unit_amount": amount,
            },
            "quantity": 1,
        }],
        metadata={
            "kind": "payg_exit",
            "license_plate": license_plate,
            "parking_session_id": str(session_db_id),
            "minutes": str(minutes),
        },
        success_url=SUCCESS_URL,
        cancel_url=CANCEL_URL,
    )

    return session.id, session.url, amount, minutes


# called after the exit fee is paid
# closes out the parking session in the database
def finalize_payg_exit(session_id):
    # check it's actually paid
    info = get_session_status(session_id)
    if info["payment_status"] != "paid":
        print("Payment not paid yet")
        return False

    # get the info we saved earlier
    meta = info["metadata"]
    session_db_id = int(meta["parking_session_id"])
    minutes = int(meta["minutes"])
    amount_dollars = (info["amount_total"] or 0) / 100.0

    # update the session row
    db = get_db()
    cursor = db.cursor()

    try:
        sql = """
            UPDATE parking_sessions
            SET exit_time = NOW(),
                total_minutes = %s,
                amount_due = %s,
                stripe_payment_intent_id = %s,
                payment_status = 'paid'
            WHERE id = %s AND exit_time IS NULL
        """
        values = (minutes, amount_dollars, info["payment_intent"],
                  session_db_id)
        cursor.execute(sql, values)
        rows_changed = cursor.rowcount
        db.commit()

        if rows_changed > 0:
            print("Session closed in database")
            return True
        else:
            print("No session was updated (maybe already closed?)")
            return False

    finally:
        cursor.close()
        db.close()
