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

    # get table by finding range in histogram
    horizontal_hist = cv2.reduce(table_mask, 1, cv2.REDUCE_AVG).flatten()
    horizontal_pos = []
    temp_pos = 0
    for i, v in enumerate(horizontal_hist):
        if v > 0:
            if temp_pos == 0:
                horizontal_pos.append((i, v))
            temp_pos = i

        if v == 0:
            if horizontal_pos and horizontal_hist[i - 1] > 0:
                temp_v = horizontal_hist[i - 1]
                horizontal_pos.append((i -1, temp_v))
            temp_pos = 0
    
    for i in range(len(horizontal_pos) - 1):
        temp_image = binary[horizontal_pos[i][0]:horizontal_pos[i + 1][0], :]

        height = (horizontal_pos[i + 1][0] - horizontal_pos[i][0])
        if height < 40:
            continue

        vertical_lines = cv2.morphologyEx(temp_image, cv2.MORPH_OPEN, vertical_kernel, iterations=2)

        # get columns by finding range in histogram
        vertical_hist = cv2.reduce(vertical_lines, 0, cv2.REDUCE_AVG).flatten()
        threshold_gap = int(image.shape[1] * 0.01)
        columns_pos = []
        temp_pos = 0
        for j, v in enumerate(vertical_hist):
            if v > 0:
                if temp_pos == 0:
                    columns_pos.append((j, v))
                temp_pos = j

                if columns_pos:
                    prev_i, prev_v = columns_pos[-1] 
                    if prev_v < v:
                        columns_pos[-1] = (j, v)

            if v == 0:
                if j - temp_pos > threshold_gap:
                    temp_pos = 0

        if len(columns_pos) == 0:
            continue

        print(len(columns_pos))
        gray_image = gray.copy()
        # take out table grid lines
        for yi in range(gray_image.shape[0]):
            for xi in range(gray_image.shape[1]):
                if table_mask[yi][xi]  > 40:
                    gray_image[yi][xi] = 255
        
        temp_image = gray_image[horizontal_pos[i][0]:horizontal_pos[i + 1][0], :]

        text = pytesseract.image_to_string(temp_image, lang="tha+eng", config="--psm 6")
        print(text)

        cv2.imshow('image', temp_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # return table_bbox, table_mask

def extract_from_table(image, table_bbox, table_mask, table_pos):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    x, y, w, h = table_bbox

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
detect_tables(image)


# text = ""
# text = extract_from_image(image, table_bbox)
# text  += extract_from_table(image_path, table_bbox, table_mask, table_pos)
