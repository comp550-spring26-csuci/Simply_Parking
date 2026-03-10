import re
import cv2
import pytesseract

def ocr_plate(image_path: str) -> str:
    img = cv2.imread(image_path)
    if img is None:
        return ""

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    config = r"--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    text = pytesseract.image_to_string(thr, config=config).upper().strip()
    return re.sub(r"[^A-Z0-9]", "", text)
