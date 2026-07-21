from collections.abc import Callable, Iterable
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def _write_pages(pdf: Path, output: Path, select_indices: Callable[[int], Iterable[int]]) -> None:
    with PdfReader(pdf) as reader:
        indices = select_indices(len(reader.pages))
        with PdfWriter() as writer:
            for index in indices:
                writer.add_page(reader.pages[index])
            writer.write(output)


def _normalize_index(index: int, page_count: int) -> int:
    normalized_index = index + page_count if index < 0 else index
    if normalized_index < 0 or normalized_index >= page_count:
        raise IndexError("page index out of range")
    return normalized_index


def extract_multiple_pages(
    pdf: Path,
    output: Path,
    start: int = 0,
    stop: int | None = None,
    step: int = 1,
) -> None:
    _write_pages(
        pdf,
        output,
        lambda page_count: range(*slice(start, stop, step).indices(page_count)),
    )


def extract_page(pdf: Path, output: Path, index: int) -> None:
    _write_pages(pdf, output, lambda page_count: [_normalize_index(index, page_count)])


def delete_multiple_pages(pdf: Path, output: Path, start: int = 0, stop: int | None = None) -> None:
    def select_indices(page_count: int) -> Iterable[int]:
        deleted_indices = range(*slice(start, stop).indices(page_count))
        return (index for index in range(page_count) if index not in deleted_indices)

    _write_pages(pdf, output, select_indices)


def delete_page(pdf: Path, output: Path, index: int) -> None:
    def select_indices(page_count: int) -> Iterable[int]:
        deleted_index = _normalize_index(index, page_count)
        return (page_index for page_index in range(page_count) if page_index != deleted_index)

    _write_pages(pdf, output, select_indices)

def get_page_count(pdf: Path) -> int:
    with PdfReader(pdf) as reader:
        return len(reader.pages)