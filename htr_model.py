import cv2
import pytesseract
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.pagesizes import A4

pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

def recognize_english(img_crop):
    pixel_values = processor(images=img_crop, return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values)
    return processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

def recognize_malayalam(img_crop):
    return pytesseract.image_to_string(img_crop, lang="mal")

def contains_malayalam(text):
    return bool(re.search(r'[\u0D00-\u0D7F]', text))

def process_image(image_path):
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(image_rgb)

    text_en = recognize_english(pil_img).strip()
    text_ml = recognize_malayalam(pil_img).strip()

    if text_ml and contains_malayalam(text_ml):
        return text_ml
    elif text_en:
        return text_en
    else:
        return text_en if len(text_en) >= len(text_ml) else text_ml

def save_to_pdf(text, filename="ocr_output.pdf"):
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    custom_style = ParagraphStyle("Custom", parent=styles["Normal"], fontName="HeiseiMin-W3", fontSize=12)

    flowables = [Paragraph(text, custom_style)]
    doc.build(flowables)

if __name__ == "__main__":
    final_text = process_image("ocr_input.jpg")
    save_to_pdf(final_text, "ocr_output.pdf")
    print("OCR output saved to ocr_output.pdf")
