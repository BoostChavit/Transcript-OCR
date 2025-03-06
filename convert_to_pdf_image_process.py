import cv2
import pytesseract
import csv
from matplotlib import pyplot as plt

def fill_table(image, row_pos, columns_pos, table_data):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1

    for row_idx, (y1, _) in enumerate(row_pos[:-1]):
        for col_idx, (x1, _) in enumerate(columns_pos[:-1]):
            position = (x1 + 5, y1 + 15)  # Adjust text position

            # Put text in the image
            cv2.putText(image, table_data, position, font, font_scale, (0, 0, 0), thickness)

    return image

def detect_tables(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    table_mask = cv2.add(horizontal_lines, vertical_lines)

    # get each table by finding range in histogram
    table_hist = cv2.reduce(table_mask, 1, cv2.REDUCE_AVG).flatten()
    table_pos = []
    temp_pos = 0
    for i, v in enumerate(table_hist):
        if v > 0:
            if temp_pos == 0:
                table_pos.append((i, v))
            temp_pos = i

        if v == 0:
            if table_pos and table_hist[i - 1] > 0:
                temp_v = table_hist[i - 1]
                table_pos.append((i -1, temp_v))
            temp_pos = 0
    

    for i in range(len(table_pos) - 1):
        temp_image = binary[table_pos[i][0]:table_pos[i + 1][0], :]

        height = (table_pos[i + 1][0] - table_pos[i][0])
        if height < 40:
            continue

        # get columns by finding range in histogram
        vertical_lines = cv2.morphologyEx(temp_image, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
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

        # find rows
        horizontal_lines = cv2.morphologyEx(temp_image, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        horizontal_hist = cv2.reduce(horizontal_lines, 1, cv2.REDUCE_AVG).flatten()
        row_pos = []
        temp_pos = 0
        for k, v in enumerate(horizontal_hist):
            if v > 0:
                if temp_pos == 0:
                    row_pos.append((k, v))
                if k != 0:
                    temp_pos = k
                else:
                    temp_pos = 1

            if v == 0:
                temp_pos = 0

        for k in range(len(row_pos)):
            temp_i, temp_v = row_pos[k]
            cv2.circle(temp_image, (100, temp_i), 3, (255), 5)
        
        print(len(row_pos))

        filling_text_image = gray[table_pos[i][0]:table_pos[i + 1][0], :]
        filling_text_image = fill_table(filling_text_image, columns_pos, row_pos, "hi")

        cv2.imshow('image', filling_text_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # return table_bbox, table_mask

image_path = 'page_1.png'
image = cv2.imread(image_path)
detect_tables(image)


# text = ""
# text = extract_from_image(image, table_bbox)
# text  += extract_from_table(image_path, table_bbox, table_mask, table_pos)
