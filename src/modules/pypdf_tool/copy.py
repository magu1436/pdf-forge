
import shutil
from pathlib import Path

from src.modules.temporary_pdf_file import TemporaryPDFFile
from .errors import CopyPDFError


def copy(src: Path, output_path: Path) -> None:
    """
    指定された `src` を `output_path` へ保存する。  
    同名のファイルが存在する場合は上書きする。
    """
    temp_pdf = TemporaryPDFFile()
    try:
        shutil.copyfile(src, temp_pdf.path)
        temp_pdf.path.replace(output_path)
    except Exception:
        raise CopyPDFError(f"Failed to copy {src} to {output_path}")
    temp_pdf.close()
