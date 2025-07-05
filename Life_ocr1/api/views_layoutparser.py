# import layoutparser as lp
# import pytesseract
# from pdf2image import convert_from_path
# import numpy as np
# import cv2

# # Tesseract path if needed
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# # Load layout model (Detectron2)
# model = lp.Detectron2LayoutModel(
#     config_path='lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config',
#     label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
#     extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
# )

# # OCR agent
# ocr_agent = lp.TesseractAgent(languages='eng')

# def extract_fields_from_pdf(pdf_path):
#     images = convert_from_path(pdf_path, dpi=300)
#     all_fields = []

#     for page_num, img in enumerate(images):
#         image_np = np.array(img)
#         image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

#         # Detect layout
#         layout = model.detect(image_bgr)

#         # Sort blocks top to bottom
#         layout = lp.Layout(sorted(layout, key=lambda b: b.block.y_1))

#         label_value_pairs = {}

#         for i, block in enumerate(layout):
#             text = ocr_agent.detect(image_np, block.coordinates)[0].strip()

#             # If it contains a colon, split as key-value
#             if ':' in text:
#                 parts = text.split(':', 1)
#                 key = parts[0].strip().lower()
#                 value = parts[1].strip()
#                 label_value_pairs[key] = value

#             # OR: Try to find next box as value
#             elif i < len(layout) - 1:
#                 next_text = ocr_agent.detect(image_np, layout[i + 1].coordinates)[0].strip()
#                 if len(text) < 30 and len(next_text) < 100:
#                     label_value_pairs[text.lower()] = next_text

#         all_fields.append({
#             "page": page_num + 1,
#             "fields": label_value_pairs
#         })

#     return all_fields
