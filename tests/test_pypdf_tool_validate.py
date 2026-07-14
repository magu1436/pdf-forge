import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pypdf import PdfWriter

from src.modules.pypdf_tool import (
    EncryptedPDFError,
    InvalidPDFError,
    PDFFileNotFoundError,
    PDFNotAFileError,
    PDFValidationError,
    PyPDFToolException,
    validate_pdf,
)


class ValidatePDFTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_pdf(self, name: str = "document.pdf", password: str | None = None) -> Path:
        path = self.directory / name
        with PdfWriter() as writer:
            writer.add_blank_page(width=100, height=100)
            if password is not None:
                writer.encrypt(password)
            writer.write(path)
        return path

    def test_accepts_readable_pdf(self) -> None:
        path = self.create_pdf()

        validate_pdf(path)

    def test_rejects_missing_file(self) -> None:
        path = self.directory / "missing.pdf"

        with self.assertRaises(PDFFileNotFoundError):
            validate_pdf(path)

    def test_rejects_directory(self) -> None:
        with self.assertRaises(PDFNotAFileError):
            validate_pdf(self.directory)

    def test_rejects_invalid_pdf(self) -> None:
        path = self.directory / "invalid.pdf"
        path.write_bytes(b"not a PDF")

        with self.assertRaises(InvalidPDFError):
            validate_pdf(path)

    def test_rejects_encrypted_pdf(self) -> None:
        path = self.create_pdf(password="secret")

        with self.assertRaises(EncryptedPDFError):
            validate_pdf(path)

    def test_validation_errors_are_pypdf_tool_exceptions(self) -> None:
        self.assertTrue(issubclass(PDFValidationError, PyPDFToolException))
        for error_type in (
            PDFFileNotFoundError,
            PDFNotAFileError,
            InvalidPDFError,
            EncryptedPDFError,
        ):
            with self.subTest(error_type=error_type):
                self.assertTrue(issubclass(error_type, PDFValidationError))


if __name__ == "__main__":
    unittest.main()
