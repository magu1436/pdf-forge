from .errors import (
    EncryptedPDFError,
    InvalidPDFError,
    PDFFileNotFoundError,
    PDFNotAFileError,
    PDFValidationError,
    PyPDFToolException,
)
from .merge import merge_multiple_pdf
from .pages import (
    delete_multiple_pages,
    delete_page,
    extract_multiple_pages,
    extract_page,
    get_page_count,
)
from .copy import copy
from .validate import validate_pdf

__all__ = [
    "PyPDFToolException",
    "PDFValidationError",
    "PDFFileNotFoundError",
    "PDFNotAFileError",
    "InvalidPDFError",
    "EncryptedPDFError",
    "merge_multiple_pdf",
    "copy",
    "extract_page",
    "extract_multiple_pages",
    "delete_page",
    "delete_multiple_pages",
    "get_page_count",
    "validate_pdf",
]
