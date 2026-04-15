import sys
from plate_reader import ocr_plate
from database_manager import DatabaseManager

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 main.py path/to/image.jpg")
        return 1

    image_path = sys.argv[1]
    plate = ocr_plate(image_path)

    if not plate:
        print("No plate detected.")
        return 2

    with DatabaseManager() as db:
        inserted = db.insert_plate(plate, image_path)

    print(f"{'Saved' if inserted else 'Failed to save'} plate: {plate} (source: {image_path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())