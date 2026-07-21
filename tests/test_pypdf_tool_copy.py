import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.modules.pypdf_tool import copy


class CopyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)
        self.source = self.directory / "source.pdf"
        self.output = self.directory / "output.pdf"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_copies_source_to_output(self) -> None:
        self.source.write_bytes(b"PDF contents")

        copy(self.source, self.output)

        self.assertEqual(self.output.read_bytes(), b"PDF contents")
        self.assertEqual(self.source.read_bytes(), b"PDF contents")

    def test_replaces_existing_output(self) -> None:
        self.source.write_bytes(b"new contents")
        self.output.write_bytes(b"old contents")

        copy(self.source, self.output)

        self.assertEqual(self.output.read_bytes(), b"new contents")


if __name__ == "__main__":
    unittest.main()
