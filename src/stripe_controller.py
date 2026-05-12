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

    created = app.db.create_daily_permit(
        user_id=user_id,
        plate=plate,
        amount=amount,
        stripe_session_id=info["id"],
        stripe_payment_intent_id=payment_intent,
    )
    if not created:
        return False, "Payment succeeded, but permit could not be saved. It may already exist for today."

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

    created = app.db.create_semester_permit(
        user_id=user_id,
        plate=plate,
        start_date=start_date,
        end_date=end_date,
        amount=amount,
        stripe_session_id=info["id"],
        stripe_payment_intent_id=payment_intent,
    )
    if not created:
        return False, "Payment succeeded, but semester permit could not be saved. Check for an overlapping active permit."

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

    created = app.db.create_payg_payment(
        user_id=user_id,
        plate=plate,
        duration_minutes=minutes,
        amount=amount,
        parking_session_id=session_db_id,
        stripe_session_id=info["id"],
        stripe_payment_intent_id=payment_intent,
    )
    if not created:
        return False, "Payment succeeded, but PAYG payment could not be saved."

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
