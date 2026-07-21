import unittest
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
        self.directory = Path(self.temporary_directory.name)
        self.pdf_path = self.directory / "source.pdf"
        self.output_path = self.directory / "output.pdf"

        with PdfWriter() as writer:
            for width in range(100, 104):
                writer.add_blank_page(width=width, height=100)
            writer.write(self.pdf_path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def page_widths(self, path: Path) -> list[int]:
        with PdfReader(path) as reader:
            return [int(page.mediabox.width) for page in reader.pages]

    def test_extracts_multiple_pages(self) -> None:
        extract_multiple_pages(
            self.pdf_path,
            self.output_path,
            start=1,
            stop=4,
            step=2,
        )

        self.assertEqual(self.page_widths(self.output_path), [101, 103])

    def test_extracts_page_with_negative_index(self) -> None:
        extract_page(self.pdf_path, self.output_path, -1)

        self.assertEqual(self.page_widths(self.output_path), [103])

    def test_extract_page_rejects_out_of_range_index(self) -> None:
        for index in (-5, 4):
            with self.subTest(index=index), self.assertRaises(IndexError):
                extract_page(self.pdf_path, self.output_path, index)

    def test_deletes_multiple_pages(self) -> None:
        delete_multiple_pages(
            self.pdf_path,
            self.output_path,
            start=1,
            stop=3,
        )

        self.assertEqual(self.page_widths(self.output_path), [100, 103])

    def test_deletes_page_with_negative_index(self) -> None:
        delete_page(self.pdf_path, self.output_path, -1)

        self.assertEqual(self.page_widths(self.output_path), [100, 101, 102])

    def test_delete_page_rejects_out_of_range_index(self) -> None:
        for index in (-5, 4):
            with self.subTest(index=index), self.assertRaises(IndexError):
                delete_page(self.pdf_path, self.output_path, index)


if __name__ == "__main__":
    unittest.main()
