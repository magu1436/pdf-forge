from pathlib import Path

from pypdf import PdfReader

from .errors import (
    EncryptedPDFError,
    InvalidPDFError,
    PDFFileNotFoundError,
    PDFNotAFileError,
)


def validate_pdf(pdf: Path) -> None:
    """指定したファイルが暗号化されておらず、PDFとして読み込めることを検証する。

    検証に失敗した場合は、原因に応じたPDFValidationErrorの派生例外を送出する。
    """
    if not pdf.exists():
        raise PDFFileNotFoundError(f"PDF file does not exist: {pdf}")

    if not pdf.is_file():
        raise PDFNotAFileError(f"Path is not a file: {pdf}")

    try:
        with PdfReader(pdf) as reader:
            if reader.is_encrypted:
                raise EncryptedPDFError("Encrypted PDFs are not supported")

            for _ in reader.pages:
                pass
    except EncryptedPDFError:
        raise
    except Exception as error:
        raise InvalidPDFError(f"File cannot be read as a PDF: {pdf}") from error
