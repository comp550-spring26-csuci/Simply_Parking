def init_schema(conn):
    create_plates_table(conn)
    create_users_table(conn)
    create_audit_logs_table(conn)
    create_vehicles_table(conn)
    create_issues_table(conn)
    create_notifications_table(conn)

def create_plates_table(conn):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS plates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                plate VARCHAR(32) NOT NULL,
                source_file VARCHAR(512),
                timestamp DATETIME NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        cur.close()

def create_users_table(conn):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(64) NOT NULL UNIQUE,
                password_hash VARCHAR(128) NOT NULL,
                role VARCHAR(32) NOT NULL,
                full_name VARCHAR(128),
                created_at DATETIME NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        cur.close()

def create_audit_logs_table(conn):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NULL,
                username VARCHAR(64),
                event_type VARCHAR(64) NOT NULL,
                details TEXT,
                created_at DATETIME NOT NULL,
                INDEX idx_event_type (event_type),
                INDEX idx_created_at (created_at)
            )
            """
        )
        conn.commit()
    finally:
        cur.close()

def create_vehicles_table(conn):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                plate VARCHAR(32) NOT NULL,
                make VARCHAR(64),
                model VARCHAR(64),
                color VARCHAR(32),
                created_at DATETIME NOT NULL,
                UNIQUE KEY unique_user_plate (user_id, plate),
                CONSTRAINT fk_vehicle_user
                    FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )
        conn.commit()
    finally:
        cur.close()

def create_issues_table(conn):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS issues (
                id INT AUTO_INCREMENT PRIMARY KEY,
                reported_by_user_id INT NOT NULL,
                reported_by_username VARCHAR(64) NOT NULL,
                location VARCHAR(128) NOT NULL,
                category VARCHAR(64) NOT NULL,
                priority VARCHAR(32) NOT NULL,
                description TEXT NOT NULL,
                status VARCHAR(32) NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (reported_by_user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )
        conn.commit()
    finally:
        cur.close()

def create_notifications_table(conn):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NULL,
                title VARCHAR(128) NOT NULL,
                message TEXT NOT NULL,
                notification_type VARCHAR(64) NOT NULL,
                is_read BOOLEAN NOT NULL DEFAULT FALSE,
                created_at DATETIME NOT NULL,
                INDEX idx_user_id (user_id),
                INDEX idx_is_read (is_read),
                INDEX idx_created_at (created_at)
            )
            """
        )
        conn.commit()
    finally:
        cur.close()