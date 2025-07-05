import os
import uuid
import time
import json
import requests
import pytesseract
import fitz # PyMuPDF
import cv2
from PyPDF2 import PdfReader
from pdf2image import convert_from_path, convert_from_bytes
import numpy as np
import random
import PyPDF2
import pdfplumber
import threading
import re
from io import BytesIO
import datetime
from datetime import datetime
from io import BytesIO

from django.conf import settings
from urllib.parse import quote
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import google.generativeai as genai

from io import BytesIO
from PyPDF2 import PdfReader
import fitz
import pdfplumber
from pdf2image import convert_from_bytes

# ✅ Configure MODELS

MODELS = ["gemini-1.5-flash","models/gemini-1.5-flash"] #,"gemini-2.5-flash-lite-preview-06-17"]
MODEL_CONFIG = {
    "temperature": 0.5,
    "top_p": 0.9,
    "top_k": 50,
    "max_output_tokens": 8000,  # Increased for longer outputs
}

# ✅ Field keyword map (to boost accuracy)
field_keyword_map = {

    # Insurance Company Details
    "Insurance_Company_Name": ["Insurance Company", "Insurer Name"],
    "Business_Category":["Business Category"],
    "Insurance_Company_Branch_Name":["Insurance Company Branch Name"],
    "Insurance_Company_Address": ["Insurance Company Address"],
    "Plan_Name" : ["Product Name","Plan Name","Name of Product"],
    "Sub_Plan_Name" : ["Plan Option","Sub Plan Name"],
    "Addon_Cover" : ["Addon Cover"],
    "Business_Type" : ["Business Type"],

    # Proposer Details
    "Proposer_Name": ["Full Name:(Leave a blank space between First, Middle & Last Name)","Customer Name", "Proposer Name", "Applicant Name", "Policyholder"],
    "Proposer_DOB": ["Date of Birth (DD/MM/YYYY)","Proposer DOB"],
    "Proposer_Gender": ["Gender(M/F/Tg)","Proposer Gender"],
    "Proposer_Aadhaar_No": ["Aadhaar No"],
    "Is_Pan_Card_available_?": ["Is Pan Card available ?"],
    "Proposer_PAN_NO":["PAN* (Proposer)","PAN NO"],
    "Proposer_Height":["What is your height?","Height"],
    "Proposer_Weight":["What is your weight (in kg)?","Weight"],
    "Proposer_Education":["Proposer Education"],
    "Proposer_Email_Id": ["Proposer Email Id"],
    "Proposer_Phone_No": ["Proposer Phone No"],
    "Alternate_Mobile_No":["Telephone No(R)","Alternate Mobile No"],
    "Proposer_Permanent_Address": ["Permanent Address","Permanent Address (If different from correspondence address)/ Overseas residential","Customer Address", "Proposer Address"],
    "Proposer_Communication_Address": ["Correspondence Address","Proposer Communication Address"],
    "Proposer_State":["State"],
    "Proposer_Occupation": ["Occupation", "Job"],
    "Proposer_Office_Name":["Office Name"],
    "Proposer_Annual_Income":["Gross Yearly Income (INR)","Annual Income"],
    
    # Life Assured Details 
    "Life_Assured_Name":[" Full Name: (Leave a blank space between First, Middle & Last Name)","Life Assured Name","Name of the Life Assured"],
    "Life_Assured_DOB":["Date of Birth (DD/MM/YYYY)","Life Assured DOB"],
    "Life_Assured_Gender":["Gender(M/F/Tg)","Life Assured DOB"],

    # Nominee Details
    "Nominee_Name":["Full Name","Nominee Name"],
    "Nominee_DOB":["Date of Birth(DD/MM/YYYY)","Nominee DOB"],
    "Nominee_Relationship":["Relationship with Life to be Assured","Nominee Relationship"],

    "second_Nominee_Name":["Full Name","Nominee Name"],
    "second_Nominee_DOB":["Date of Birth(DD/MM/YYYY)","Nominee DOB"],
    "second_Nominee_Relationship":["Relationship with Life to be Assured","Nominee Relationship"],

    "Appointee_Name":["Full Name","Nominee Name"],
    "Appointee_DOB":["Date of Birth(DD/MM/YYYY)","Nominee DOB"],
    "Appointee_Relationship":["Relationship with Life to be Assured","Nominee Relationship"],

    # Premium Details
    "PPT":["Premium Payment(in years)","Premium Payment","Premium Paying Term"],
    "PT":["Policy Term(in years)","Policy Term"],
    "Frequency":["Frequency","Income Benefit Frequency","For Sanchay Par Advantage, also choose survival benefit payout frequency","Premium Paying Mode"],
    "Number_Of_Due_Collected_In_Months":["Number Of Due Collected In Months"],
    "Total_Premium_With_Tax|Collected_premium":["Total Premium (INR)","Total Premium With Tax / Collected premium","Amount in (INR)","Amount of Instalment Premium"],
    "GST_Percentage":["GST Rate","GST Rate(First Year)","GST Percentage"],
    "GST_AMOUNT":["GST AMOUNT"],
    "Total_Premium_Without_Tax":["Modal Premium (in INR)","Modal Premium (Exclusive of taxes and levies as applicable)","Premium Without Tax","Modal Premium (in INR)"],
    "Annualised_Net_Premium":["Annualised Net Premium"],
    "Total_Sum_Assured":["Sum Assured(in INR)","Total Sum Assured"],
    "Mode_of_Payment":["Mode of Payment"],

    # Payment Details
    "Type_of_Payment":["Mode Of Deposit","Mode of Payment","Premium Payment Method"],
    "Bank_name":["Bank Name"],
    "Bank_Branch_Name":["Bank Branch","Bank Branch Name"],
    "Bank_Account_Number":["Account Number","Bank Account Number"],
    "Bank_IFSC_code":["IFSC Code","Bank Ifsc code"],
    "Bank_Cheque_Number":["Cheque/DD No","Bank Cheque number"],
    "Bank_Cheque_Date":["Cheque/DD/DA Date","Bank Cheque Date"],
    "Customer_Name_As_Per_Bank_Account":["Customer Name as per Bank Account"],
  
    # Policy Details
    "Insurance_Company_Application_No":["Application No","Proposal No","Quotation No","Quotation number","Insurance Company Application No"],
    "Policy_Number": ["Policy Number", "Policy No", "Application No", "Proposal No"],
    "Policy_Issued_Date": ["**All figures as on","Policy Issued Date", "Date of Issue", "Issue Date"],
    "Policy_From_Date": ["Risk Start Date", "Coverage Start"],
    "Policy_To_Date": ["Risk End Date", "Coverage End"],
    "Policy_Status": ["Policy Status", "Application Status"],
    # "Created_Date":["Created Date"],

    # Agency Details
    "Agency_Name": ["Agency Name", "Agent Name", "Broker Name", "Intermediary"],
    "Agency_Code": ["Agency Code", "Agent Code", "Broker Code", "Intermediary Code"],

    # "Customer_Id": ["Customer ID", "Proposer ID"],
    # "Customer_Age": ["Age", "Proposer Age"],
    # "Customer_Gender": ["Gender", "Sex"],
    # "Premium_Payment_Term":["Premium Payment Term"],
    # "Base_Premium": ["Base Premium", "Basic Premium"],
    # "Net_Premium": ["Net Premium"],
    # "GST": ["GST", "IGST", "CGST", "SGST"],
    # "Total_Premium": ["Total Premium", "Gross Premium"],
    # "Sum_Assured":["Sum Assured on Death", "Sum Insured Rs."],
    # "Premium_Payment_Frequency":["Premium Payment Term",],
    # "Instalment_Premium": ["Amount of Instalment Premium"],
}

fields = list(field_keyword_map.keys())

# ✅ Configure Gemini
def setup_model():
    selected_key = random.choice(settings.GEMINI_API_KEYS)
    genai.configure(api_key=selected_key)
    selected_model = random.choice(MODELS)
    model = genai.GenerativeModel(model_name=selected_model, generation_config=MODEL_CONFIG)
    print(f"🔑 Using Gemini key: {selected_key[:15]}... for text extraction")  # Optional for debug 
    print(f"🚀 Using Gemini model: {selected_model} for text extraction")
    return model

def extract_text_from_all_methods(file_path):
    parts = []

    # Try Gemini OCR
    try:
        gemini_text = ""
        with open(file_path, "rb") as f:
            pdf_content = f.read()
        # configure_random_gemini_key() # pick a key every time it's called
        model = setup_model()
        response = model.generate_content(
            contents=[
                "You are an advanced OCR system. Extract the full text from this PDF **without summarizing**. "
                "Ensure that all text, including policy schedules, tables, and details from all pages, is included. "
                "Preserve line breaks, paragraphs, and lists. Do not summarize or omit any information.",
                {"mime_type": "application/pdf", "data": pdf_content}
            ]
        )
        gemini_text += response.text.strip() if hasattr(response, "text") else "[No text extracted]"
        if gemini_text.strip():
            print("✅ Gemini text found")
            # print("✅ Gemini extracted text",gemini_text)
            parts.append(gemini_text.strip())
    except Exception as e:
        print("❌ Gemini OCR failed:", e)

    # Try Tesseract OCR
    try:
        pytesseract_text = ""
        images = convert_from_path(file_path, dpi=300)
        for image in images:
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            ocr_text = pytesseract.image_to_string(img_cv, config="--psm 6")
            if ocr_text:
               pytesseract_text += ocr_text.replace("\n", " ").strip() + " "
        if pytesseract_text.strip():
            print("✅ OCR Pytesseract_text text found")
            # print("✅ OCR Pytesseract_text text found", pytesseract_text)
            parts.append(pytesseract_text.strip())
    except Exception as e:
        print("❌ OCR failed:", e)

    # Try PyMuPDF
    try:
        PyMuPDF_text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                PyMuPDF_text += page.get_text()
        if PyMuPDF_text.strip():
            print("✅ PyMuPDF text found")
            # print("✅ PyMuPDF text found",PyMuPDF_text)
            parts.append(PyMuPDF_text.strip())
    except Exception as e:
        print("❌ PyMuPDF failed:", e)

    # Try PyPDF2
    try:
        PyPDF2_text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    PyPDF2_text += page_text
        if PyPDF2_text.strip():
            print("✅ PyPDF2 text found")
            # print("✅ PyPDF2 text found",PyPDF2_text)
            parts.append(PyPDF2_text.strip())
    except Exception as e:
        print("❌ PyPDF2 failed:", e)

    # Try pdfplumber
    try:
        pdfplumber_text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pdfplumber_text += page_text
        if pdfplumber_text.strip():
            print("✅ pdfplumber text found")
            # print("✅ pdfplumber text found",pdfplumber_text)
            parts.append(pdfplumber_text.strip())
    except Exception as e:
        print("❌ pdfplumber failed:", e)




    full_text = " ".join(parts).strip()

    full_text = full_text.replace('\n', ' ')  # Replaces all newline characters with spaces

    full_text = full_text.replace('\r\n', ' ') # Replaces Windows-style newline characters with spaces
    
    full_text = full_text.replace('\r', ' ')  # Replaces older Mac-style newline characters with spaces


    # To be extra thorough and catch any odd newline representations:
    full_text = re.sub(r'\s+', ' ', full_text) # Replaces all whitespace (including newlines) with a single space
    print("📄 Final full text length:", len(full_text))
    # print("📄 Final full text>>>", full_text)
    return full_text


# def extract_text_from_all_methods(pdf_input):
#     parts = []

#     # Identify file type
#     is_file_path = isinstance(pdf_input, str)
    
#     # If it's not a path, it's a file-like object
#     if not is_file_path:
#         pdf_input.seek(0)
#         pdf_data = pdf_input.read()
#         pdf_input.seek(0)
#     else:
#         with open(pdf_input, "rb") as f:
#             pdf_data = f.read()

#     # ✅ Gemini OCR
#     try:
#         model = setup_model()
#         response = model.generate_content(
#             contents=[
#                 "You are an advanced OCR system. Extract the full text from this PDF **without summarizing**. "
#                 "Ensure that all text, including policy schedules, tables, and details from all pages, is included. "
#                 "Preserve line breaks, paragraphs, and lists. Do not summarize or omit any information.",
#                 {"mime_type": "application/pdf", "data": pdf_data}
#             ]
#         )
#         gemini_text = response.text.strip() if hasattr(response, "text") else ""
#         if gemini_text:
#             print("✅ Gemini text found")
#             parts.append(gemini_text)
#     except Exception as e:
#         print("❌ Gemini OCR failed:", e)

#     # ✅ Tesseract OCR
#     try:
#         pytesseract_text = ""
#         images = convert_from_path(pdf_input, dpi=300) if is_file_path else convert_from_bytes(pdf_data, dpi=300)
#         for image in images:
#             img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
#             ocr_text = pytesseract.image_to_string(img_cv, config="--psm 6")
#             if ocr_text:
#                 pytesseract_text += ocr_text.replace("\n", " ").strip() + " "
#         if pytesseract_text.strip():
#             print("✅ OCR pytesseract text found")
#             parts.append(pytesseract_text.strip())
#     except Exception as e:
#         print("❌ Tesseract OCR failed:", e)

#     # ✅ PyMuPDF
#     try:
#         pymupdf_text = ""
#         doc = fitz.open(pdf_input) if is_file_path else fitz.open(stream=pdf_data, filetype="pdf")
#         for page in doc:
#             pymupdf_text += page.get_text()
#         if pymupdf_text.strip():
#             print("✅ PyMuPDF text found")
#             parts.append(pymupdf_text.strip())
#     except Exception as e:
#         print("❌ PyMuPDF failed:", e)

#     # ✅ PyPDF2
#     try:
#         pypdf2_text = ""
#         reader = PdfReader(pdf_input) if is_file_path else PdfReader(BytesIO(pdf_data))
#         for page in reader.pages:
#             text = page.extract_text()
#             if text:
#                 pypdf2_text += text
#         if pypdf2_text.strip():
#             print("✅ PyPDF2 text found")
#             parts.append(pypdf2_text.strip())
#     except Exception as e:
#         print("❌ PyPDF2 failed:", e)

#     # ✅ pdfplumber
#     try:
#         pdfplumber_text = ""
#         with (pdfplumber.open(pdf_input) if is_file_path else pdfplumber.open(BytesIO(pdf_data))) as pdf:
#             for page in pdf.pages:
#                 text = page.extract_text()
#                 if text:
#                     pdfplumber_text += text
#         if pdfplumber_text.strip():
#             print("✅ pdfplumber text found")
#             parts.append(pdfplumber_text.strip())
#     except Exception as e:
#         print("❌ pdfplumber failed:", e)

#     # 🧹 Clean and merge
#     full_text = " ".join(parts).strip()
#     full_text = re.sub(r'\s+', ' ', full_text)  # Normalize whitespace
#     print("📄 Final full text length:", len(full_text))
#     return full_text


# ✅ Split text into manageable chunks
# def split_texts_into_chunks(text, chunk_size=3500):
#     text = text.replace("\n"," ").strip()
#     chunks = []
#     current_chunk = ""
#     for sentence in text.split(". "):
#         if len(current_chunk) + len(sentence) > chunk_size:
#             chunks.append(current_chunk.strip())
#             current_chunk = sentence
#         else:
#             current_chunk += " " + sentence
#     if current_chunk:
#         chunks.append(current_chunk.strip())
#     return chunks


# ✅ Gemini Query with Keywords
def query_gemini_with_keywords(text, field_keyword_map):
    # configure_random_gemini_key()  # pick a key every time it's called
    selected_key = random.choice(settings.GEMINI_API_KEYS)
    genai.configure(api_key=selected_key)
    model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-06-17", generation_config=MODEL_CONFIG) # gemini-1.5-flash,gemini-1.5-flash-8b
    ''' 🚫 Watch Out:
            If you're sending very long text, this model has token limits (about 8,000 tokens for input + output combined). If you exceed this, you'll get errors like:

            InvalidArgumentError: input too long

            Prompt exceeds model limits'''
    
    print(f"🔑 Using Gemini key: {selected_key[:15]}... for json output")  # Optional for debug
    print(f"🚀 Using gemini model gemini-2.5-flash-lite-preview-06-17... for for json output") # Optional for debug
    # Create prompt using keyword hints
    field_instructions = ""
    for field, keywords in field_keyword_map.items():
        joined = ", ".join(keywords)
        field_instructions += f'- "{field}": look for keywords like [{joined}]\n'

    prompt = f"""
        You are an expert AI in document analyzer. Your task is to extract key details from insurance documents.
        Extract the following fields in correct structure from the insurance document and return JSON with exactly these keys:


{field_instructions}

Return JSON with exactly these keys: {list(field_keyword_map.keys())}

 Rules:
 1. JSON Order
    - Don't Change the JSON Order
 
 2.Customer
    - if customer age is not specified calculate the age from date of birth
 
 3.Dates
    - All Dates in YYYY-MM-DD
    - if can't find Policy Issued Date it will be available somewhere alone 
 
 4.GST
    - Add these SGST, CGST, IGST values if available and return added amount
 
 5.Amounts
    - Remove Comma from all amounts
 
 6.Business
    - Business Category always should be life
    - Business Type always should be fresh 
 
 7.Appointee
    - If the Appointee details not available then consider second Nominee details as Appointee details, fill the Appointee details with Nominee details   
 
 8.Policy Details
    - **HDFC proposal form**
        1.If you can't find application number for Insurance_Company_Application_No consider the number in the starting of the text like 13 digit number * this is an example(1320404820466) *
 
 9.Address
    - Don't take Proposer_Communication_Address or Proposer_Permanent_Address as Insurance_Company_Address. Insurance_Company_Address is always differ from that

    - ICICI PRUDENTIAL LIFE INSURANCE
        1.Replace "SAME AS MAILING ADDRESS" for Proposer_Permanent_Address with Proposer_Communication_Address
 10. Height, Weight
    - Proposer_Height, Proposer_Weight for this not take the life assured height and weight 
Text:
{text}
"""

    try:
        response = model.generate_content(prompt)
        cleaned = re.sub(r"```json|```", "", response.text).strip()
        parsed = json.loads(cleaned)
        # print("cleaned",cleaned)
        # print("🧾 Gemini raw response:\n", response.text)
        # print("parsed",parsed)

        # Fill any missing fields with None
        return {key: parsed.get(key, None) for key in field_keyword_map.keys()}
    
    except Exception as e:
        return {"error": "Gemini failed", "raw": str(e)}
    
# ✅ Extract all fields chunk-wise
# def extract_fields_from_chunks(chunks, field_keyword_map, delay=4, max_requests=50):
#     data = {}
#     request_count = 0

#     for idx, chunk in enumerate(chunks):
#         if request_count >= max_requests:
#             print("🚫 Daily request limit reached.")
#             break

#         print(f"🔍 Processing chunk {idx + 1} / {len(chunks)}")
#         result = query_gemini_with_keywords(chunk, field_keyword_map)

#         # 🔴 Stop and return error if Gemini failed
#         if "error" in result:
#             print("❌ Gemini error:", result.get("raw"))
#             return result  # return this directly to propagate to API view

#         # 🟢 If OK, fill data fields # 1. Add values from this chunk
#         if isinstance(result, dict):
#             for key in field_keyword_map:
#                 if key in result and result[key] and key not in data:
#                     data[key] = result[key]

#         request_count += 1
#         time.sleep(delay)
#         
#     print("data::::1,",data)

#     # Fill any remaining fields with None # 2. At the end of all chunks
#     for key in field_keyword_map:
#         if key not in data:
#             data[key] = None

#     print("data::::2,",data)
#     return data

def extract_fields_from_text(combined_full_text, field_keyword_map):
    result = query_gemini_with_keywords(combined_full_text, field_keyword_map)

    # 🔴 Stop and return error if Gemini failed
    if "error" in result:
        print("❌ Gemini error:", result.get("raw"))
        return result

    # 🟢 Ensure all expected fields exist in the output
    data = {key: result.get(key, None) for key in field_keyword_map}
    
    print("📄 Extracted Data:", data)
    return data

def reformat_date(date_string):
    if date_string and isinstance(date_string, str):
        formats = [
            "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y",
            "%m/%d/%Y", "%m-%d-%Y", "%d %b %Y", "%d %B %Y",
            "%d-%b-%y"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_string.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return date_string.strip()
    return date_string

def str_to_int(str_value):
    try:
        int_value=int(str_value)
        return int_value
    except(ValueError, TypeError):
        return 0
def set_status_based_on_date(output_data, date_field, status_field, past_or_today_value="Issued", future_value="No"):
    """
    Dynamically sets a status field based on a date field in the output_data dictionary.

    Args:
        output_data (dict): The dictionary containing the extracted data.
        date_field (str): The key in the dict containing the date string.
        status_field (str): The key to set in the dict based on the date logic.
        past_or_today_value (str): Value to assign if date is today or in the past.
        future_value (str): Value to assign if date is in the future or invalid.

    Returns:
        dict: Updated dictionary with status field set.
    """
    date_str = output_data.get(date_field)

    if date_str:
        try:
            date_value = datetime.strptime(date_str, "%Y-%m-%d").date()
            today = datetime.today().date()
            output_data[status_field] = past_or_today_value if date_value <= today else future_value
        except ValueError:
            output_data[status_field] = future_value
    else:
        output_data[status_field] = future_value

    return output_data

def pdf_processing(temp_path):
    try:
        # 🔹 Step 1: Extract OCR text first
        combined_full_text = extract_text_from_all_methods(temp_path)
        # print("combined_full_text::::",combined_full_text)

        # 🔹 Step 2: Check for keyword (optional)
        # if "vizza" not in combined_full_text.lower():
        #     return Response({"message": "Agency Name not found in document. Skipping processing."})

        # 🔹 Chunk & Gemini
        # chunks = split_texts_into_chunks(combined_full_text)
        # print("chunks::::",chunks)
        # output_data = extract_fields_from_chunks(chunks, field_keyword_map)

        output_data = extract_fields_from_text(combined_full_text, field_keyword_map)

        if "error" in output_data:
            return Response(output_data, status=500)        

        output_data["Policy_Issued_Date"] = reformat_date(output_data.get("Policy_Issued_Date"))
        output_data["Policy_From_Date"] = reformat_date(output_data.get("Policy_From_Date"))
        output_data["Policy_To_Date"] = reformat_date(output_data.get("Policy_To_Date"))
        
        output_data = set_status_based_on_date(output_data,date_field="Policy_Issued_Date",status_field="Policy_Status",past_or_today_value="Issued",future_value="No")
        
        if output_data.get("Agency_Name") != None and "vizza" in output_data.get("Agency_Name").lower():
            output_data["Agency_Name"] = "VIZZA INSURANCE BROKING SERVICES PRIVATE LIMITED"            
        else:
            output_data["Agency_Name"] = None
            output_data["Agency_Code"] = None

        if output_data.get("Proposer_PAN_NO") != None:
            output_data["Is_Pan_Card_available_?"] = "Yes"
        else:
            output_data["Is_Pan_Card_available_?"] = "No"
        
        # Appointee
        output_data["Appointee_Name"]=output_data["second_Nominee_Name"]
        output_data["Appointee_DOB"]=output_data["second_Nominee_DOB"]
        output_data["Appointee_Relationship"]=output_data["second_Nominee_Relationship"]

        # Annualised_Net_Premium
        
        output_data["Annualised_Net_Premium"] = str_to_int( output_data["Total_Premium_With_Tax|Collected_premium"]*12)- str_to_int(output_data["GST_AMOUNT"]*12)
        # gst_components = []
        # for tax_type in ["CGST", "SGST", "IGST"]:
        #     value = output_data.get(tax_type)
        #     if value:
        #         gst_components.append(f"{tax_type}: {value}")
        #         del output_data[tax_type]

        # output_data["GST_AMOUNT"] = ", ".join(gst_components) if gst_components else None

        # if output_data["GST_AMOUNT"] == None or output_data["GST_AMOUNT"] == "0.00" or output_data["GST_AMOUNT"] == 0.00:
        #     output_data["GST_AMOUNT"] = str(str_to_int(output_data["Premium_Without_Tax"]) - str_to_int(output_data["Annualised_Net_Premium"]))
        
        print(output_data)
        return Response(output_data)
    except Exception as e:
        print("❌ Error in background processing task:", str(e))
        return Response({"error": "Processing failed", "details": str(e)}, status=500)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ✅ Final Django View
class GeminiOCRView(APIView):
    def post(self, request):

        # Remote URL using filename
        filename = request.data.get("filename")
        base_url = "https://erpproject.blr1.cdn.digitaloceanspaces.com/live/life_salessheet/"
        # base_url = "https://erpproject.blr1.digitaloceanspaces.com/live/general_datasheet/"

        # Local file upload
        uploaded_file = request.FILES.get("file")

        if not filename and not uploaded_file:
            return Response({"error": "No filename or file provided"}, status=400)

        temp_path = os.path.join(settings.MEDIA_ROOT, "temp", f"{uuid.uuid4()}.pdf")

        try:
            if filename:
                file_url = base_url + quote(filename)
                print("📎 PDF URL:", file_url)
                # 🔹 Download file
                response = requests.get(file_url)
                if response.status_code != 200:
                    print("Failed to download pdf")
                    return Response({"error": "Failed to download PDF"}, status=400)

                with open(temp_path, "wb") as file:
                    file.write(response.content)
            elif uploaded_file:
                # response = request.get(uploaded_file)
                # if response.status_code != 200:
                #     print("Failed to get pdf file")
                #     return Response({"error":"Failed to get pdf file"}, status=400)
                
                with open(temp_path, "wb") as file:
                    for chunk in uploaded_file.chunks():
                        file.write(chunk)
                '''
                📩 How to Test in Postman:
                🔹 For remote file:
                Set POST body type as raw

                {
                "filename": "20250415190701_1744724221.2605769650072590536_BenefitIllustration.pdf"
                }
                
                🔹 For local file upload:
                Set POST body type as form-data

                Key: file → Type: File → Choose your .pdf'''

            # threading.Thread(target=pdf_processing, args=(temp_path,)).start()
            # return Response({"Message":"Upload started, Proccessing in background..."},status=status.HTTP_202_ACCEPTED)

            return pdf_processing(temp_path)
        
        except Exception as e:
            return Response({"error": str(e)}, status=500)

# class GeminiOCRView(APIView):
#     def post(self, request):
#         filename = request.data.get("filename")
#         uploaded_file = request.FILES.get("file")

#         base_url = "https://erpproject.blr1.cdn.digitaloceanspaces.com/live/life_salessheet/"

#         if not filename and not uploaded_file:
#             return Response({"error": "No filename or file provided"}, status=400)

#         try:
#             if filename:
#                 # ✅ Remote file (from URL)
#                 file_url = base_url + quote(filename)
#                 print("📎 PDF URL:", file_url)

#                 response = requests.get(file_url)
#                 if response.status_code != 200:
#                     return Response({"error": "Failed to download PDF"}, status=400)

#                 # 🔄 Process in-memory without saving to disk
                
#                 pdf_bytes = BytesIO(response.content)
#                 return pdf_processing(pdf_bytes)  # <-- Update pdf_processing to accept BytesIO

#             elif uploaded_file:
#                 # ✅ Local upload (via Postman form-data)
#                 from io import BytesIO
#                 pdf_bytes = BytesIO(uploaded_file.read())

#             # threading.Thread(target=pdf_processing, args=(temp_path,)).start()
#             # return Response({"Message":"Upload started, Proccessing in background..."},status=status.HTTP_202_ACCEPTED)
#             # return pdf_processing(pdf_bytes)  # <-- Update pdf_processing to accept BytesIO
        
#         except Exception as e:
#             return Response({"error": str(e)}, status=500)
