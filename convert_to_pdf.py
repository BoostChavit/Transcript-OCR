import fitz
from fuzzywuzzy import process

def remove_special_character(text):
    text = text.replace('#', '')
    text = text.replace('_', '')
    text = text.replace('-', '')
    text = text.strip()
    return text

def fill_misspelled_fields(pdf_path, field_values):
    """
    Find keywords (even if misspelled) and insert the corresponding values dynamically.
    """
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
                    print(f"✅ Found '{keyword}' at {inst}")
            else:
                print(f"❌ Could not locate '{keyword}' in PDF")

    return doc

def add_grades_to_pdf(doc, grades):
    for page in doc:
        for course_code, grade in grades.items():
            text_instances = page.search_for(course_code)  
            for inst in text_instances:
                x, y, x1, y1 = inst  
                page.insert_text((x1 + 10, y), grade, fontsize=12, color=(1, 0, 0))  

    return doc


pdf_path = "CourseInspectionForm2560.pdf"

fields_to_fill = {
    "ชื#อ-สกุล": "สมชาย ใจดี",
    "รหัสนิสิต": "12345678",
    "คะแนนเฉลี่ยสะสม": "3.75",
    "หน่วยกิตรวม" : "128",
}


# # Fill the fields and get the modified document
modified_doc = fill_misspelled_fields(pdf_path, fields_to_fill)

# Save the modified PDF to a new file
output_path = "temp.pdf"
modified_doc.save(output_path)

# Close the document
modified_doc.close()
