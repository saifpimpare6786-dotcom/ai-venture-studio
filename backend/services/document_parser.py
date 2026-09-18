import io
import re
import os
import hashlib
from typing import Dict, Any, List

class DocumentParser:
    @staticmethod
    def compute_sha256(content_bytes: bytes) -> str:
        return hashlib.sha256(content_bytes).hexdigest()

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Strip dangerous formula injection prefixes (=cmd, @SUM) and excessive whitespace."""
        lines = text.splitlines()
        sanitized = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('=', '+', '-', '@')) and any(cmd in stripped.lower() for cmd in ['cmd', 'powershell', 'exec', 'calc']):
                stripped = "'" + stripped  # neutralise formula execution
            sanitized.append(stripped)
        return "\n".join(sanitized)

    @staticmethod
    def parse_excel_or_csv(file_bytes: bytes, filename: str) -> str:
        """Convert Excel spreadsheets or CSV files into structured Markdown tables."""
        try:
            import pandas as pd
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_bytes))
                return f"### File: {filename}\n\n" + df.to_markdown(index=False)
            else:
                excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
                output = [f"### Excel Workbook: {filename}\n"]
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    output.append(f"#### Sheet: {sheet_name}")
                    output.append(df.to_markdown(index=False))
                    output.append("\n")
                return "\n".join(output)
        except Exception as e:
            return f"Error parsing spreadsheet {filename}: {str(e)}"

    @staticmethod
    def parse_pdf(file_bytes: bytes, filename: str) -> str:
        """Extract text page-by-page using PyMuPDF (fitz)."""
        try:
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pages = [f"### PDF Document: {filename}"]
            for i, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    pages.append(f"--- Page {i+1} ---\n{text.strip()}")
            return "\n\n".join(pages)
        except Exception as e:
            return f"Error parsing PDF {filename}: {str(e)}"

    @staticmethod
    def parse_docx(file_bytes: bytes, filename: str) -> str:
        """Extract paragraphs and tables using python-docx."""
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            content = [f"### Word Document: {filename}\n"]
            for p in doc.paragraphs:
                if p.text.strip():
                    content.append(p.text.strip())
            for t in doc.tables:
                table_data = []
                for row in t.rows:
                    row_text = [cell.text.strip() for cell in row.cells]
                    table_data.append(" | ".join(row_text))
                if table_data:
                    content.append("\nTable:\n" + "\n".join(table_data) + "\n")
            return "\n\n".join(content)
        except Exception as e:
            return f"Error parsing DOCX {filename}: {str(e)}"

    @staticmethod
    def parse_pptx(file_bytes: bytes, filename: str) -> str:
        """Extract slide texts using python-pptx."""
        try:
            from pptx import Presentation
            prs = Presentation(io.BytesIO(file_bytes))
            content = [f"### PowerPoint Presentation: {filename}\n"]
            for i, slide in enumerate(prs.slides):
                slide_text = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text.append(shape.text.strip())
                if slide_text:
                    content.append(f"--- Slide {i+1} ---\n" + "\n".join(slide_text))
            return "\n\n".join(content)
        except Exception as e:
            return f"Error parsing PPTX {filename}: {str(e)}"

    @classmethod
    def parse_document(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Auto-detect extension, parse in-memory, compute SHA-256 hash, and sanitize."""
        sha256 = cls.compute_sha256(file_bytes)
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if ext in ('xlsx', 'xls', 'csv'):
            text = cls.parse_excel_or_csv(file_bytes, filename)
            doc_type = 'spreadsheet'
        elif ext == 'pdf':
            text = cls.parse_pdf(file_bytes, filename)
            doc_type = 'pdf'
        elif ext in ('docx', 'doc'):
            text = cls.parse_docx(file_bytes, filename)
            doc_type = 'word'
        elif ext in ('pptx', 'ppt'):
            text = cls.parse_pptx(file_bytes, filename)
            doc_type = 'presentation'
        else:
            text = file_bytes.decode('utf-8', errors='ignore')
            doc_type = 'text'

        sanitized_text = cls.sanitize_text(text)
        return {
            "filename": filename,
            "file_type": ext,
            "doc_type": doc_type,
            "sha256": sha256,
            "text": sanitized_text,
            "size_bytes": len(file_bytes)
        }

document_parser = DocumentParser()
