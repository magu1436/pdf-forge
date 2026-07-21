from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import overload

from src.common.type import Pathish

from .pypdf_tool import (
    copy,
    extract_multiple_pages,
    extract_page,
    get_page_count,
    merge_multiple_pdf,
)
from .temporary_pdf_file import TemporaryPDFFile


class PDFError(Exception):
    """PDFの高水準操作に失敗した場合に送出する例外。"""


class PDF:
    """1つのPDF文書と、その一時ファイルの所有権を表す。"""

    def __init__(self) -> None:
        self._path: Path | None = None
        self._temporary: TemporaryPDFFile | None = None

    def save(
        self,
        destination_dir: Pathish | None = None,
        output_file_name: str | None = None,
    ) -> Path:
        source = self.path()
        destination = self._resolve_destination(
            source,
            destination_dir,
            output_file_name,
        )

        if self._is_same_path(source, destination):
            if self._temporary is not None:
                raise ValueError("a temporary PDF must be saved to a different path")
            return destination

        try:
            copy(source, destination)
        except Exception as error:
            raise PDFError(f"failed to save PDF to {destination}") from error

        previous_temporary = self._temporary
        self._path = destination
        self._temporary = None

        if previous_temporary is not None:
            previous_temporary.close()

        return destination

    def merge(self, other: PDF, overwrite: bool = False) -> PDF:
        if not isinstance(other, PDF):
            raise TypeError("other must be a PDF")

        source = self.path()
        other_source = other.path()
        merged = self._create_temporary_pdf(
            lambda output: merge_multiple_pdf(
                [source, other_source],
                output,
            )
        )

        if not overwrite:
            return merged

        previous_temporary = self._temporary
        self._path = merged._path
        self._temporary = merged._temporary
        # merged._path = None
        # merged._temporary = None

        if previous_temporary is not None:
            previous_temporary.close()

        return self

    @overload
    def __getitem__(self, index: int) -> PDF: ...

    @overload
    def __getitem__(self, index: slice) -> PDF: ...

    def __getitem__(self, index: int | slice) -> PDF:
        source = self.path()

        # if isinstance(index, bool):
        #     raise TypeError("page index must be an integer or slice")

        if isinstance(index, int):
            return self._create_temporary_pdf(
                lambda output: extract_page(source, output, index)
            )

        if not isinstance(index, slice):
            raise TypeError("page index must be an integer or slice")

        start, stop = self._normalize_slice(index)
        return self._create_temporary_pdf(
            lambda output: extract_multiple_pages(
                source,
                output,
                start=start,
                stop=stop,
            )
        )

    def __len__(self) -> int:
        path = self.path()
        try:
            return get_page_count(path)
        except Exception as error:
            raise PDFError(f"failed to get page count for {path}") from error

    def _normalize_slice(self, index: slice) -> tuple[int, int]:
        if index.step not in (None, 1):
            raise ValueError("slice step must be None or 1")

        for value in (index.start, index.stop):
            if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
                raise TypeError("slice indices must be integers or None")

        page_count = len(self)
        start = 0 if index.start is None else index.start
        stop = page_count - 1 if index.stop is None else index.stop

        if start < 0:
            start += page_count
        if stop < 0:
            stop += page_count

        start = min(max(start, 0), page_count)
        exclusive_stop = min(max(stop + 1, 0), page_count)

        if start >= exclusive_stop:
            raise ValueError("slice selects no pages")

        return start, exclusive_stop

    def _resolve_destination(
        self,
        source: Path,
        destination_dir: Pathish | None,
        output_file_name: str | None,
    ) -> Path:
        directory = source.parent
        if destination_dir is not None:
            directory = Path(destination_dir)
            if not directory.exists():
                raise FileNotFoundError(f"destination directory does not exist: {directory}")
            if not directory.is_dir():
                raise NotADirectoryError(f"destination is not a directory: {directory}")

        file_name = source.name if output_file_name is None else output_file_name
        if output_file_name is not None:
            if not isinstance(output_file_name, str):
                raise TypeError("output_file_name must be a string or None")

            candidate = Path(output_file_name)
            if candidate.is_absolute() or candidate.parent != Path(".") or candidate.name != output_file_name:
                raise ValueError("output_file_name must contain only a file name")
            if candidate.suffix != ".pdf":
                raise ValueError("output_file_name must have a .pdf suffix")

        return directory / file_name

    def _create_temporary_pdf(self, write: Callable[[Path], object]) -> PDF:
        temporary = TemporaryPDFFile()
        try:
            write(temporary.path)
        except (IndexError, TypeError, ValueError):
            temporary.close()
            raise
        except Exception as error:
            temporary.close()
            raise PDFError("failed to create temporary PDF") from error

        result = PDF()
        result._path = temporary.path
        result._temporary = temporary
        return result

    def path(self) -> Path:
        if self._path is None:
            raise ValueError("PDF does not contain a document")
        return self._path

    @staticmethod
    def _is_same_path(left: Path, right: Path) -> bool:
        
        return left.resolve(strict=False) == right.resolve(strict=False)


__all__ = ["PDF", "PDFError"]
