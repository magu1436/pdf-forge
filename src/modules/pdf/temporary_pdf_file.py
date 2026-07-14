import tempfile
import weakref
from pathlib import Path


class TemporaryPDFFile:
    """名前付き一時PDFファイルを所有し、解放時に削除する。"""

    def __init__(self, data: bytes) -> None:
        temporary_file = tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
        )
        path = Path(temporary_file.name)

        try:
            temporary_file.write(data)
        except BaseException:
            temporary_file.close()
            path.unlink(missing_ok=True)
            raise
        else:
            temporary_file.close()

        self._path = path
        self._finalizer = weakref.finalize(
            self,
            TemporaryPDFFile._delete,
            path,
        )

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
        self._finalizer()

    @staticmethod
    def _delete(path: Path) -> None:
        path.unlink(missing_ok=True)
