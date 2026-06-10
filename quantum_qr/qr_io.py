# import cv2

# def make_qr_code(data: str, filename: str) -> None:
#     """
#     Generate a standard QR code image from a data string and save it to disk.
#     """
#     import qrcode # Keep this import here if only used for generation
#     qr = qrcode.QRCode(version=1, box_size=10, border=5)
#     qr.add_data(data)
#     qr.make(fit=True)
#     img = qr.make_image(fill_color="black", back_color="white")
#     img.save(filename)

# def read_qr_code(filename: str) -> str:
#     """
#     Read and decode a string payload using OpenCV.
#     This implementation is quiet and robust to image noise.
#     """
#     img = cv2.imread(filename)
#     if img is None:
#         raise ValueError(f"Could not open image file: {filename}")
        
#     detector = cv2.QRCodeDetector()
#     data, _, _ = detector.detectAndDecode(img)

#     if not data:
#         raise ValueError(f"Could not decode QR code from {filename}")

#     return data


import qrcode
from PIL import Image
from pyzbar.pyzbar import decode


def make_qr_code(data: str, filename: str) -> None:
    """
    Generate a standard QR code image from a data string and save it to disk.

    Args:
        data: The string payload to encode.
        filename: The output file path for the generated PNG image.
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)


def read_qr_code(filename: str) -> str:
    """
    Read and decode a string payload from a QR code image on disk.

    Args:
        filename: The file path of the QR code image.

    Returns:
        The decoded string data contained in the QR code.

    Raises:
        ValueError: If no QR code could be detected or decoded in the image.
    """
    img = Image.open(filename)
    decoded_objects = decode(img)

    if not decoded_objects:
        raise ValueError(f"Could not read QR code from {filename}")

    return decoded_objects[0].data.decode("utf-8")
