# import os
# import pytesseract
# import cv2
# import numpy as np
# from pdf2image import convert_from_path
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.parsers import MultiPartParser
# from django.conf import settings
# from django.core.files.storage import default_storage

# # Set the Tesseract path (for Windows — change if using Mac/Linux)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# class CleanTextOCRView(APIView):
#     parser_classes = [MultiPartParser]

#     def post(self, request):
#         uploaded_file = request.FILES.get("file")
#         if not uploaded_file:
#             return Response({"error": "No file uploaded"}, status=400)

#         file_path = default_storage.save(f"temp/{uploaded_file.name}", uploaded_file)
#         full_path = os.path.join(settings.MEDIA_ROOT, file_path)

#         try:
#             images = convert_from_path(full_path, dpi=300)
#             full_text = ""

#             for image in images:
#                 img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
#                 text = pytesseract.image_to_string(img_cv)
#                 clean_text = text.replace("\n", " ").replace("\r", " ")  # remove newlines
#                 full_text += clean_text + " "

#             return Response("text", full_text.strip())

#         except Exception as e:
#             return Response({"error": str(e)}, status=500)

#         finally:
#             if os.path.exists(full_path):
#                 os.remove(full_path)


import os
import pytesseract
import cv2
import numpy as np
import re
from pdf2image import convert_from_path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.conf import settings
from django.core.files.storage import default_storage

# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# class ExtractDetailsView(APIView):
#     parser_classes = [MultiPartParser]

#     def post(self, request):
#         uploaded_file = request.FILES.get("file")
#         if not uploaded_file:
#             return Response({"error": "No file uploaded"}, status=400)

#         file_path = default_storage.save(f"temp/{uploaded_file.name}", uploaded_file)
#         full_path = os.path.join(settings.MEDIA_ROOT, file_path)

#         try:
#             images = convert_from_path(full_path, dpi=300)
#             full_text = ""

#             for image in images:
#                 img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
#                 text = pytesseract.image_to_string(img_cv)
#                 clean_text = text.replace("\n", " ").replace("\r", " ")
#                 full_text += clean_text + " "
#             print(full_text)
#             # Extract specific details using regex or keyword search
#             details = {
#                 "policy_number": re.search(r"Policy\s*Number[:\-]?\s*(\w+.\d+.\d+.\d+)", full_text, re.IGNORECASE),
#                 "name": re.search(r"Name[:\-]?\s*([A-Za-z\s]+)", full_text, re.IGNORECASE),
#                 "premium": re.search(r"Premium[:\-]?\s*([₹Rs\$\d,\.]+)", full_text, re.IGNORECASE),
#                 "start_date": re.search(r"Start\s*Date[:\-]?\s*(\d{4}-\d{2}-\d{2})", full_text),
#                 "end_date": re.search(r"End\s*Date[:\-]?\s*(\d{4}-\d{2}-\d{2})", full_text),
#             }

#             # Clean up matched values
#             output = {}
#             for key, match in details.items():
#                 output[key] = match.group(1).strip() if match else None
#             print(output)
#             return Response(output)

#         except Exception as e:
#             return Response({"error": str(e)}, status=500)

#         finally:
#             if os.path.exists(full_path):
#                 os.remove(full_path)



class DynamicOCRFieldExtractor(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "No file uploaded"}, status=400)

        file_path = default_storage.save(f"temp/{uploaded_file.name}", uploaded_file)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        try:
            images = convert_from_path(full_path, dpi=300)
            full_text = ""
            for image in images:
                img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                text = pytesseract.image_to_string(img_cv)
                full_text += text.replace("\n", " ") + " "
            print(full_text)
            # Field patterns (can expand based on new templates)
            field_patterns = {
                "policy_number": [
                    r"(policy\s*(no|number|#)[:\-]?\s*)([A-Z0-9\-\/]+)"
                ],
                "gst_number": [
                    r"(gst(in)?|c(g)?st|s(g)?st|igst)[:\-]?\s*([A-Z0-9]{15})"
                ],
                "premium": [
                    r"(total\s*premium|gross\s*premium|premium\s*amount)[:\-]?\s*([₹Rs\$\d,\.]+)"
                ],
                "period_of_insurance": [
                    r"(period\s*of\s*insurance|policy\s*period|from\s*to)[:\-]?\s*([\d\/\-]+\s*(to|-)\s*[\d\/\-]+)"
                ]
            }
            # field_keywords = {
            #     "policy_number": ["policy number", "policy no", "pol no", "policy #", "Policy Number"],
            #     "gst_number": ["gst", "gstin", "cgst", "sgst", "igst", "gst_number"],
            #     "period_of_insurance": ["period of insurance", "policy period", "from", "to", "Period of Insurance"],
            #     "premium": ["total premium", "premium amount", "gross premium", "net premium", "Total Amount"],
            #     "invoice_date": ["date of invoice", "invoice date", "issued on", "date of issue", "Policy Issued on"]
            # }



            # def extract_fields_dynamic(text, field_patterns):
            #     results = {}

            #     for field, patterns in field_patterns.items():
            #         value = None
            #         for pattern in patterns:
            #             match = re.search(pattern, text, re.IGNORECASE)
            #             if match:
            #                 value = match.group(2) if match.lastindex >= 2 else match.group(1)
            #                 break
            #         results[field] = value
                
            #     return results
            def extract_fields_dynamic(text, field_patterns):
                results = {}

                for field, patterns in field_patterns.items():
                    value = None
                    for pattern in patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            # Return last group (most specific value)
                            value = match.group(match.lastindex).strip()
                            break
                    results[field] = value
                print(results)
                return results

            # def clean_text_lines(text):
            #     # Normalize the text by removing duplicate spaces
            #     text = re.sub(r'\s+', ' ', text)
            #     # Split into pseudo-lines based on common break characters
            #     return re.split(r'[.:;\n]', text)
            # print(text)

            # def smart_keyword_extractor(text, keyword_dict):
            #     extracted = {}
            #     lines = text.split()
            #     text_lines = " ".join(lines).split("  ")  # double space = new line

            #     for field, keywords in keyword_dict.items():
            #         for line in text_lines:
            #             for keyword in keywords:
            #                 if keyword.lower() in line.lower():
            #                     value = line.split(":")[-1].strip()  # after colon
            #                     extracted[field] = value
            #                     break
            #             if field in extracted:
            #                 break
            #     return extracted

            # def smart_keyword_extractor(text, keyword_dict):
            #     extracted = {}
            #     lines = clean_text_lines(text)

            #     for field, keywords in keyword_dict.items():
            #         found = False
            #         for line in lines:
            #             line_lower = line.lower()

            #             for keyword in keywords:
            #                 if keyword in line_lower:
            #                     # Try to extract the value after the keyword
            #                     match = re.search(rf"{keyword}[:\-]?\s*(.+)", line, re.IGNORECASE)
            #                     if match:
            #                         value = match.group(1).strip()

            #                         # Ignore garbage values (like URLs or short words)
            #                         if not re.match(r'^https?://', value) and len(value) > 2:
            #                             extracted[field] = value
            #                             found = True
            #                             break
            #             if found:
            #                 break

            #         if field not in extracted:
            #             extracted[field] = None

            #     return extracted



            extracted_data = extract_fields_dynamic(full_text, field_patterns)
            print(extracted_data)
            return Response(extracted_data)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

        finally:
            if os.path.exists(full_path):
                os.remove(full_path)
