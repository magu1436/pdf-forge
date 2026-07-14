

from pathlib import Path


def save(data: bytes, output_path: Path) -> None:
    """
    指定した `data` を `output_path` に保存する。  
    同名のファイルが存在する場合は上書きする。
    """
    output_path.write_bytes(data)