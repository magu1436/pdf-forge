import gc
import unittest
import weakref
from pathlib import Path
from unittest.mock import patch

from src.modules.temporary_pdf_file import TemporaryPDFFile


class TemporaryPDFFileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_files: list[TemporaryPDFFile] = []

    def tearDown(self) -> None:
        for temporary_file in self.temporary_files:
            temporary_file.close()

    def create_temporary_file(self, data: bytes = b"") -> TemporaryPDFFile:
        temporary_file = TemporaryPDFFile.from_bytes(data)
        self.temporary_files.append(temporary_file)
        return temporary_file

    def test_creates_reopenable_named_pdf_file(self) -> None:
        temporary_file = self.create_temporary_file(b"pdf contents")

        self.assertIsInstance(temporary_file.path, Path)
        self.assertEqual(temporary_file.path.suffix, ".pdf")
        self.assertTrue(temporary_file.path.is_file())
        self.assertEqual(temporary_file.path.read_bytes(), b"pdf contents")

    def test_path_and_closed_are_read_only(self) -> None:
        temporary_file = self.create_temporary_file()

        with self.assertRaises(AttributeError):
            setattr(temporary_file, "path", Path("replacement.pdf"))
        with self.assertRaises(AttributeError):
            setattr(temporary_file, "closed", True)

    def test_close_removes_file_and_is_idempotent(self) -> None:
        temporary_file = self.create_temporary_file()
        path = temporary_file.path

        self.assertFalse(temporary_file.closed)
        temporary_file.close()
        temporary_file.close()

        self.assertTrue(temporary_file.closed)
        self.assertFalse(path.exists())

    def test_close_can_be_retried_after_deletion_failure(self) -> None:
        temporary_file = self.create_temporary_file()
        path = temporary_file.path

        with patch.object(Path, "unlink", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                temporary_file.close()

        self.assertFalse(temporary_file.closed)
        self.assertTrue(path.exists())

        temporary_file.close()

        self.assertTrue(temporary_file.closed)
        self.assertFalse(path.exists())

    def test_garbage_collection_removes_file(self) -> None:
        temporary_file = self.create_temporary_file()
        path = temporary_file.path
        owner_reference = weakref.ref(temporary_file)
        self.temporary_files.remove(temporary_file)

        del temporary_file
        gc.collect()

        self.assertIsNone(owner_reference())
        self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
