from datetime import datetime
from mysql.connector import Error

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def register_vehicle(conn, user_id, plate, make="", model="", color=""):
    plate = (plate or "").strip().upper()
    make = (make or "").strip()
    model = (model or "").strip()
    color = (color or "").strip()

    if not user_id or not plate:
        return False

    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO vehicles (user_id, plate, make, model, color, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, plate, make, model, color, now_str()),
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Register vehicle failed: {e}")
        return False
    finally:
        cur.close()

def fetch_user_vehicles(conn, user_id):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, plate, make, model, color, created_at
            FROM vehicles
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        return cur.fetchall()
    finally:
        cur.close()

def delete_vehicle(conn, vehicle_id, user_id):
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM vehicles WHERE id = %s AND user_id = %s",
            (vehicle_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    except Error as e:
        print(f"Delete vehicle failed: {e}")
        return False
    finally:
        cur.close()