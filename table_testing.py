import cv2
import pytesseract
import csv
from matplotlib import pyplot as plt

def detect_tables(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    table_mask = cv2.add(horizontal_lines, vertical_lines)

    # get columns by finding range in histogram
    vertical_hist = cv2.reduce(vertical_lines, 0, cv2.REDUCE_AVG).flatten()
    threshold_gap = int(image.shape[1] * 0.01)
    columns_pos = []
    temp_pos = 0
    for i, v in enumerate(vertical_hist):
        if v > 0:
            if temp_pos == 0:
                columns_pos.append((i, v))
            temp_pos = i

            if columns_pos:
                prev_i, prev_v = columns_pos[-1] 
                if prev_v < v:
                    columns_pos[-1] = (i, v)

        if v == 0:
            if i - temp_pos > threshold_gap:
                temp_pos = 0

    max_value = max([t[1] for t in columns_pos])
    table_pos = [t for t in columns_pos if t[1] == max_value]
    
    contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:1]
    table_bbox = cv2.boundingRect(contours[0])
    return table_bbox, table_mask, table_pos

def extract_from_table(image_path, table_bbox, table_mask, table_pos):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    x, y, w, h = table_bbox

    # take out table grid lines
    for yi in range(gray_image.shape[0]):
        for xi in range(gray_image.shape[1]):
            if table_mask[yi][xi]  > 40:
                gray_image[yi][xi] = 255
    

    # extract to text
    text = ""
    for i in range(len(table_pos) - 1):
        cropped_table = gray_image[y:y+h, table_pos[i][0]:table_pos[i + 1][0]]

        text += pytesseract.image_to_string(cropped_table, lang="eng", config="--psm 6")
    return text

def extract_from_image(image, table_bbox):
    x, y, w, h = table_bbox
    detail = image[:y, :x+w]
    text = pytesseract.image_to_string(detail, lang="tha+eng", config="--psm 6")
    return text

image_path = 'page_1.png'
image = cv2.imread(image_path)
table_bbox, table_mask, table_pos = detect_tables(image)

text = ""
text = extract_from_image(image, table_bbox)
text  += extract_from_table(image_path, table_bbox, table_mask, table_pos)

def remove_special_character(text):
    text = text.replace('(', '')
    text = text.replace(')', '')
    text = text.replace('|', '')
    return text



text = remove_special_character(text)
print(text.splitlines())