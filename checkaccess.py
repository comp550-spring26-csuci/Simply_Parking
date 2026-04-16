def check_general_access(license_plate):
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT 'permit' AS access_type
        FROM permits
        WHERE license_plate = %s
          AND (
                (permit_type = 'semester' AND CURDATE() BETWEEN start_date AND end_d>
                OR
                (permit_type = 'daily' AND permit_date = CURDATE())
              )

        UNION

        SELECT 'pay_as_you_go' AS access_type
        FROM parking_sessions
        WHERE license_plate = %s
          AND exit_time IS NULL
    """

    cursor.execute(sql, (license_plate, license_plate))
    result = cursor.fetchall()

    cursor.close()
    db.close()

    return result

