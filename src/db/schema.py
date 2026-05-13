def init_schema(conn):
    _run(conn, """CREATE TABLE IF NOT EXISTS plates (
        id INT AUTO_INCREMENT PRIMARY KEY,
        plate VARCHAR(32) NOT NULL,
        source_file VARCHAR(512),
        timestamp DATETIME NOT NULL)""")
    _run(conn, """CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(64) NOT NULL UNIQUE,
        password_hash VARCHAR(128) NOT NULL,
        role VARCHAR(32) NOT NULL,
        full_name VARCHAR(128),
        created_at DATETIME NOT NULL)""")
    _run(conn, """CREATE TABLE IF NOT EXISTS audit_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NULL, username VARCHAR(64),
        event_type VARCHAR(64) NOT NULL, details TEXT,
        created_at DATETIME NOT NULL,
        INDEX idx_event_type (event_type), INDEX idx_created_at (created_at))""")
    _run(conn, """CREATE TABLE IF NOT EXISTS vehicles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL, plate VARCHAR(32) NOT NULL,
        make VARCHAR(64), model VARCHAR(64), color VARCHAR(32),
        created_at DATETIME NOT NULL,
        UNIQUE KEY unique_user_plate (user_id, plate),
        CONSTRAINT fk_vehicle_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)""")
    _run(conn, """CREATE TABLE IF NOT EXISTS issues (
        id INT AUTO_INCREMENT PRIMARY KEY,
        reported_by_user_id INT NOT NULL, reported_by_username VARCHAR(64) NOT NULL,
        location VARCHAR(128) NOT NULL, category VARCHAR(64) NOT NULL,
        priority VARCHAR(32) NOT NULL, description TEXT NOT NULL,
        status VARCHAR(32) NOT NULL, created_at DATETIME NOT NULL,
        FOREIGN KEY (reported_by_user_id) REFERENCES users(id) ON DELETE CASCADE)""")
    _run(conn, """CREATE TABLE IF NOT EXISTS notifications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NULL, title VARCHAR(128) NOT NULL, message TEXT NOT NULL,
        notification_type VARCHAR(64) NOT NULL,
        is_read BOOLEAN NOT NULL DEFAULT FALSE, created_at DATETIME NOT NULL,
        INDEX idx_user_id (user_id), INDEX idx_is_read (is_read), INDEX idx_created_at (created_at))""")
    _run(conn, """CREATE TABLE IF NOT EXISTS daily_permits (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL, plate VARCHAR(32) NOT NULL,
        permit_date DATE NOT NULL, amount DECIMAL(6,2) NOT NULL DEFAULT 6.00,
        stripe_session_id VARCHAR(255) NULL,
        stripe_payment_intent_id VARCHAR(255) NULL,
        created_at DATETIME NOT NULL,
        INDEX idx_daily_user_date (user_id, permit_date),
        UNIQUE KEY unique_user_plate_day (user_id, plate, permit_date),
        UNIQUE KEY uniq_daily_stripe_pi (stripe_payment_intent_id))""")
    _run(conn, """CREATE TABLE IF NOT EXISTS semester_permits (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL, plate VARCHAR(32) NOT NULL,
        start_date DATE NOT NULL, end_date DATE NOT NULL,
        amount DECIMAL(6,2) NOT NULL DEFAULT 0.00,
        stripe_session_id VARCHAR(255) NULL,
        stripe_payment_intent_id VARCHAR(255) NULL,
        created_at DATETIME NOT NULL,
        INDEX idx_sem_user_plate_dates (user_id, plate, start_date, end_date),
        UNIQUE KEY uniq_semester_stripe_pi (stripe_payment_intent_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)""")
    _run(conn, """CREATE TABLE IF NOT EXISTS payg_payments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NULL, plate VARCHAR(32) NOT NULL,
        parking_session_id INT NULL,
        duration_minutes INT NOT NULL, amount DECIMAL(6,2) NOT NULL,
        stripe_session_id VARCHAR(255) NULL,
        stripe_payment_intent_id VARCHAR(255) NULL,
        created_at DATETIME NOT NULL,
        UNIQUE KEY uniq_payg_stripe_pi (stripe_payment_intent_id),
        INDEX idx_payg_session (parking_session_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL)""")
    _run(conn, """CREATE TABLE IF NOT EXISTS parking_sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        plate VARCHAR(32) NOT NULL, entry_time DATETIME NOT NULL,
        exit_time DATETIME NULL, status VARCHAR(32) NOT NULL DEFAULT 'active',
        amount_due DECIMAL(6,2) NOT NULL DEFAULT 0.00, created_at DATETIME NOT NULL,
        INDEX idx_plate_status (plate, status), INDEX idx_entry_time (entry_time))""")

    _upgrade_existing_schema(conn)
    print("Schema ready.")


def _run(conn, sql):
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
    finally:
        cur.close()


def _column_exists(conn, table, column):
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME=%s
        """, (table, column))
        return cur.fetchone()[0] > 0
    finally:
        cur.close()


def _index_exists(conn, table, index_name):
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME=%s AND INDEX_NAME=%s
        """, (table, index_name))
        return cur.fetchone()[0] > 0
    finally:
        cur.close()


def _add_column_if_missing(conn, table, column, definition):
    if not _column_exists(conn, table, column):
        _run(conn, f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _add_unique_if_missing(conn, table, index_name, columns):
    if not _index_exists(conn, table, index_name):
        _run(conn, f"ALTER TABLE {table} ADD UNIQUE KEY {index_name} ({columns})")


def _add_index_if_missing(conn, table, index_name, columns):
    if not _index_exists(conn, table, index_name):
        _run(conn, f"ALTER TABLE {table} ADD INDEX {index_name} ({columns})")


def _upgrade_existing_schema(conn):
    # Makes old databases compatible without dropping data.
    for table in ("daily_permits", "semester_permits", "payg_payments"):
        _add_column_if_missing(conn, table, "stripe_session_id", "VARCHAR(255) NULL")
        _add_column_if_missing(conn, table, "stripe_payment_intent_id", "VARCHAR(255) NULL")

    _add_column_if_missing(conn, "payg_payments", "parking_session_id", "INT NULL")

    _add_unique_if_missing(conn, "daily_permits", "uniq_daily_stripe_pi", "stripe_payment_intent_id")
    _add_unique_if_missing(conn, "semester_permits", "uniq_semester_stripe_pi", "stripe_payment_intent_id")
    _add_unique_if_missing(conn, "payg_payments", "uniq_payg_stripe_pi", "stripe_payment_intent_id")
    _add_index_if_missing(conn, "semester_permits", "idx_sem_user_plate_dates", "user_id, plate, start_date, end_date")
    _add_index_if_missing(conn, "payg_payments", "idx_payg_session", "parking_session_id")
