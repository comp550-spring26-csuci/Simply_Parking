#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2


SAVE_DIR = Path.home() / "simplyPark" / "testing" / "images"
CASCADE_PATH = "/usr/share/opencv4/haarcascades/haarcascade_russian_plate_number.xml"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def timestamped_name() -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return SAVE_DIR / f"im-test{ts}.jpg"


def main() -> int:
    ensure_dir(SAVE_DIR)

    if not os.path.exists(CASCADE_PATH):
        print(f"Plate cascade not found: {CASCADE_PATH}")
        print("Install it with: sudo apt install opencv-data")
        return 1

    cascade = cv2.CascadeClassifier(CASCADE_PATH)
    if cascade.empty():
        print(f"Failed to load plate cascade classifier from: {CASCADE_PATH}")
        return 1

    camera_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"Could not open webcam at index {camera_index}.")
        return 1

    print("Watching webcam for a plate. Press q to quit.")
    last_capture = 0.0
    cooldown_seconds = 2.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Failed to read frame from webcam.")
                time.sleep(0.2)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            plates = cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(60, 20),
            )

            for (x, y, w, h) in plates:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            now = time.time()
            if len(plates) > 0 and (now - last_capture) >= cooldown_seconds:
                out_path = timestamped_name()
                cv2.imwrite(str(out_path), frame)
                last_capture = now
                print(f"Plate detected. Saved image: {out_path}")

            cv2.imshow("SimplyPark Plate Capture", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
