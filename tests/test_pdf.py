import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from pypdf import PdfReader, PdfWriter

from src.modules.pdf import PDF, PDFError
from src.modules.temporary_pdf_file import TemporaryPDFFile


class PDFTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_pdf(self, name: str, page_widths: list[int]) -> tuple[PDF, Path]:
        path = self.directory / name
        with PdfWriter() as writer:
            for width in page_widths:
                writer.add_blank_page(width=width, height=100)
            writer.write(path)

        pdf = PDF()
        pdf._path = path
        return pdf, path

    def create_temporary_pdf(self, page_widths: list[int]) -> tuple[PDF, TemporaryPDFFile]:
        temporary = TemporaryPDFFile()
        with PdfWriter() as writer:
            for width in page_widths:
                writer.add_blank_page(width=width, height=100)
            writer.write(temporary.path)

        pdf = PDF()
        pdf._path = temporary.path
        pdf._temporary = temporary
        return pdf, temporary

    def page_widths(self, pdf: PDF) -> list[int]:
        path = pdf._path
        if path is None:
            self.fail("PDF does not reference a file")
        with PdfReader(path) as reader:
            return [int(page.mediabox.width) for page in reader.pages]

    def test_empty_pdf_rejects_operations_requiring_content(self) -> None:
        pdf = PDF()

        operations = (
            lambda: len(pdf),
            lambda: pdf[0],
            lambda: pdf[:],
            lambda: pdf.save(),
            lambda: pdf.merge(PDF()),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_returns_page_count(self) -> None:
        pdf, _ = self.create_pdf("source.pdf", [100, 101, 102])

        self.assertEqual(len(pdf), 3)

    def test_extracts_integer_page_into_owned_temporary_file(self) -> None:
        pdf, source = self.create_pdf("source.pdf", [100, 101, 102])

        extracted = pdf[-1]

        self.assertIsNot(extracted, pdf)
        self.assertEqual(self.page_widths(extracted), [102])
        extracted_temporary = extracted._temporary
        if extracted_temporary is None:
            self.fail("extracted PDF does not own its temporary file")
        self.assertEqual(extracted._path, extracted_temporary.path)
        self.assertTrue(source.exists())

    def test_integer_index_rejects_bool_and_out_of_range_values(self) -> None:
        pdf, _ = self.create_pdf("source.pdf", [100])

        with self.assertRaises(TypeError):
            pdf[True]
        with self.assertRaises(IndexError):
            pdf[1]

    def test_extracts_inclusive_slice_and_normalizes_bounds(self) -> None:
        pdf, _ = self.create_pdf("source.pdf", [100, 101, 102, 103])

        cases = (
            (slice(None, 2), [100, 101, 102]),
            (slice(1, 3), [101, 102, 103]),
            (slice(2, None), [102, 103]),
            (slice(None, -1), [100, 101, 102, 103]),
            (slice(-2, -1), [102, 103]),
            (slice(-100, 100), [100, 101, 102, 103]),
        )
        for index, expected_widths in cases:
            with self.subTest(index=index):
                self.assertEqual(self.page_widths(pdf[index]), expected_widths)

    def test_slice_rejects_step_and_empty_selection(self) -> None:
        pdf, _ = self.create_pdf("source.pdf", [100, 101])

        with self.assertRaises(ValueError):
            pdf[::2]
        with self.assertRaises(ValueError):
            pdf[1:0]

    def test_merge_is_non_destructive_by_default(self) -> None:
        first, _ = self.create_pdf("first.pdf", [100, 101])
        second, _ = self.create_pdf("second.pdf", [200])

        merged = first.merge(second)

        self.assertIsNot(merged, first)
        self.assertEqual(self.page_widths(merged), [100, 101, 200])
        self.assertEqual(self.page_widths(first), [100, 101])
        self.assertEqual(self.page_widths(second), [200])

    def test_merge_can_replace_self_and_releases_old_temporary_file(self) -> None:
        first, previous_temporary = self.create_temporary_pdf([100])
        previous_path = previous_temporary.path
        second, _ = self.create_pdf("second.pdf", [200])

        result = first.merge(second, overwrite=True)

        self.assertIs(result, first)
        self.assertEqual(self.page_widths(first), [100, 200])
        self.assertTrue(previous_temporary.closed)
        self.assertFalse(previous_path.exists())

    def test_merge_rejects_non_pdf(self) -> None:
        pdf, _ = self.create_pdf("source.pdf", [100])

        with self.assertRaises(TypeError):
            pdf.merge(object())  # type: ignore[arg-type]

    def test_saves_to_resolved_destination_and_updates_reference(self) -> None:
        pdf, source = self.create_pdf("source.pdf", [100])
        output_directory = self.directory / "output"
        output_directory.mkdir()

        result = pdf.save(output_directory, "result.pdf")

        self.assertEqual(result, output_directory / "result.pdf")
        self.assertEqual(pdf._path, result)
        self.assertIsNone(pdf._temporary)
        self.assertEqual(self.page_widths(pdf), [100])
        self.assertTrue(source.exists())

    def test_save_moves_temporary_pdf_to_regular_reference(self) -> None:
        pdf, temporary = self.create_temporary_pdf([100])
        temporary_path = temporary.path
        output = self.directory / "saved.pdf"

        result = pdf.save(self.directory, output.name)

        self.assertEqual(result, output)
        self.assertEqual(pdf._path, output)
        self.assertIsNone(pdf._temporary)
        self.assertTrue(temporary.closed)
        self.assertFalse(temporary_path.exists())
        self.assertEqual(self.page_widths(pdf), [100])

    def test_save_without_new_destination_returns_regular_source(self) -> None:
        pdf, source = self.create_pdf("source.pdf", [100])

        self.assertEqual(pdf.save(), source)
        self.assertEqual(pdf._path, source)

    def test_save_uses_current_name_when_only_directory_is_given(self) -> None:
        pdf, _ = self.create_pdf("source.pdf", [100])
        output_directory = self.directory / "output"
        output_directory.mkdir()

        result = pdf.save(destination_dir=output_directory)

        self.assertEqual(result, output_directory / "source.pdf")
        self.assertEqual(pdf._path, result)

    def test_save_uses_current_directory_when_only_name_is_given(self) -> None:
        pdf, _ = self.create_pdf("source.pdf", [100])

        result = pdf.save(output_file_name="renamed.pdf")

        self.assertEqual(result, self.directory / "renamed.pdf")
        self.assertEqual(pdf._path, result)

    def test_save_failure_preserves_pdf_state(self) -> None:
        pdf, source = self.create_pdf("source.pdf", [100])
        output = self.directory / "output.pdf"

        with (
            patch("src.modules.pdf.copy", side_effect=RuntimeError("copy failed")),
            self.assertRaises(PDFError),
        ):
            pdf.save(output_file_name=output.name)

        self.assertEqual(pdf._path, source)
        self.assertIsNone(pdf._temporary)
        self.assertFalse(output.exists())

    def test_temporary_pdf_cannot_be_saved_to_itself(self) -> None:
        pdf, temporary = self.create_temporary_pdf([100])

        with self.assertRaises(ValueError):
            pdf.save()

        self.assertFalse(temporary.closed)

    def test_save_validates_destination_and_file_name(self) -> None:
        pdf, _ = self.create_pdf("source.pdf", [100])
        file_path = self.directory / "not-a-directory"
        file_path.write_text("content", encoding="utf-8")

        invalid_arguments = (
            (self.directory / "missing", None, FileNotFoundError),
            (file_path, None, NotADirectoryError),
            (None, "nested/result.pdf", ValueError),
            (None, "result.txt", ValueError),
        )
        for directory, name, error_type in invalid_arguments:
            with self.subTest(directory=directory, name=name), self.assertRaises(error_type):
                pdf.save(directory, name)


if __name__ == "__main__":
    unittest.main()
