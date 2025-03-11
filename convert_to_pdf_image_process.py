import cv2
import pytesseract
import json
import numpy as np
import fitz
from fuzzywuzzy import process

def fill_info_fields(pdf_path, field_values):
    doc = fitz.open(pdf_path)
    thai_font = "THSarabunNew.ttf"  
    
    for page in doc:
        page.insert_font(fontname="THSarabun", fontfile=thai_font)

        text = page.get_text("text")

        for keyword, value in field_values.items():
            text_instances = page.search_for(keyword)
            if not text_instances:
                best_match = process.extractOne(keyword, text.split())  # Find closest match
                if best_match and best_match[1] > 90:  # Ensure high similarity
                    matched_text = best_match[0]
                    print(matched_text)
                    text_instances = page.search_for(matched_text)  # Find the location

            if text_instances:
                for inst in text_instances:
                    x, y, x1, y1 = inst
                    page.insert_text((x1 + 10, y + 10), value, fontname="THSarabun", fontsize=12, color=(1, 0, 0))  # Fill value in red
                    
    return doc


def is_text_in_cell(image, x1, x2, y1, y2):
    cell = image[y1:y2, x1:x2]  
    threshold = (cell.shape[0] * cell.shape[1]) * 4.5 // 100
    _, binary = cv2.threshold(cell, 200, 255, cv2.THRESH_BINARY)
    non_white_pixels = np.sum(binary < 255)  
    return non_white_pixels < threshold

def what_text_in_cell(image, x1, x2, y1, y2):
    cell = image[y1:y2, x1:x2]  
    text = pytesseract.image_to_string(cell, lang="tha+eng", config="--psm 6")
    return text


def fill_table(image, row_pos, columns_pos, table_data, cnt):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    thickness = 2

    # print((list(table_data))[cnt])
    data = table_data[(list(table_data))[cnt]]
    
    cell_height = (row_pos[1][0] - row_pos[0][0]) // 2

    for row_idx, (y1, _) in enumerate(row_pos[:-1]):
        if row_idx == 0:
            continue
        for col_idx, (x1, _) in enumerate(columns_pos[:-1]):
            position = (x1 + 10, y1 + cell_height + 10)
            x2, y2 = columns_pos[col_idx + 1][0], row_pos[row_idx + 1][0]
            if (row_idx - 1) > len(data) -1:
                continue
            if len(columns_pos) == 6:
                temp = data[row_idx - 1]
                fill_data = None
                if col_idx == 0:
                    if not is_text_in_cell(image, x1, x2, y1, y2):
                        text = what_text_in_cell(image, x1, x2, y1, y2)
                        if len(text) < 10:
                            image[y1+10:y2-10, x1+10:x2-10] = (255)
                        else:
                            continue
                            
                    fill_data = str(temp['courseId'])
                elif col_idx == 1:
                    if not is_text_in_cell(image, x1, x2, y1, y2):
                        continue
                    fill_data = str(temp['courseName'])
                elif col_idx == 2:
                    if not is_text_in_cell(image, x1, x2, y1, y2):
                        continue
                    fill_data = str(temp['creditAmount'])
                elif col_idx == 3:
                    fill_data = str(temp['enrollmentDate'])
                elif col_idx == 4:
                    fill_data = str(temp['grade'])

                # Put text in the image
                cv2.putText(image, fill_data, position, font, font_scale, (0, 0, 0), thickness)
            
            elif len(columns_pos) == 7:
                temp = data[row_idx - 1]
                fill_data = None
                if col_idx == 0:
                    if not is_text_in_cell(image, x1, x2, y1, y2):
                        continue
                    fill_data = str(temp['courseId'])
                elif col_idx == 1:
                    if not is_text_in_cell(image, x1, x2, y1, y2):
                        continue
                    fill_data = str(temp['courseName'])
                elif col_idx == 2:
                    continue
                elif col_idx == 3:
                    if not is_text_in_cell(image, x1, x2, y1, y2):
                        continue
                    fill_data = str(temp['creditAmount'])
                elif col_idx == 4:
                    fill_data = str(temp['enrollmentDate'])
                elif col_idx == 5:
                    fill_data = str(temp['grade'])

                # Put text in the image
                cv2.putText(image, fill_data, position, font, font_scale, (0, 0, 0), thickness)

    return image

def detect_tables(image, data, second_page=0):
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
    
    cnt = second_page
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

        filling_text_image = gray[table_pos[i][0]:table_pos[i + 1][0], :]
        filling_text_image = fill_table(filling_text_image, row_pos, columns_pos, data, cnt)

        gray[table_pos[i][0]:table_pos[i + 1][0], :] = filling_text_image
        cnt += 1

    return gray


pdf_path = "CourseInspectionForm2560.pdf"

result = None
with open('data.json', 'r') as file:
    result = json.load(file)


fields_to_fill = {
    "ชื#อ-สกุล": result['thaiName'],
    "รหัสนิสิต": result['studentId'],
    "คะแนนเฉลี่ยสะสม": result['gpa'],
    "หน่วยกิตรวม" : result['result']['totalCredit'],
}


# Fill the fields and get the modified document
modified_doc = fill_info_fields(pdf_path, fields_to_fill)

# Save the modified PDF to a new file
output_path = "temp.pdf"
modified_doc.save(output_path)

# Close the document
modified_doc.close()



groups = {
    "Wellness" : [],
    "Entrepreneurship" : [],
    "LanguageandCommunication" : [],
    "ThaiCitizenandGlobalCitizen" : [],
    "Aesthetics" : [],
    "FacultyGECourses" : [],
    "Coresubject" : [],
    "RestrictedElective" : [],
    "Elective" : [],
    "Open Electives" : [],
}

for group in result['result']:
    for subgroup in group['subGroups']:
        courses = []
        for course in subgroup['courses']:
            courses.append(course)
        
        groups[subgroup['subGroupName']] = courses


image_path = 'page_1.png'
image = cv2.imread(image_path)
page1 = detect_tables(image, groups)

image_path = 'page_2.png'
image = cv2.imread(image_path)
page2 = detect_tables(image, groups, second_page=7)
