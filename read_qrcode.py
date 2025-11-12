import cv2
from pyzbar.pyzbar import decode

# Read the QR code image
img = cv2.imread('qrcode.png')

# Decode the QR code
data = decode(img)

if data:
    print(data[0].data.decode('utf-8'))
else:
    print('QR code not found.')