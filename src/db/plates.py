from datetime import datetime
from db.parking_sessions import create_session_if_not_active
from mysql.connector import Error
from db.logs import add_log

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def insert_plate(conn, plate, source_file, actor_user_id=None, actor_username=None):
    plate = (plate or "").strip().upper()
    source_file = (source_file or "").strip()

    if not plate:
        return False

    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO plates (plate, source_file, timestamp)
            VALUES (%s, %s, %s)
            """,
            (plate, source_file, now_str()),
        )
        conn.commit()
        create_session_if_not_active(conn, plate)

        add_log(
            conn,
            event_type="plate_entry_added",
            details=f"Plate={plate}, source_file={source_file}",
            user_id=actor_user_id,
            username=actor_username,
        )
        return True
    except Error as e:
        print(f"Insert failed: {e}")
        return False
    finally:
        cur.close()

def fetch_all(conn, limit=50):
    sql = "SELECT id, plate, source_file, timestamp FROM plates ORDER BY timestamp DESC"
    params = ()

    if isinstance(limit, int) and limit > 0:
        sql += " LIMIT %s"
        params = (limit,)

    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()

def update_plate_entry(conn, record_id, plate, source_file="", actor_user_id=None, actor_username=None):
    plate = (plate or "").strip().upper()
    source_file = (source_file or "").strip()

    if not record_id or not plate:
        return False

    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE plates
            SET plate = %s, source_file = %s
            WHERE id = %s
            """,
            (plate, source_file, record_id),
        )

        if cur.rowcount > 0:
            add_log(
                conn,
                event_type="plate_entry_updated",
                details=f"Record ID={record_id}, plate={plate}, source_file={source_file}",
                user_id=actor_user_id,
                username=actor_username,
            )
            return True
        return False
    except Error as e:
        print(f"Update plate failed: {e}")
        return False
    finally:
        cur.close()

def delete_plate_entry(conn, record_id, actor_user_id=None, actor_username=None):
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM plates WHERE id = %s", (record_id,))
        if cur.rowcount > 0:
            add_log(
                conn,
                event_type="plate_entry_deleted",
                details=f"Record ID={record_id}",
                user_id=actor_user_id,
                username=actor_username,
            )
            return True
        return False
    except Error as e:
        print(f"Delete plate failed: {e}")
        return False
    finally:
        cur.close()
    

def fetch_latest_plate_session(conn, plate):
    plate = (plate or "").strip().upper()

    if not plate:
        return None

    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, plate, source_file, timestamp
            FROM plates
            WHERE plate = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (plate,),
        )
        return cur.fetchone()
    finally:
        cur.close()