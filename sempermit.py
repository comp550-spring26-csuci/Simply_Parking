ef register_semester_permit(user_id, license_plate, start_date, end_date):
    db = get_connection()
    cursor = db.cursor()

    sql = """
        INSERT INTO permits (user_id, permit_type, license_plate, start_date, end_da>
        VALUES (%s, %s, %s, %s, %s)
    """
    values = (user_id, 'semester', license_plate, start_date, end_date)

    cursor.execute(sql, values)
    db.commit()

    cursor.close()
    db.close()


