import cv2
import sys
import os
import numpy as np


def load_and_normalize_image(image_path, target_width=900):
    original_bgr = cv2.imread(image_path)
    if original_bgr is None:
        raise ValueError(f"Could not load image from path: {image_path}")

    orig_h, orig_w = original_bgr.shape[:2]
    scale_ratio = target_width / float(orig_w)
    target_height = int(orig_h * scale_ratio)

    resized_bgr = cv2.resize(
        original_bgr,
        (target_width, target_height),
        interpolation=cv2.INTER_AREA,
    )
    resized_gray = cv2.cvtColor(resized_bgr, cv2.COLOR_BGR2GRAY)
    return original_bgr, resized_bgr, resized_gray, scale_ratio


def rotate_image_bound(image, angle_deg):
    h, w = image.shape[:2]
    center = (w / 2.0, h / 2.0)

    m = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    cos = abs(m[0, 0])
    sin = abs(m[0, 1])

    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    m[0, 2] += (new_w / 2.0) - center[0]
    m[1, 2] += (new_h / 2.0) - center[1]

    rotated = cv2.warpAffine(
        image,
        m,
        (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated, m


def preprocess_for_plate_candidates(image_bgr):
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]

    y1 = int(0.12 * h)
    y2 = int(0.92 * h)
    roi = gray[y1:y2, :]

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    roi_eq = clahe.apply(roi)
    roi_blur = cv2.bilateralFilter(roi_eq, 9, 25, 25)

    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 5))
    blackhat = cv2.morphologyEx(roi_blur, cv2.MORPH_BLACKHAT, rect_kernel)

    grad_x = cv2.Sobel(blackhat, cv2.CV_32F, 1, 0, ksize=3)
    grad_x = np.absolute(grad_x)
    grad_x = cv2.normalize(grad_x, None, 0, 255, cv2.NORM_MINMAX).astype("uint8")
    grad_x = cv2.GaussianBlur(grad_x, (5, 5), 0)

    _, binary = cv2.threshold(
        grad_x, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (25, 5)),
        iterations=2,
    )
    binary = cv2.erode(binary, None, iterations=1)
    binary = cv2.dilate(binary, None, iterations=2)

    return gray, roi, binary, y1, y2


def normalize_rect_angle(rect):
    (_, _), (w, h), angle = rect
    if w < h:
        angle += 90.0
    while angle <= -90.0:
        angle += 180.0
    while angle > 90.0:
        angle -= 180.0
    return angle


def score_plate_candidate(cnt, gray_full, y_offset):
    h_img, w_img = gray_full.shape[:2]
    image_area = h_img * w_img

    x, y, w, h = cv2.boundingRect(cnt)
    y_full = y + y_offset
    area = cv2.contourArea(cnt)
    box_area = max(w * h, 1)
    aspect = w / float(max(h, 1))
    extent = area / float(box_area)

    if area < 0.004 * image_area:
        return None
    if w < 110 or h < 35:
        return None
    if aspect < 2.0 or aspect > 6.5:
        return None

    patch = gray_full[y_full:y_full + h, x:x + w]
    if patch.size == 0:
        return None

    patch_eq = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(patch)
    _, char_mask = cv2.threshold(
        patch_eq, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    mx = max(2, int(0.06 * w))
    my = max(2, int(0.12 * h))
    if (h - 2 * my) > 5 and (w - 2 * mx) > 5:
        inner = char_mask[my:h - my, mx:w - mx]
    else:
        inner = char_mask
    ink_ratio = cv2.countNonZero(inner) / float(inner.size)

    rect = cv2.minAreaRect(cnt)
    (_, _), (rw, rh), _ = rect
    long_side = max(rw, rh)
    short_side = max(min(rw, rh), 1.0)
    minrect_aspect = long_side / short_side
    angle = normalize_rect_angle(rect)

    center_x = x + w / 2.0
    center_y = y_full + h / 2.0
    center_penalty = (
        abs(center_x - w_img / 2.0) / w_img
        + 0.6 * abs(center_y - h_img / 2.0) / h_img
    )

    aspect_score = max(0.0, 1.0 - abs(minrect_aspect - 4.2) / 4.2)
    ink_score = 1.0 - min(abs(ink_ratio - 0.32) / 0.32, 1.0)
    extent_score = min(extent / 0.8, 1.0)
    area_score = min(area / (0.08 * image_area), 1.0)
    tilt_penalty = min(abs(angle) / 30.0, 1.0)

    score = (
        3.0 * aspect_score
        + 2.5 * ink_score
        + 1.2 * extent_score
        + 0.8 * area_score
        - 0.8 * center_penalty
        - 0.5 * tilt_penalty
    )

    return {
        "score": score,
        "bbox": (x, y_full, w, h),
        "min_rect": rect,
        "ink_ratio": ink_ratio,
        "aspect": minrect_aspect,
        "extent": extent,
        "area": area,
        "angle": angle,
    }


def detect_plate_bbox(image_bgr, deskew_once=True, depth=0):
    gray, roi, binary, y1, _ = preprocess_for_plate_candidates(image_bgr)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best = None
    for cnt in contours:
        cand = score_plate_candidate(cnt, gray, y1)
        if cand is None:
            continue

        x, y, w, h = cand["bbox"]
#        print(
#            f"x={x}, y={y}, w={w}, h={h}, area={cand['area']:.1f}, "
#            f"aspect={cand['aspect']:.2f}, extent={cand['extent']:.3f}, "
#            f"ink={cand['ink_ratio']:.3f}, angle={cand['angle']:.2f}, score={cand['score']:.3f}"
#        )

        if best is None or cand["score"] > best["score"]:
            best = cand

    corrected = image_bgr.copy()

    if deskew_once and best is not None and depth == 0:
        angle = best["angle"]
        if abs(angle) > 1.0 and abs(angle) < 25.0:
            corrected, _ = rotate_image_bound(image_bgr, angle)
            return detect_plate_bbox(corrected, deskew_once=False, depth=1)

    result_vis = corrected.copy()
    best_box = None

    if best is not None:
        x, y, w, h = best["bbox"]
        pad_x = int(0.03 * w)
        pad_y = int(0.10 * h)

        x = max(x - pad_x, 0)
        y = max(y - pad_y, 0)
        w = min(w + 2 * pad_x, corrected.shape[1] - x)
        h = min(h + 2 * pad_y, corrected.shape[0] - y)

        best_box = (x, y, w, h)
        cv2.rectangle(result_vis, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return best_box, result_vis, corrected


def crop_plate_region(image_bgr, plate_box):
    if plate_box is None:
        return None
    x, y, w, h = plate_box
    if w <= 0 or h <= 0:
        return None
    return image_bgr[y:y + h, x:x + w].copy()


def straighten_plate_region(plate_bgr):
    if plate_bgr is None or plate_bgr.size == 0:
        return None

    gray = cv2.cvtColor(plate_bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    blur = cv2.bilateralFilter(gray, 7, 20, 20)

    blackhat = cv2.morphologyEx(
        blur,
        cv2.MORPH_BLACKHAT,
        cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5)),
    )

    _, binary = cv2.threshold(
        blackhat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (19, 3)),
        iterations=2,
    )

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return plate_bgr.copy()

    merged = np.vstack(contours)
    rect = cv2.minAreaRect(merged)
    angle = normalize_rect_angle(rect)
    print(f"Plate deskew angle: {angle:.2f}")

    if abs(angle) < 0.5:
        rotated = plate_bgr.copy()
    else:
        rotated, _ = rotate_image_bound(plate_bgr, angle)

    rotated_gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
    rotated_gray = clahe.apply(rotated_gray)
    _, mask = cv2.threshold(
        rotated_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return rotated

    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)

    pad_x = int(0.02 * w)
    pad_y = int(0.04 * h)
    x = max(x - pad_x, 0)
    y = max(y - pad_y, 0)
    w = min(w + 2 * pad_x, rotated.shape[1] - x)
    h = min(h + 2 * pad_y, rotated.shape[0] - y)

    return rotated[y:y + h, x:x + w].copy()


def isolate_center_text_band(plate_bgr, top_ratio=0.01, bottom_ratio=0.99):
    if plate_bgr is None or plate_bgr.size == 0:
        return None

    h, w = plate_bgr.shape[:2]
    y1 = max(0, min(int(top_ratio * h), h - 1))
    y2 = max(y1 + 1, min(int(bottom_ratio * h), h))
    return plate_bgr[y1:y2, :].copy()


def remove_small_components(binary, min_area=60):
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    cleaned = np.zeros_like(binary)

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_area:
            cleaned[labels == i] = 255

    return cleaned


def enhance_and_binarize_center_band(center_band_bgr):
    if center_band_bgr is None or center_band_bgr.size == 0:
        return None, None

    gray = cv2.cvtColor(center_band_bgr, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    enhanced = cv2.bilateralFilter(enhanced, 7, 20, 20)

    binary = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        8,
    )

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)),
        iterations=1,
    )

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)),
        iterations=1,
    )

    binary = remove_small_components(binary, min_area=60)

    return enhanced, binary
    
def segment_character_candidates(binary, min_area=120, min_height_ratio=0.45, max_height_ratio=0.98):
    if binary is None or binary.size == 0:
        return [], None

    h_img, w_img = binary.shape[:2]
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)

    candidates = []
    vis = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    for i in range(1, num_labels):
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        area = stats[i, cv2.CC_STAT_AREA]

        if area < min_area:
            continue
        if h < int(min_height_ratio * h_img) or h > int(max_height_ratio * h_img):
            continue
        if w < 8 or w > int(0.30 * w_img):
            continue

        aspect = w / float(max(h, 1))
        if aspect < 0.08 or aspect > 0.75:
            continue

        roi = binary[y:y + h, x:x + w]
        fill_ratio = cv2.countNonZero(roi) / float(w * h)
        if fill_ratio < 0.15 or fill_ratio > 0.85:
            continue

        candidates.append({
            "bbox": (x, y, w, h),
            "area": area,
            "aspect": aspect,
            "fill_ratio": fill_ratio,
            "image": roi.copy(),
        })

    candidates = sorted(candidates, key=lambda c: c["bbox"][0])

    for c in candidates:
        x, y, w, h = c["bbox"]
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return candidates, vis


def extract_character_images(binary, candidates, pad=4):
    chars = []
    if binary is None:
        return chars

    h_img, w_img = binary.shape[:2]

    for idx, c in enumerate(candidates):
        x, y, w, h = c["bbox"]

        x1 = max(x - pad, 0)
        y1 = max(y - pad, 0)
        x2 = min(x + w + pad, w_img)
        y2 = min(y + h + pad, h_img)

        char_img = binary[y1:y2, x1:x2].copy()

        chars.append({
            "index": idx,
            "bbox": (x1, y1, x2 - x1, y2 - y1),
            "image": char_img,
        })

    return chars
    
def normalize_character_image(char_binary, target_size=(40, 60), pad=4):
    if char_binary is None or char_binary.size == 0:
        return None

    if len(char_binary.shape) == 3:
        char_binary = cv2.cvtColor(char_binary, cv2.COLOR_BGR2GRAY)

    _, char_binary = cv2.threshold(char_binary, 127, 255, cv2.THRESH_BINARY)

    coords = cv2.findNonZero(char_binary)
    if coords is None:
        return None

    x, y, w, h = cv2.boundingRect(coords)
    crop = char_binary[y:y + h, x:x + w]

    inner_w = target_size[0] - 2 * pad
    inner_h = target_size[1] - 2 * pad
    if inner_w <= 0 or inner_h <= 0:
        raise ValueError("Padding too large for target size.")

    scale = min(inner_w / float(w), inner_h / float(h))
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    resized = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_NEAREST)

    canvas = np.zeros((target_size[1], target_size[0]), dtype=np.uint8)

    x_offset = (target_size[0] - new_w) // 2
    y_offset = (target_size[1] - new_h) // 2

    canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
    return canvas

def normalize_character_set(char_images, target_size=(40, 60), pad=4):
    normalized = []

    for c in char_images:
        norm = normalize_character_image(c["image"], target_size=target_size, pad=pad)
        if norm is None:
            continue

        normalized.append({
            "index": c["index"],
            "bbox": c["bbox"],
            "image": norm,
        })

    return normalized
    
def load_template_library(template_dir, target_size=(40, 60), pad=4):
    templates = {}

    if not os.path.isdir(template_dir):
        raise ValueError(f"Template directory not found: {template_dir}")

    print(f"Looking for templates in: {os.path.abspath(template_dir)}")

    valid_exts = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")

    for filename in sorted(os.listdir(template_dir)):
        if not filename.lower().endswith(valid_exts):
            continue

        label = os.path.splitext(filename)[0].upper()
        path = os.path.join(template_dir, filename)

#        print(f"Trying template: {path}")

        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"  skipped: could not read")
            continue

        _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)

        if cv2.countNonZero(binary) > (binary.size // 2):
            binary = cv2.bitwise_not(binary)

        norm = normalize_character_image(binary, target_size=target_size, pad=pad)
        if norm is None:
            print(f"  skipped: normalization failed")
            continue

        templates[label] = norm
#        print(f"  loaded as label: {label}")

    print(f"Total templates loaded: {len(templates)}")

    if not templates:
        raise ValueError(f"No valid templates loaded from: {template_dir}")

    return templates


def match_one_character(char_img, templates):
    if char_img is None or char_img.size == 0:
        return None, -1.0

    best_label = None
    best_score = -1.0

    char_float = char_img.astype(np.float32) / 255.0

    for label, tmpl in templates.items():
        tmpl_float = tmpl.astype(np.float32) / 255.0

        score = cv2.matchTemplate(
            char_float,
            tmpl_float,
            cv2.TM_CCOEFF_NORMED,
        )[0, 0]

        if score > best_score:
            best_score = score
            best_label = label

    return best_label, float(best_score)


def recognize_characters(normalized_chars, templates, min_score=0.15):
    results = []

    for c in normalized_chars:
        label, score = match_one_character(c["image"], templates)

        if label is None or score < min_score:
            label = "?"
        results.append({
            "index": c["index"],
            "bbox": c["bbox"],
            "image": c["image"],
            "label": label,
            "score": score,
        })

    results = sorted(results, key=lambda r: r["index"])
    plate_text = "".join(r["label"] for r in results)
    return results, plate_text


def make_recognition_vis(center_band_bgr, recognized_chars):
    if center_band_bgr is None or center_band_bgr.size == 0:
        return None

    vis = center_band_bgr.copy()

    for r in recognized_chars:
        x, y, w, h = r["bbox"]
        text = f"{r['label']}:{r['score']:.2f}"
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            vis,
            text,
            (x, max(18, y - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )

    return vis
    
def apply_plate_validation(recognized_chars, expected_len_range=(6, 8), min_char_score=0.35, min_avg_score=0.45):
    if not recognized_chars:
        return {
            "validated_text": "",
            "is_valid": False,
            "avg_score": 0.0,
            "weak_indices": [],
            "reasons": ["no characters recognized"],
        }

    scores = [float(r["score"]) for r in recognized_chars]
    labels = [str(r["label"]) for r in recognized_chars]
    text = "".join(labels)

    weak_indices = [i for i, s in enumerate(scores) if s < min_char_score]
    avg_score = sum(scores) / max(len(scores), 1)

    reasons = []
    is_valid = True

    if len(recognized_chars) < expected_len_range[0] or len(recognized_chars) > expected_len_range[1]:
        is_valid = False
        reasons.append(
            f"character count {len(recognized_chars)} outside expected range {expected_len_range}"
        )

    if avg_score < min_avg_score:
        is_valid = False
        reasons.append(f"average score too low ({avg_score:.3f} < {min_avg_score:.3f})")

    if weak_indices:
        reasons.append(f"weak matches at indices {weak_indices}")

    return {
        "validated_text": text,
        "is_valid": is_valid,
        "avg_score": avg_score,
        "weak_indices": weak_indices,
        "reasons": reasons,
    }


def build_final_plate_text(recognized_chars, validation_result, unknown_char="?"):
    if not recognized_chars:
        return ""

    weak_indices = set(validation_result["weak_indices"])
    final_chars = []

    for i, r in enumerate(recognized_chars):
        label = r["label"]
        if i in weak_indices and r["score"] < 0.35:
            final_chars.append(unknown_char)
        else:
            final_chars.append(label)

    return "".join(final_chars)


def make_validation_vis(center_band_bgr, recognized_chars, validation_result):
    if center_band_bgr is None or center_band_bgr.size == 0:
        return None

    vis = center_band_bgr.copy()
    weak_indices = set(validation_result["weak_indices"])

    for i, r in enumerate(recognized_chars):
        x, y, w, h = r["bbox"]
        label = r["label"]
        score = float(r["score"])

        if i in weak_indices:
            color = (0, 0, 255)   # red for weak
        else:
            color = (0, 255, 0)   # green for strong

        cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)
        cv2.putText(
            vis,
            f"{label}:{score:.2f}",
            (x, max(18, y - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )

    status_text = "VALID" if validation_result["is_valid"] else "CHECK"
    cv2.putText(
        vis,
        f"{status_text}  avg={validation_result['avg_score']:.2f}",
        (8, vis.shape[0] - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    return vis
    
def read_plate(image_path, template_dir="templates_normalized"):
    outputs = process_one_image(
        image_path,
        target_width=900,
        template_dir=template_dir
    )

    return {
        "image_path": image_path,
        "recognized_text": outputs.get("recognized_text", ""),
        "final_plate_text": outputs.get("final_plate_text", ""),
        "is_valid": outputs.get("validation_result", {}).get("is_valid", False),
        "validation_result": outputs.get("validation_result", {}),
        "outputs": outputs,
    }

def process_one_image(image_path, target_width=900, save_debug_dir=None, template_dir="."):
    original_bgr, resized_bgr, resized_gray, scale_ratio = load_and_normalize_image(
        image_path=image_path,
        target_width=target_width,
    )

    best_box, result_vis, corrected_bgr = detect_plate_bbox(resized_bgr)

    print(f"Loaded image: {image_path}")
    print(f"Resized size: {resized_bgr.shape[1]}x{resized_bgr.shape[0]}")
    print(f"Scale ratio: {scale_ratio:.4f}")
 
    plate_crop = None
    straightened_plate = None
    center_band = None
    center_band_enhanced = None
    center_band_binary = None
    char_candidates = []
    char_segment_vis = None
    char_images = []
    normalized_chars = []
    templates = {}
    recognized_chars = []
    recognized_text = ""
    recognition_vis = None
    validation_result = {
        "validated_text": "",
        "is_valid": False,
        "avg_score": 0.0,
        "weak_indices": [],
        "reasons": [],
    }
    final_plate_text = ""
    validation_vis = None

    if best_box is not None:
        x, y, w, h = best_box
        print(f"Detected plate: x={x}, y={y}, w={w}, h={h}")

        plate_crop = crop_plate_region(corrected_bgr, best_box)
        straightened_plate = straighten_plate_region(plate_crop)
        center_band = isolate_center_text_band(straightened_plate)
        center_band_enhanced, center_band_binary = enhance_and_binarize_center_band(center_band)
        char_candidates, char_segment_vis = segment_character_candidates(center_band_binary)
        char_images = extract_character_images(center_band_binary, char_candidates)
        normalized_chars = normalize_character_set(char_images, target_size=(40, 60), pad=4)

        print(f"Segmented character candidates: {len(char_candidates)}")
        print(f"Normalized characters: {len(normalized_chars)}")

        templates = load_template_library(template_dir, target_size=(40, 60), pad=4)
        recognized_chars, recognized_text = recognize_characters(normalized_chars, templates, min_score=0.15)
        recognition_vis = make_recognition_vis(center_band, recognized_chars)

        validation_result = apply_plate_validation(
            recognized_chars,
            expected_len_range=(6, 8),
            min_char_score=0.35,
            min_avg_score=0.45,
        )
        
        final_plate_text = build_final_plate_text(
            recognized_chars,
            validation_result,
            unknown_char="?"
        )

        print(f"Recognized text: {recognized_text}")
        print(f"Validated text: {final_plate_text}")
        print(f"Valid plate: {validation_result['is_valid']}")
        print(f"Average score: {validation_result['avg_score']:.3f}")

        if validation_result["reasons"]:
            for reason in validation_result["reasons"]:
                print(f"  validation: {reason}")

        for r in recognized_chars:
            print(f"  char[{r['index']}] -> {r['label']}  score={r['score']:.3f}")
    else:
        print("No plate found.")

    if save_debug_dir:
        os.makedirs(save_debug_dir, exist_ok=True)
        stem = os.path.splitext(os.path.basename(image_path))[0]

        cv2.imwrite(os.path.join(save_debug_dir, f"{stem}_detected.png"), result_vis)

        if plate_crop is not None:
            cv2.imwrite(os.path.join(save_debug_dir, f"{stem}_plate.png"), plate_crop)
        if straightened_plate is not None:
            cv2.imwrite(os.path.join(save_debug_dir, f"{stem}_straightened.png"), straightened_plate)
        if center_band is not None:
            cv2.imwrite(os.path.join(save_debug_dir, f"{stem}_center_band.png"), center_band)
        if center_band_enhanced is not None:
            cv2.imwrite(os.path.join(save_debug_dir, f"{stem}_center_band_enhanced.png"), center_band_enhanced)
        if center_band_binary is not None:
            cv2.imwrite(os.path.join(save_debug_dir, f"{stem}_center_band_binary.png"), center_band_binary)
        if char_segment_vis is not None:
            cv2.imwrite(os.path.join(save_debug_dir, f"{stem}_char_segments.png"), char_segment_vis)

        for c in char_images:
            idx = c["index"]
            cv2.imwrite(
                os.path.join(save_debug_dir, f"{stem}_char_{idx:02d}.png"),
                c["image"]
            )
        for c in normalized_chars:
            idx = c["index"]
            cv2.imwrite(
                os.path.join(save_debug_dir, f"{stem}_char_norm_{idx:02d}.png"),
                c["image"]
            )
        if recognition_vis is not None:
            cv2.imwrite(os.path.join(save_debug_dir, f"{stem}_recognition.png"), recognition_vis)
        if validation_vis is not None:
            cv2.imwrite(os.path.join(save_debug_dir, f"{stem}_validation.png"), validation_vis)
        if validation_vis is not None:
            cv2.imwrite(os.path.join(save_debug_dir, f"{stem}_validation.png"), validation_vis)

    return {
        "original_bgr": original_bgr,
        "resized_bgr": resized_bgr,
        "resized_gray": resized_gray,
        "scale_ratio": scale_ratio,
        "best_box": best_box,
        "result_vis": result_vis,
        "corrected_bgr": corrected_bgr,
        "plate_crop": plate_crop,
        "straightened_plate": straightened_plate,
        "center_band": center_band,
        "center_band_enhanced": center_band_enhanced,
        "center_band_binary": center_band_binary,
        "char_candidates": char_candidates,
        "char_segment_vis": char_segment_vis,
        "char_images": char_images,
        "normalized_chars": normalized_chars,
        "templates": templates,
        "recognized_chars": recognized_chars,
        "recognized_text": recognized_text,
        "recognition_vis": recognition_vis,
        "validation_result": validation_result,
        "final_plate_text": final_plate_text,
        "validation_vis": validation_vis,
        "validation_result": validation_result,
        "final_plate_text": final_plate_text,
    }

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        image_path = sys.argv[1]
        outputs = process_one_image(image_path, target_width=900, template_dir="templates_normalized")
        print(f"Final plate text: {outputs['recognized_text']}")
        print(f"Final plate text: {outputs['final_plate_text']}")
        print(f"Plate valid: {outputs['validation_result']['is_valid']}")

        cv2.imshow("Detected Plate", outputs["result_vis"])
        if outputs["plate_crop"] is not None:
            cv2.imshow("Plate Crop", outputs["plate_crop"])
        if outputs["straightened_plate"] is not None:
            cv2.imshow("Straightened Plate", outputs["straightened_plate"])
        if outputs["center_band"] is not None:
            cv2.imshow("Center Text Band", outputs["center_band"])
        if outputs["center_band_enhanced"] is not None:
            cv2.imshow("Center Band Enhanced", outputs["center_band_enhanced"])
        if outputs["center_band_binary"] is not None:
            cv2.imshow("Center Band Binary", outputs["center_band_binary"])
        if outputs["char_segment_vis"] is not None:
            cv2.imshow("Character Segments", outputs["char_segment_vis"])
        for c in outputs["char_images"]:
            cv2.imshow(f"Char {c['index']}", c["image"])
        for c in outputs["normalized_chars"]:
            cv2.imshow(f"Norm Char {c['index']}", c["image"])
        if outputs["recognition_vis"] is not None:
            cv2.imshow("Recognition", outputs["recognition_vis"])
        if outputs["validation_vis"] is not None:
            cv2.imshow("Validation", outputs["validation_vis"])

        while True:
            key = cv2.waitKey(0) & 0xFF
            if key == ord("q"):
                break

        cv2.destroyAllWindows()
        sys.exit(0)

    image_dir = "captures"
    if not os.path.exists(image_dir):
        print(f"Directory not found: {image_dir}")
        sys.exit(1)

    for filename in sorted(os.listdir(image_dir)):
        if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        image_path = os.path.join(image_dir, filename)
        print(f"\nProcessing: {image_path}")
        outputs = process_one_image(image_path, target_width=900, template_dir="templates_normalized")
        print(f"Final plate text: {outputs['recognized_text']}")
        print(f"Final plate text: {outputs['final_plate_text']}")
        print(f"Plate valid: {outputs['validation_result']['is_valid']}")
        

        cv2.imshow("Detected Plate", outputs["result_vis"])
        if outputs["plate_crop"] is not None:
            cv2.imshow("Plate Crop", outputs["plate_crop"])
        if outputs["straightened_plate"] is not None:
            cv2.imshow("Straightened Plate", outputs["straightened_plate"])
        if outputs["center_band"] is not None:
            cv2.imshow("Center Text Band", outputs["center_band"])
        if outputs["center_band_enhanced"] is not None:
            cv2.imshow("Center Band Enhanced", outputs["center_band_enhanced"])
        if outputs["center_band_binary"] is not None:
            cv2.imshow("Center Band Binary", outputs["center_band_binary"])
        if outputs["char_segment_vis"] is not None:
            cv2.imshow("Character Segments", outputs["char_segment_vis"])
        for c in outputs["char_images"]:
            cv2.imshow(f"Char {c['index']}", c["image"])
        for c in outputs["normalized_chars"]:
            cv2.imshow(f"Norm Char {c['index']}", c["image"])
        if outputs["recognition_vis"] is not None:
            cv2.imshow("Recognition", outputs["recognition_vis"])
        if outputs["validation_vis"] is not None:
            cv2.imshow("Validation", outputs["validation_vis"])

        key = cv2.waitKey(0) & 0xFF
        if key == ord("q"):
            break

    cv2.destroyAllWindows()