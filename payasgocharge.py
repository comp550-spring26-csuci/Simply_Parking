def end_parking_session(license_plate):
    db = get_connection()
    cursor = db.cursor()

    sql = """
        UPDATE parking_sessions
        SET exit_time = NOW(),
            total_minutes = TIMESTAMPDIFF(MINUTE, entry_time, NOW()),
            amount_due = CASE
                WHEN TIMESTAMPDIFF(MINUTE, entry_time, NOW()) > 30
                THEN (TIMESTAMPDIFF(MINUTE, entry_time, NOW()) - 30) * 0.50
                ELSE 0
            END
        WHERE license_plate = %s
          AND exit_time IS NULL
    """

    cursor.execute(sql, (license_plate,))
    db.commit()

    cursor.close()
    db.close()






