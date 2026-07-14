from pathlib import Path
from io import BytesIO

from pypdf import PdfWriter


def merge_multiple_pdf(pdfs: list[Path]) -> bytes:
    """
    複数PDFを結合したPDFのバイナリを返す。
    """
    buffer = BytesIO()
    with (PdfWriter()) as merger:
        for pdf in pdfs:
            merger.append(pdf)
        merger.write(buffer)
    return buffer.getvalue()