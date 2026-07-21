
import shutil
from pathlib import Path


def copy(src: Path, output_path: Path) -> None:
    """
    指定された `src` を `output_path` へ保存する。  
    同名のファイルが存在する場合は上書きする。
    """
    shutil.copyfile(src, output_path)