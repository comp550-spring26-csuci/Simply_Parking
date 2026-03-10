import sys
from plate_reader import ocr_plate
from database_manager import DatabaseManager

DB_HOST = "127.0.0.1"
DB_NAME = "simply_park"
DB_USER = "simplydb"
DB_PASS = "Comp550SWE!"
DB_PORT = 3306

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py path/to/image.jpg")
        return 1

    image_path = sys.argv[1]
    plate = ocr_plate(image_path)

    if not plate:
        print("No plate detected.")
        return 2

    with DatabaseManager(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        port=DB_PORT,
    ) as db:
        inserted = db.insert_plate(plate, image_path)

    print(f"{'Saved' if inserted else 'Duplicate'} plate: {plate} (source: {image_path})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
