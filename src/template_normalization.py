import cv2
import os
import numpy as np
import sys

def load_templates(template_dir="templates"):
    templates = {}

    for filename in os.listdir(template_dir):
        if filename.lower().endswith(".png"):
            filepath = os.path.join(template_dir, filename)

            # Load with alpha channel
            image = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)

            if image is None:
                print(f"Warning: Could not load {filename}")
                continue

            label = os.path.splitext(filename)[0]

            # If image has alpha channel
            if image.shape[2] == 4:
                # Extract alpha channel
                alpha = image[:, :, 3]

                # Convert to binary (character = white)
                _, binary = cv2.threshold(alpha, 0, 255, cv2.THRESH_BINARY)

            else:
                # Fallback if no alpha channel
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                _, binary = cv2.threshold(
                    gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )

            templates[label] = binary

    return templates
    
def normalize_templates(templates, output_size=(40, 60), padding=4):
    normalized_templates = {}

    out_w, out_h = output_size

    for label, binary in templates.items():
        original_h, original_w = binary.shape[:2]

        # Find all white pixels
        coords = cv2.findNonZero(binary)

        if coords is None:
            print(f"Warning: No foreground found in template {label}")
            continue

        # Tight bounding box around character
        x, y, w, h = cv2.boundingRect(coords)
        cropped = binary[y:y + h, x:x + w]

        # Compute scale so character fits inside output image with padding
        max_w = out_w - 2 * padding
        max_h = out_h - 2 * padding

        scale = min(max_w / w, max_h / h)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))

        resized = cv2.resize(cropped, (new_w, new_h), interpolation=cv2.INTER_NEAREST)

        # Create blank black canvas
        canvas = np.zeros((out_h, out_w), dtype=np.uint8)

        # Center resized character on canvas
        x_offset = (out_w - new_w) // 2
        y_offset = (out_h - new_h) // 2

        canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized

        normalized_templates[label] = canvas

        # Diagnostics
#        print(
#            f"Label: {label} | "
#            f"Original: {original_w}x{original_h} | "
#            f"BBox: x={x}, y={y}, w={w}, h={h} | "
#            f"Resized: {new_w}x{new_h} | "
#            f"Canvas: {out_w}x{out_h}"
#        )

    return normalized_templates
    
def save_templates(templates, output_dir="templates_normalized"):
    # Create output folder if it does not exist
    os.makedirs(output_dir, exist_ok=True)

    for label, image in templates.items():
        output_path = os.path.join(output_dir, f"{label}.png")
        cv2.imwrite(output_path, image)
#        print(f"Saved: {output_path}")
    
def show_template_grid(templates, cell_size=(40, 60), columns=6, window_name="Normalized Templates"):
    labels = sorted(templates.keys())

    if not labels:
        print("No templates to display.")
        return

    cell_w, cell_h = cell_size
    rows = (len(labels) + columns - 1) // columns

    grid_h = rows * cell_h
    grid_w = columns * cell_w

    grid = np.zeros((grid_h, grid_w), dtype=np.uint8)

    for idx, label in enumerate(labels):
        row = idx // columns
        col = idx % columns

        x = col * cell_w
        y = row * cell_h

        img = templates[label]

        if img.shape != (cell_h, cell_w):
            img = cv2.resize(img, (cell_w, cell_h), interpolation=cv2.INTER_NEAREST)

        grid[y:y + cell_h, x:x + cell_w] = img

    # Enlarge for easier viewing
    preview = cv2.resize(
        grid,
        (grid_w * 3, grid_h * 3),
        interpolation=cv2.INTER_NEAREST
    )

    cv2.imshow(window_name, preview)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
if __name__ == "__main__":
    templates = load_templates()
    normalized_templates = normalize_templates(
        templates,
        output_size=(40, 60),
        padding=4
    )

    save_templates(normalized_templates, output_dir="templates_normalized")

    print(f"\nSaved {len(normalized_templates)} normalized templates.\n")

    show_template_grid(
        normalized_templates,
        cell_size=(40, 60),
        columns=6,
        window_name="Normalized Templates Grid"
    )