import pytesseract
import cv2
from PIL import Image

from pdf2image import convert_from_path
from pytesseract import Output
from collections import defaultdict

# Convert PDF to images (one image per page)
images = convert_from_path("6310451413.pdf", dpi=300)

# Process each page
for i, image in enumerate(images):
    image_path = f"transcript_{i+1}.png"
    image.save(image_path, "PNG")
    print(f"Saved: {image_path}")

    # Extract text using Tesseract (Thai + English)
    # text = pytesseract.image_to_string(image, lang="tha+eng")
    
    # print(f"Text from page {i+1}:\n{text}\n{'-'*50}")

# # image = Image.open('page_1.png')
# image = cv2.imread('page_1.png')
# gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# _, binary_image = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

# text = pytesseract.image_to_string(binary_image, lang="tha+eng")
# print(f"Text from page 1:\n{text}\n{'-'*50}")
 