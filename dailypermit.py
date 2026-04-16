def purchase_daily_permit(user_id, license_plate, permit_date):
    db = get_connection()
    cursor = db.cursor()

    sql = """
        INSERT INTO permits (user_id, permit_type, license_plate, permit_date)
        VALUES (%s, %s, %s, %s)
    """
    values = (user_id, 'daily', license_plate, permit_date)

    cursor.execute(sql, values)
    db.commit()

    cursor.close()
    db.close()
