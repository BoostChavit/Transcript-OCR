import fitz
import json
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
                    print(f"✅ Found '{keyword}' at {inst}")
            else:
                print(f"❌ Could not locate '{keyword}' in PDF")

    return doc



pdf_path = "CourseInspectionForm2560.pdf"

fields_to_fill = {
    "ชื#อ-สกุล": "สมชาย ใจดี",
    "รหัสนิสิต": "12345678",
    "คะแนนเฉลี่ยสะสม": "3.75",
    "หน่วยกิตรวม" : "128",
}


# Fill the fields and get the modified document
modified_doc = fill_info_fields(pdf_path, fields_to_fill)

# Save the modified PDF to a new file
output_path = "temp.pdf"
modified_doc.save(output_path)

# Close the document
modified_doc.close()