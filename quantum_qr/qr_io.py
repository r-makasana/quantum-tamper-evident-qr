import cv2
import qrcode

def make_qr_code(data: str, filename: str) -> None:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save(filename)


def read_qr_code(filename: str) -> str:
     # Load image
    img = cv2.imread(filename)
    # Create QR detector
    detector = cv2.QRCodeDetector()
    # Decode QR
    data, vertices_array, binary_qrcode = detector.detectAndDecode(img)
    return data