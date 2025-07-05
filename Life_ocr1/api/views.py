import google.generativeai as genai
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from django.core.files.storage import default_storage
from pdf2image import convert_from_path
import pytesseract
import numpy as np
import os
import cv2
from django.conf import settings
import json

API_KEY = "AIzaSyCfdmRaUuXAJCMkjNBaRK9LMyTRKVokGH4",
# Set Gemini API key
genai.configure(api_key=API_KEY)

def query_gemini_for_fields(text):
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
    You are a specialist in comprehending and extracting information from insurance documents. Your task is to analyze input text from PDF files and extract, validate, and compute the requested details accurately. The extraction process involves specific rules and exceptions to ensure correctness.
- Insurancre_Company_Name    
- policy_number
- gst_number
- period_of_insurance
- premium
- invoice_date

Return only JSON like:
{{
  "Insurancre_Company_Name":"...",
  "policy_number": "...",
  "gst_number": "...",
  "period_of_insurance": "...",
  "premium": "...",
  "invoice_date": "..."
}}

Text:
{text}
"""

    try:
        response = model.generate_content(prompt)
    except Exception as e:
        return {"error": f"Gemini API failed: {str(e)}"}

    try:
        return json.laods(response.text)  
    except:
        return {"error": "Gemini returned non-JSON", "raw": response.text}

class GeminiOCRView(APIView):
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
                ocr_text = pytesseract.image_to_string(img_cv)
                clean_text = ocr_text.replace("\n", " ").replace("\r", " ")  # remove newlines
                full_text += clean_text + " "
            result = query_gemini_for_fields(full_text.strip())
            return Response(result)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        finally:
            if os.path.exists(full_path):
                os.remove(full_path)
