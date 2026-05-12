import io
try:
    import qrcode
    from PIL import Image
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

def qr_available():
    return QR_AVAILABLE

def generate_qr_pil(url, box_size=8, border=4):
    if not QR_AVAILABLE or not url:
        return None
    qr = qrcode.QRCode(version=None,
                       error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=box_size, border=border)
    qr.add_data(url); qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")

def generate_qr_bytes(url):
    img = generate_qr_pil(url)
    if img is None: return None
    buf = io.BytesIO(); img.save(buf, format="PNG"); return buf.getvalue()
