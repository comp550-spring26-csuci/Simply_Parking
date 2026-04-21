def check_semester_access(license_plate):
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT * FROM permits
        WHERE license_plate = %s
          AND permit_type = 'semester'
          AND CURDATE() BETWEEN start_date AND end_date
    """

    cursor.execute(sql, (license_plate,))
    result = cursor.fetchone()

    cursor.close()
    db.close()

    return result
