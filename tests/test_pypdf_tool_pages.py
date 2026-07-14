import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from pypdf import PdfReader, PdfWriter

from src.modules.pypdf_tool import (
    delete_multiple_pages,
    delete_page,
    extract_multiple_pages,
    extract_page,
)


class PageOperationsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.pdf_path = Path(self.temporary_directory.name) / "source.pdf"

        with PdfWriter() as writer:
            for width in range(100, 104):
                writer.add_blank_page(width=width, height=100)
            writer.write(self.pdf_path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def page_widths(self, data: bytes) -> list[int]:
        with PdfReader(BytesIO(data)) as reader:
            return [int(page.mediabox.width) for page in reader.pages]

    def test_extracts_multiple_pages(self) -> None:
        data = extract_multiple_pages(self.pdf_path, start=1, stop=4, step=2)

        self.assertEqual(self.page_widths(data), [101, 103])

    def test_extracts_page_with_negative_index(self) -> None:
        data = extract_page(self.pdf_path, -1)

        self.assertEqual(self.page_widths(data), [103])

    def test_extract_page_rejects_out_of_range_index(self) -> None:
        for index in (-5, 4):
            with self.subTest(index=index), self.assertRaises(IndexError):
                extract_page(self.pdf_path, index)

    def test_deletes_multiple_pages(self) -> None:
        data = delete_multiple_pages(self.pdf_path, start=1, stop=3)

        self.assertEqual(self.page_widths(data), [100, 103])

    def test_deletes_page_with_negative_index(self) -> None:
        data = delete_page(self.pdf_path, -1)

        self.assertEqual(self.page_widths(data), [100, 101, 102])

    def test_delete_page_rejects_out_of_range_index(self) -> None:
        for index in (-5, 4):
            with self.subTest(index=index), self.assertRaises(IndexError):
                delete_page(self.pdf_path, index)


if __name__ == "__main__":
    unittest.main()
