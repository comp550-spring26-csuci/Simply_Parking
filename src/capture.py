import cv2
from pathlib import Path
from datetime import datetime
from plate_reader import process_one_image

CASCADE_PATH = "/usr/share/opencv4/haarcascades/haarcascade_russian_plate_number.xml"
CAPTURE_DIR = Path("captures")

MIN_PLATE_WIDTH = 180
MIN_PLATE_HEIGHT = 60
SHARPNESS_THRESHOLD = 80.0
REQUIRED_SHARP_FRAMES = 5


def ensure_capture_dir():
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)


def capture_filename():
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return CAPTURE_DIR / f"plate_{ts}.jpg"


def sharpness_score(gray_image):
    return cv2.Laplacian(gray_image, cv2.CV_64F).var()


def capture_image():
    camera_index = 0
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"Error: Could not access camera at index {camera_index}.")
        return None

    ensure_capture_dir()
    sharp_frames = 0

    # --- Camera Settings ---
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
    cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
    cap.set(cv2.CAP_PROP_EXPOSURE, -6)

    print("Camera opened successfully.")
    print("Click on the webcam window, then press 'q' or Esc to quit.")

    plate_cascade = cv2.CascadeClassifier(CASCADE_PATH)

    if plate_cascade.empty():
        print(f"Error: Could not load cascade file at {CASCADE_PATH}")
        cap.release()
        return

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("Error: Could not read frame from camera.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            plates = plate_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(60, 20)
            )

            best_plate = None
            best_area = 0

            for (x, y, w, h) in plates:
                area = w * h
                if area > best_area:
                    best_area = area
                    best_plate = (x, y, w, h)

            if best_plate is not None:
                x, y, w, h = best_plate

                if w >= MIN_PLATE_WIDTH and h >= MIN_PLATE_HEIGHT:

                    plate_crop_gray = gray[y:y + h, x:x + w]
                    score = sharpness_score(plate_crop_gray)

                    if score >= SHARPNESS_THRESHOLD:
                        sharp_frames += 1
                    else:
                        sharp_frames = 0

                    if sharp_frames >= REQUIRED_SHARP_FRAMES:
                        save_path = capture_filename()
                        cv2.imwrite(str(save_path), frame)
                        print(f"Saved image: {save_path}")
                        return str(save_path)
                else:
                  sharp_frames = 0
            else:
                sharp_frames = 0

            cv2.imshow("Webcam Feed", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == 27:
                print("Exiting and releasing camera...")
                return None

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released. Windows closed.")


if __name__ == "__main__":
    capture_image()