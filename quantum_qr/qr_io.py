import qrcode
from PIL import Image
from pyzbar.pyzbar import decode

def make_qr_code(data: str, filename: str) -> None:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    img.save(filename)

def read_qr_code(filename: str) -> str:
    # Load image using PIL (Pillow)
    img = Image.open(filename)
    
    # Decode QR using pyzbar
    decoded_objects = decode(img)
    
    # If it fails to find a QR code, fail loudly instead of silently returning ""
    if not decoded_objects:
        raise ValueError(f"Could not read QR code from {filename}")
        
    # pyzbar returns data as raw bytes, so we decode it to a UTF-8 string
    return decoded_objects[0].data.decode("utf-8")