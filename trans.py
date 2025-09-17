import sys
import re
from PyPDF2 import PdfReader
from deep_translator import GoogleTranslator
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.pagesizes import A4


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


def protect_links(text):
    link_pattern = re.compile(r"(https?://\S+|www\.\S+|[\w\.-]+@[\w\.-]+\.\w+)")
    links = {}

    def replacer(match):
        placeholder = f"§§LINK{len(links)}§§"
        links[placeholder] = match.group(0)
        return placeholder

    protected_text = link_pattern.sub(replacer, text)
    return protected_text, links


def restore_links(text, links):
    for placeholder, link in links.items():
        # Case-insensitive restore
        pattern = re.compile(re.escape(placeholder), re.IGNORECASE)
        link_markup = f'<a href="{link}" color="blue"><u>{link}</u></a>'
        text = pattern.sub(link_markup, text)
    return text



def translate_text(text, src_lang, dest_lang, chunk_size=4500):
    protected_text, links = protect_links(text)  # step 1: protect links
    lines = protected_text.splitlines()
    translated_lines = []

    current_chunk = ""
    for line in lines:
        if len(current_chunk) + len(line) + 1 > chunk_size:
            translated_chunk = GoogleTranslator(source=src_lang, target=dest_lang).translate(current_chunk)
            translated_lines.append(translated_chunk)
            current_chunk = ""
        current_chunk += line + "\n"

    if current_chunk.strip():
        translated_chunk = GoogleTranslator(source=src_lang, target=dest_lang).translate(current_chunk)
        translated_lines.append(translated_chunk)

    translated_text = "\n".join(translated_lines)
    return restore_links(translated_text, links)  # step 2: restore links




def write_text_to_pdf(text, output_pdf_path):
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))

    doc = SimpleDocTemplate(output_pdf_path, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=50, bottomMargin=50)

    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontName="HeiseiMin-W3",
        fontSize=12,
        leading=16,
    )

    story = []
    for line in text.splitlines():
        if line.strip():
            story.append(Paragraph(line, normal_style))
            story.append(Spacer(1, 6))
        else:
            story.append(Spacer(1, 12))
    doc.build(story)


def main():
    if len(sys.argv) != 4:
        print("Usage: python translation.py <input_pdf> <output_pdf> <direction>")
        print("direction: 'ml2en' for Malayalam->English, 'en2ml' for English->Malayalam")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    direction = sys.argv[3]

    text = extract_text_from_pdf(input_pdf)

    if direction == 'ml2en':
        translated = translate_text(text, src_lang='ml', dest_lang='en')
    elif direction == 'en2ml':
        translated = translate_text(text, src_lang='en', dest_lang='ml')
    else:
        print("Invalid direction. Use 'ml2en' or 'en2ml'.")
        sys.exit(1)

    write_text_to_pdf(translated, output_pdf)
    print(f"Translated PDF saved to {output_pdf}")


if __name__ == "__main__":
    main()


#to run
#python input.py Malyalam.pdf output.pdf ml2en
#python input.py Malyalam.pdf output.pdf en2ml