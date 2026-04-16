def register_vehicle(user_id, license_plate):
    db = get_connection()
    cursor = db.cursor()

    sql = """
        INSERT INTO vehicles (user_id, license_plate)
        VALUES (%s, %s)
    """

    cursor.execute(sql, (user_id, license_plate))
    db.commit()

    cursor.close()
    db.close()

