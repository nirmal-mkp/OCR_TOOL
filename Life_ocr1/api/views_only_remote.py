import os
import uuid
import time
import json
import requests
import pytesseract
import fitz # PyMuPDF
import cv2
import numpy as np
import random
import threading
import datetime
from datetime import datetime
import re
import PyPDF2
import pdfplumber
from io import BytesIO
from pdf2image import convert_from_path,convert_from_bytes
from django.conf import settings
from urllib.parse import quote
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai import GenerativeModel
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import logging

logging.getLogger("fitz").setLevel(logging.ERROR)
load_dotenv()  # Only needed if using .env files during local dev
# ✅ Configure MODELS

# print("Loaded keys:", os.getenv("GOOGLE_API_KEYS"))
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
    "Plan_Name" : ["Product Name","Plan Name","Name of Product","Base Plan"],
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
    "Proposer_Height":["What is your height?","Proposer Height"],
    "Proposer_Weight":["What is your weight (in kg)?","Proposer Weight"],
    "Proposer_Education":["Proposer Education"],
    "Proposer_Email_Id": ["Proposer Email Id"],
    "Proposer_Phone_No": ["Proposer Phone No"],
    "Proposer_Alternate_Phone_No":["Telephone No(R)","Alternate Mobile No"],
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

API_KEYS = os.getenv("GOOGLE_API_KEYS", "").split(",")
# ✅ Configure Gemini
def setup_model():
    selected_key = random.choice(API_KEYS)
    genai.configure(api_key=selected_key)
    selected_model = random.choice(MODELS)
    model = genai.GenerativeModel(model_name=selected_model, generation_config=MODEL_CONFIG)
    print(f"🔑 Using Gemini key: {selected_key[:15]}... for text extraction")  # Optional for debug 
    print(f"🚀 Using Gemini model: {selected_model} for text extraction")
    return model


def upload_pdf_to_gemini(pdf_content, model_name=None):
    """Uploads a PDF (binary data) to Gemini and extracts text."""
    
    model = model_name if model_name else setup_model()
    print(f"🚀 Using OCR model: {model}")

    try:
        response = model.generate_content(
            contents=[
                "You are an advanced OCR system. Extract the full text from this PDF **without summarizing**. "
                "Ensure that all text, including policy schedules, tables, and details from all pages, is included. "
                "Preserve line breaks, paragraphs, and lists. Do not summarize or omit any information.",
                {"mime_type": "application/pdf", "data": pdf_content}
            ]
        )
        return response.text if hasattr(response, "text") else "[No text extracted]"
    except Exception as e:
        print(f"⚠️ OCR failed: {str(e)}")
        return f"[OCR Extraction Failed] {str(e)}"

def extract_text_from_all_methods(pdf_content):
    combined_text = ""
    combined_text2 = ""

    # Convert file path to bytes if needed
    if isinstance(pdf_content, str):
        try:
            with open(pdf_content, 'rb') as f:
                pdf_content = f.read()
        except Exception as e:
            return "Unable to read the PDF file"

    pdf_stream = BytesIO(pdf_content)

    # 1. Pytesseract (image OCR)
    pytesseract_text = ""
    try:
        pdf_stream.seek(0)
        images = convert_from_bytes(pdf_stream.read(), dpi=300)
        for image in images:
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            ocr_text = pytesseract.image_to_string(img_cv, config="--psm 6")
            if ocr_text:
                pytesseract_text += ocr_text.replace("\n", " ").strip() + " "
        if pytesseract_text.strip():
            print("✅ OCR pytesseract_text found")
    except Exception as e:
        print("❌ OCR with pytesseract failed:",str(e))

    # 2. pdfplumber
    text_pdfplumber = ""
    try:
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_pdfplumber += page_text
        if text_pdfplumber.strip():
            print("✅ text_pdfplumber found")
    except Exception as e:
        print("❌ pdf_plumber is failed:",str(e))
        print("Uploding pdf to gemini to extract data")
        combined_text2 = upload_pdf_to_gemini(pdf_content)

    # 3. PyPDF2
    text_pypdf2 = ""
    try:
        pdf_stream.seek(0)
        reader = PyPDF2.PdfReader(pdf_stream)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_pypdf2 += page_text
        if text_pypdf2.strip():
            print("✅ text_pypdf2 found")
    except Exception as e:
        print("❌ PyPDF2 failed:", str(e))

    # 4. PyMuPDF
    text_pymupdf = ""
    try:
        pdf_stream.seek(0)
        with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
            for page in doc:
                page_text = page.get_text() or ""
                text_pymupdf += page_text
        if text_pymupdf.strip():
            print("✅ text_pymupdf found")
    except Exception as e:
        print("❌ PyMuPDF failed:",str(e))

    # Combine all
    combined_text = (
        pytesseract_text.strip() +
        text_pdfplumber.strip() +
        text_pypdf2.strip() +
        text_pymupdf.strip() +
        combined_text2
    )

    combined_text = combined_text.replace('\n', ' ').replace('\r\n', ' ').replace('\r', ' ')
    combined_text = re.sub(r'\s+', ' ', combined_text)

    # If text is still too short, use Gemini
    if not combined_text or len(combined_text) <= 500:
        combined_text = upload_pdf_to_gemini(pdf_content)
        return combined_text
    
    return combined_text

# # ✅ Split text into manageable chunks
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
    selected_key = random.choice(API_KEYS)
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

 2. Customer
    - if customer age is not specified calculate the age from date of birth
 
 3. Dates
    - All Dates in YYYY-MM-DD
    - if can't find Policy Issued Date it will be available somewhere alone 
 
 4. GST
    - Add these SGST, CGST, IGST values if available and return added amount
 
 5. Amounts
    - Remove Comma from all amounts
 
 6. Business
    - Business Category always should be life
    - Business Type always should be fresh 
 
 7. Appointee
    - If the Appointee details not available then consider second Nominee details as Appointee details, fill the Appointee details with Nominee details   
 
 8. Policy Details
    - **HDFC proposal form**
        1. If you can't find application number for Insurance_Company_Application_No consider the number in the starting of the text like 13 digit number ** this is an example(1320404820466) ** 
 
 9. Address
    - Don't take Proposer_Communication_Address or Proposer_Permanent_Address as Insurance_Company_Address.  Insurance_Company_Address is always differ from that

    - ** ICICI PRUDENTIAL LIFE INSURANCE **
        1. Replace "SAME AS MAILING ADDRESS" for Proposer_Permanent_Address with Proposer_Communication_Address
 
 10. Payment Details
    - Type_of_Payment is one of among this (UPI Payment,NEFTCard Payment,Financier,EMI,Gpay,PhonePe,DD,Cheque,Cash,Online Payment) if you can't find this don't return value for Type_of_Payment

 11. Phone Number
    - Remove country code from phone number

 12. Height, Weight
    - dont't take the life assured Height, Weight for Proposer_Height, Proposer_Weight

 13. Insurance Company Details
    - ** Insurance_Company_Branch_Name **
        i. Find the city from Insurance_Company_Address value and consider that as Insurance_Company_Branch_Name 

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

def pdf_processing(pdf_content):
    try:
        # 🔹 Step 1: Extract OCR text first
        combined_full_text = extract_text_from_all_methods(pdf_content)
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
        # output_data.get("")
        gender=["m","l"]
        if output_data.get("Life_Assured_Gender") != None and output_data.get("Life_Assured_Gender").lower() in gender:
            if output_data.get("Life_Assured_Gender") == "m":
                output_data["Life_Assured_Gender"] = "Male"
            if output_data.get("Life_Assured_Gender") == "l":
                output_data["Life_Assured_Gender"] = "Female"
        
        phone_no = output_data.get('Proposer_Phone_No') 
        if isinstance(phone_no, str) and ("*" in phone_no or "x" in phone_no or "X" in phone_no):
            output_data['Proposer_Phone_No'] = None
        else:
            output_data['Proposer_Phone_No'] = phone_no 

        alternate_phone_no = output_data.get('Proposer_Alternate_Phone_No') 
        if isinstance(  alternate_phone_no, str) and ("*" in   alternate_phone_no or "x" in   alternate_phone_no or "X" in   alternate_phone_no):
            output_data['Proposer_Alternate_Phone_No'] = None
        else:
            output_data['Proposer_Alternate_Phone_No'] = alternate_phone_no  

        email_id = output_data.get('Proposer_Email_Id')
        if isinstance(email_id, str) and ("**" in email_id or "xx" in email_id or "XX" in email_id,"*" in email_id ):
            output_data['Proposer_Email_Id'] = None
        else:
            output_data['Proposer_Email_Id'] = email_id 
              
        names = output_data["Proposer_Name"].lower()
        replace_chars = ["mr","mrs","mr/mrs"]
        for i in replace_chars:
            names = names.replace(i,"")
        output_data["Proposer_Name"] = names.strip().title()

        # Annualised_Net_Premium
        output_data["Annualised_Net_Premium"] = str(str_to_int(output_data["Total_Premium_With_Tax|Collected_premium"])*12-str_to_int(output_data["GST_AMOUNT"])*12)
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
    
   

# ✅ Final Django View
# @csrf_exempt
# @api_view(["POST"])
# def life_background_processing(data):
#     # Remote URL using filename
#     filename = data["file"]
#     base_url = "https://erpproject.blr1.cdn.digitaloceanspaces.com/live/life_salessheet/"
#     # base_url = "https://erpproject.blr1.digitaloceanspaces.com/live/general_datasheet/"

#     try:
#         if filename:
#             file_url = base_url + quote(filename)
#             print("📎 PDF URL:", file_url)
#             response = requests.get(file_url)
#             # print(response)
#             if response.status_code != 200:
#                 print("Failed to download pdf")
#                 return Response({"error": "Failed to download PDF"}, status=400)

#         pdf_content = response.content
#         # threading.Thread(target=pdf_processing, args=(temp_path,)).start()
#         # return Response({"Message":"Upload started, Proccessing in background..."},status=status.HTTP_202_ACCEPTED)

#         return pdf_processing(pdf_content)
    
#     except Exception as e:
#         return Response({"error": str(e)}, status=500)
   
# ✅ Final Django View
# @api_view(["POST"])
# def life_background_processing(request):

#     # Remote URL using filename
#     filename = request.data.get("filename")
#     base_url = "https://erpproject.blr1.cdn.digitaloceanspaces.com/live/life_salessheet/"
#     # base_url = "https://erpproject.blr1.digitaloceanspaces.com/live/general_datasheet/"

#     try:
#         if filename:
#             file_url = base_url + quote(filename)
#             print("📎 PDF URL:", file_url)
#             response = requests.get(file_url)
#             print(response)
#             if response.status_code != 200:
#                 print("Failed to download pdf")
#                 return Response({"error": "Failed to download PDF"}, status=400)

#         pdf_content = response.content
#         # threading.Thread(target=pdf_processing, args=(temp_path,)).start()
#         # return Response({"Message":"Upload started, Proccessing in background..."},status=status.HTTP_202_ACCEPTED)

#         return pdf_processing(pdf_content)
    
#     except Exception as e:
#         return Response({"error": str(e)}, status=500)

@api_view(["POST"])
def life_background_processing(request):
    base_url = "https://erpproject.blr1.cdn.digitaloceanspaces.com/live/life_salessheet/"
    pdf_content = None

    try:
        # Case 1: Remote PDF from URL
        filename = request.data.get("filename")
        if filename:
            file_url = base_url + quote(filename)
            print("📎 PDF URL:", file_url)
            response = requests.get(file_url)
            if response.status_code != 200:
                print("❌ Failed to download PDF")
                return Response({"error": "Failed to download PDF"}, status=400)
            pdf_content = response.content

        # Case 2: Local PDF from upload (form-data file)
        elif 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            pdf_content = uploaded_file.read()
            print(f"📂 Local file uploaded: {uploaded_file.name}")

        else:
            return Response({"error": "No filename or file uploaded"}, status=400)

        # ✅ Proceed to process the PDF
        return pdf_processing(pdf_content)

    except Exception as e:
        print("❌ Exception during processing:", str(e))
        return Response({"error": str(e)}, status=500)
