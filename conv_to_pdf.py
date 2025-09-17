import os
import mimetypes
from docx2pdf import convert
from PIL import Image
from fpdf import FPDF
import pdfkit
import subprocess
import argparse

def convert_to_pdf(input_path, output_path):
    mime_type, _ = mimetypes.guess_type(input_path)
    if mime_type is None:
        raise ValueError("Cannot determine file type.")
    
    # DOCX
    if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        convert(input_path, output_path)

    # XLSX   
    elif mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        try:
            subprocess.run([
                'xlsx2pdf', input_path, output_path
            ], check=True)
        except Exception as e:
            raise RuntimeError(f"Failed to convert XLSX to PDF: {e}")
        
    # Image
    elif mime_type.startswith('image/'):
        image = Image.open(input_path)
        image.save(output_path, "PDF", resolution=100.0)

    # TXT
    elif mime_type == 'text/plain':
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        for line in text.split('\n'):
            pdf.cell(200, 10, txt=line, ln=True)
        pdf.output(output_path)

    # HTML
    elif mime_type == 'text/html':
        pdfkit.from_file(input_path, output_path)
    else:
        raise ValueError(f"Unsupported file type: {mime_type}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert documents to PDF.")
    parser.add_argument("input", help="Path to the input file")
    parser.add_argument("output", help="Path to the output PDF file")
    args = parser.parse_args()
    convert_to_pdf(args.input, args.output)
