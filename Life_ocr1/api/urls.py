from django.urls import path
# from .without_api_views import DynamicOCRFieldExtractor
# from .layoutparser_view import extract_fields_from_pdf
# from .views import GeminiOCRView
# from .views_new import GeminiOCRView
from .views_my_UAT import life_background_processing
from .views_multi_up import life_background_processing1
urlpatterns = [
    # path('extract/', DynamicOCRFieldExtractor.as_view(), name='pdf-ocr'),
    # path("extrat_lPar/", extract_fields_from_pdf.as_view(), name = "pdf-ocr1-loPar")
    # path*("life_ocr0")
    # path("life_ocr/", GeminiOCRView.as_view(), name="life_ocr"),
    # path("life_ocr1/", GeminiOCRView.as_view(), name = "life-ocr1"),
    # path("life_ocr2/",Gemini_Bulk_OCRView.as_view(), name = "life-ocr2")
    path("life_ocr3/", life_background_processing, name = "life-ocr3"),
    path("life_ocr4/", life_background_processing1, name = "life-ocr3")
]