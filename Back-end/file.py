import os
from io import BytesIO
from PyPDF2 import PdfReader
import pdfplumber
from docx import Document

def read_document_file(file_obj, filename: str) -> str:
    text = ""
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        try:
            with pdfplumber.open(file_obj) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception:
            reader = PdfReader(file_obj)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

    elif ext == ".docx":
        doc = Document(file_obj)
        for para in doc.paragraphs:
            text += para.text + "\n"
    else:
        raise ValueError(f"不支持的文件类型: {ext}")

    return text.strip()