import traceback
import stripe_service


def _require_paid_session(session_id, expected_type):
    info = stripe_service.get_checkout_status(session_id)
    if info["payment_status"] != "paid":
        return None, False, "Payment is not completed yet."

    meta = info.get("metadata") or {}
    if meta.get("payment_type") != expected_type:
        return None, False, f"Wrong payment type. Expected {expected_type}."

    payment_intent = info.get("payment_intent")
    if not payment_intent:
        return None, False, "Stripe payment_intent is missing. Try verifying again in a moment."

    return info, True, "OK"


def _log_db_failure(where, payment_intent, exc=None):
    """Print full diagnostic info to terminal so the real cause is visible."""
    print()
    print("=" * 70)
    print(f"DB WRITE FAILED in {where}")
    print(f"  Stripe payment_intent: {payment_intent}")
    if exc is not None:
        print(f"  Exception type: {type(exc).__name__}")
        print(f"  Exception: {exc!r}")
        if hasattr(exc, "errno"):
            print(f"  MySQL errno: {exc.errno}")
        if hasattr(exc, "msg"):
            print(f"  MySQL msg: {exc.msg}")
        print("Full traceback:")
        traceback.print_exc()
    else:
        print("  (no exception - the DB function returned False without raising)")
        print("  Check the terminal for 'Create ... failed:' lines printed by the db module.")
    print("=" * 70)
    print()


def activate_daily_permit_after_payment(app, session_id):
    info, ok, msg = _require_paid_session(session_id, "daily_permit")
    if not ok:
        return False, msg

    meta = info["metadata"]
    user_id = int(meta["user_id"])
    plate = meta["plate"].strip().upper()
    amount = float(meta.get("amount", "6.00"))
    payment_intent = info["payment_intent"]

    if app.db.daily_payment_exists(payment_intent):
        return True, f"Daily permit for {plate} was already activated."

    try:
        created = app.db.create_daily_permit(
            user_id=user_id,
            plate=plate,
            amount=amount,
            stripe_session_id=info["id"],
            stripe_payment_intent_id=payment_intent,
        )
    except Exception as e:
        _log_db_failure("create_daily_permit", payment_intent, e)
        return False, f"Payment succeeded, but DB write failed: {type(e).__name__}: {e}"

    if not created:
        _log_db_failure("create_daily_permit", payment_intent)
        # Check what's actually in the DB so we can give a real message.
        if app.db.daily_payment_exists(payment_intent):
            return True, f"Daily permit for {plate} was already activated."
        return False, ("Payment succeeded, but the database refused the insert. "
                       "Check the terminal for the real MySQL error (look for "
                       "'Create daily permit failed:'). Most common cause: "
                       "missing default value on a column.")

    username = app.current_user["username"] if app.current_user else None
    app.db.add_log("stripe_daily_permit_paid", f"Plate={plate},amount=${amount:.2f},pi={payment_intent}",
                   user_id=user_id, username=username)
    app.db.create_notification("Daily Permit Purchased",
        f"Daily permit activated for {plate}. Amount: ${amount:.2f}.",
        notification_type="purchase", user_id=user_id)
    return True, f"Daily permit activated for {plate}."


def activate_semester_permit_after_payment(app, session_id):
    info, ok, msg = _require_paid_session(session_id, "semester_permit")
    if not ok:
        return False, msg

    meta = info["metadata"]
    user_id = int(meta["user_id"])
    plate = meta["plate"].strip().upper()
    start_date = meta["start_date"]
    end_date = meta["end_date"]
    amount = float(meta.get("amount", "250.00"))
    payment_intent = info["payment_intent"]

    if app.db.semester_payment_exists(payment_intent):
        return True, f"Semester permit for {plate} was already activated."

    if not app.db.user_owns_vehicle(user_id, plate):
        return False, "Payment succeeded, but this plate is not registered to the user. Contact support."

    try:
        created = app.db.create_semester_permit(
            user_id=user_id,
            plate=plate,
            start_date=start_date,
            end_date=end_date,
            amount=amount,
            stripe_session_id=info["id"],
            stripe_payment_intent_id=payment_intent,
        )
    except Exception as e:
        _log_db_failure("create_semester_permit", payment_intent, e)
        return False, f"Payment succeeded, but DB write failed: {type(e).__name__}: {e}"

    if not created:
        _log_db_failure("create_semester_permit", payment_intent)
        if app.db.semester_payment_exists(payment_intent):
            return True, f"Semester permit for {plate} was already activated."
        # Look for the actual cause and give a specific message
        if app.db.has_active_semester_permit_for_plate(user_id, plate):
            return False, (f"Payment succeeded, but {plate} already has an active "
                           f"semester permit. Contact support to refund.")
        return False, ("Payment succeeded, but the database refused the insert. "
                       "Check the terminal for the real MySQL error (look for "
                       "'Create semester permit failed:'). Most common cause: "
                       "missing default value on the 'status' column - run: "
                       "ALTER TABLE semester_permits MODIFY COLUMN status "
                       "VARCHAR(32) NOT NULL DEFAULT 'active';")

    username = app.current_user["username"] if app.current_user else None
    app.db.add_log("stripe_semester_permit_paid", f"Plate={plate},amount=${amount:.2f},pi={payment_intent}",
                   user_id=user_id, username=username)
    app.db.create_notification("Semester Permit Purchased",
        f"Semester permit activated for {plate}. Valid {start_date} to {end_date}.",
        notification_type="purchase", user_id=user_id)
    return True, f"Semester permit activated for {plate}.\nValid: {start_date} → {end_date}"


def finalize_payg_after_payment(app, session_id):
    info, ok, msg = _require_paid_session(session_id, "payg")
    if not ok:
        return False, msg

    meta = info["metadata"]
    user_id = int(meta["user_id"]) if meta.get("user_id") else None
    plate = meta["plate"].strip().upper()
    session_db_id = int(meta["session_db_id"])
    minutes = int(meta["duration_minutes"])
    amount = float(meta["amount"])
    payment_intent = info["payment_intent"]

    if app.db.payg_payment_exists(payment_intent):
        return True, "Exit payment was already processed. Drive safely!"

    # Re-check the parking session before closing so an old Checkout Session cannot close the wrong flow.
    active = app.db.fetch_active_session_by_plate(plate)
    if not active:
        return False, "Payment succeeded, but no active parking session exists for this plate. Contact support."
    active_session_id = int(active[0])
    if active_session_id != session_db_id:
        return False, "Payment succeeded, but the parking session changed. Contact support."

    try:
        created = app.db.create_payg_payment(
            user_id=user_id,
            plate=plate,
            duration_minutes=minutes,
            amount=amount,
            parking_session_id=session_db_id,
            stripe_session_id=info["id"],
            stripe_payment_intent_id=payment_intent,
        )
    except Exception as e:
        _log_db_failure("create_payg_payment", payment_intent, e)
        return False, f"Payment succeeded, but DB write failed: {type(e).__name__}: {e}"

    if not created:
        _log_db_failure("create_payg_payment", payment_intent)
        if app.db.payg_payment_exists(payment_intent):
            return True, "Exit payment was already processed. Drive safely!"
        return False, ("Payment succeeded, but PAYG payment could not be saved. "
                       "Check the terminal for the real MySQL error.")

    if not app.db.close_session(session_db_id, amount):
        return False, "Payment saved, but the parking session could not be closed."

    username = app.current_user.get("username", "guest") if app.current_user else "guest"
    app.db.add_log("stripe_payg_paid", f"Plate={plate},duration={minutes}min,amount=${amount:.2f},pi={payment_intent}",
                   user_id=user_id, username=username)
    if user_id:
        app.db.create_notification("PAYG Payment Completed",
            f"Exit payment for {plate}. Duration: {minutes} min. Amount: ${amount:.2f}.",
            notification_type="purchase", user_id=user_id)
    return True, "Exit payment complete. Drive safely!"
