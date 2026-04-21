# all your imports
import mysql.connector

# connection function
def get_connection():
    ...

# ALL your functions
def register_vehicle(user_id, license_plate):
    ...

def register_semester_permit(user_id, license_plate, start_date, end_date):
    ...

def check_semester_access(license_plate):
    ...

def purchase_daily_permit(user_id, license_plate, permit_date):
    ...

def check_daily_access(license_plate):
    ...

def start_parking_session(license_plate):
    ...

def end_parking_session(license_plate):
    ...

def check_general_access(license_plate):
    ...
if __name__ == "__main__":
    register_vehicle(1, "ABC123")
    register_semester_permit(1, "ABC123", "2026-01-01", "2026-05-01")

    access = check_semester_access("ABC123")
    print("Semester access:", access)

    purchase_daily_permit(2, "XYZ789", "2026-04-12")
    print("Daily access:", check_daily_access("XYZ789"))

    start_parking_session("LMN456")
    end_parking_session("LMN456")
    print("General access:", check_general_access("LMN456"))
