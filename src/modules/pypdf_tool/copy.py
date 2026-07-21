import shutil
import tempfile
from pathlib import Path

from .errors import CopyPDFError


def copy(src: Path, output_path: Path) -> None:
    """PDFを一時ファイルへコピーし、成功後に出力先を置き換える。"""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        shutil.copyfile(src, temporary_path)
        temporary_path.replace(output_path)
    except Exception as error:
        raise CopyPDFError(f"Failed to copy {src} to {output_path}") from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
