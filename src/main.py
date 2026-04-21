from capture import capture_image
from plate_reader import process_one_image
from database_manager import DatabaseManager


def main():
    image_path = capture_image()

    if image_path is None:
        print("No image captured.")
        return

    outputs = process_one_image(
        image_path,
        target_width=900,
        template_dir="templates_normalized"
    )

    final_plate_text = outputs.get("final_plate_text", "").strip()
    if not final_plate_text:
        final_plate_text = outputs.get("recognized_text", "").strip()

    print(f"Recognized text: {outputs.get('recognized_text', '')}")
    print(f"Final plate text: {final_plate_text}")

    if not final_plate_text:
        print("No plate text available to insert into database.")
        return

    try:
        with DatabaseManager() as db:
            ok = db.insert_plate(final_plate_text, image_path)

        if ok:
            print(f"Inserted into database: {final_plate_text}")
        else:
            print("Database insert failed.")

    except Exception as e:
        print(f"Database error: {e}")


if __name__ == "__main__":
    main()