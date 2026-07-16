from __future__ import annotations

import tempfile
import weakref
from pathlib import Path


class TemporaryPDFFile:
    """名前付き一時PDFファイルを所有し、解放時に削除する。"""

    def __init__(self) -> None:
        path = TemporaryPDFFile._create_empty_temporary_pdf_file()

        self._path = path
        self._finalizer = weakref.finalize(
            self,
            TemporaryPDFFile._delete,
            path,
        )
    
    def overwrite(self, data: bytes) -> None:
        if self.closed:
            raise RuntimeError("cannot overwrite a closed TemporaryPDFFile")

        try:
            replacement_path = TemporaryPDFFile._create_empty_temporary_pdf_file()
            replacement_path.write_bytes(data)
            replacement_path.replace(self._path)
        finally:
            if replacement_path.exists():
                TemporaryPDFFile._delete(replacement_path)
    
    @staticmethod
    def from_bytes(data: bytes) -> TemporaryPDFFile:
        temporary_file = TemporaryPDFFile()
        temporary_file.overwrite(data)
        return temporary_file

    @property
    def path(self) -> Path:
        """所有する一時ファイルのパスを返す。"""
        return self._path

    @property
    def closed(self) -> bool:
        """一時ファイルを解放済みかどうかを返す。"""
        return not self._finalizer.alive

    def close(self) -> None:
        """一時ファイルを削除する。解放済みの場合は何もしない。"""
        if not self._finalizer.alive:
            return

        self._delete(self._path)
        self._finalizer.detach()

    @staticmethod
    def _delete(path: Path) -> None:
        path.unlink(missing_ok=True)
    
    @staticmethod
    def _create_empty_temporary_pdf_file() -> Path:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as file:
            path = Path(file.name)
        return path