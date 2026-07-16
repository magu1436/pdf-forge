import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pypdf import PdfReader, PdfWriter

from src.modules.pypdf_tool import merge_multiple_pdf


class MergeMultiplePDFTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_pdf(self, name: str, page_widths: list[int]) -> Path:
        path = self.directory / name
        with PdfWriter() as writer:
            for width in page_widths:
                writer.add_blank_page(width=width, height=100)
            writer.write(path)
        return path

    def read_page_widths(self, path: Path) -> list[int]:
        with PdfReader(path) as reader:
            return [int(page.mediabox.width) for page in reader.pages]

    def test_merges_pdfs_in_the_given_order(self) -> None:
        first = self.create_pdf("first.pdf", [100, 101])
        second = self.create_pdf("second.pdf", [200])
        output = self.directory / "merged.pdf"

        result = merge_multiple_pdf([first, second], output)

        self.assertEqual(result, output)
        self.assertEqual(self.read_page_widths(output), [100, 101, 200])

    def test_replaces_existing_output_pdf(self) -> None:
        source = self.create_pdf("source.pdf", [200, 201])
        output = self.create_pdf("output.pdf", [100])

        merge_multiple_pdf([source], output)

        self.assertEqual(self.read_page_widths(output), [200, 201])


if __name__ == "__main__":
    unittest.main()
