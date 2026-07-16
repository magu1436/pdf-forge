from pathlib import Path
from typing import Sequence

from pypdf import PdfWriter


def merge_multiple_pdf(pdfs: Sequence[Path], output: Path) -> Path:
    """複数のPDFを指定された順序で結合し、出力先のPDFを置き換える。

    ``output`` に存在するPDFは、結合結果で上書きされる。

    Args:
        pdfs: 結合するPDFファイルのパス。リストの順序で結合される。
        output: 結合結果を書き込むPDFファイルのパス。

    Returns:
        結合結果を書き込んだPDFファイルのパス。
    """
    with PdfWriter() as merger:
        for pdf in pdfs:
            merger.append(pdf)
        merger.write(output)
    return output
