# pdf-forge

`pdf-forge` は、PDFの結合やページ抽出をオブジェクト指向のAPIで扱うためのPythonプロジェクトです。
内部では [`pypdf`](https://pypdf.readthedocs.io/) を使用し、ファイルやReader／Writerの管理を `PDF` クラスにまとめています。

## 主な機能

- PDF同士の結合
- 1ページまたは複数ページの抽出
- ページ数の取得
- 処理結果を一時PDFとして管理
- 任意のディレクトリ・ファイル名への保存

## 必要環境

- Python 3.13以上
- [uv](https://docs.astral.sh/uv/)

## セットアップ

```bash
uv sync
```

## クイックスタート

```python
from pathlib import Path

from src.modules.pdf import PDF


input_dir = Path("input")
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

document = PDF(input_dir / "document.pdf")
appendix = PDF(input_dir / "appendix.pdf")

merged = document + appendix
merged.save(output_dir, "merged.pdf")
```

`merge()` やページ抽出の結果は一時PDFです。必要な結果は `save()` で永続ファイルとして保存してください。

## PDFオブジェクトの作成

既存のPDFファイルは、コンストラクタへパスを渡して参照します。`str` と `PathLike[str]` を使用できます。

```python
from pathlib import Path

from src.modules.pdf import PDF


pdf_from_string = PDF("docs/document.pdf")
pdf_from_path = PDF(Path("docs/document.pdf"))
```

引数なしの `PDF()` は、まだ文書を参照していない空のオブジェクトを作成します。空の状態でページ数取得、抽出、結合、保存を行うと `ValueError` が発生します。

## PDFの結合

### `merge()` を使う

```python
merged = first.merge(second)
```

デフォルトでは `first` と `second` を変更せず、結合結果を持つ新しい `PDF` を返します。

`overwrite=True` を指定すると、`first` の論理的な内容を結合結果で置き換え、`first` 自身を返します。元のディスク上のPDFファイルは、`save()` を呼ぶまで上書きされません。

```python
first.merge(second, overwrite=True)
```

### `+` 演算子を使う

`+` は `merge()` の非破壊操作と同じです。

```python
merged = first + second
```

## ページの抽出

ページ番号は0から始まります。整数を指定すると、その1ページだけを含む新しい `PDF` を返します。

```python
first_page = pdf[0]
last_page = pdf[-1]
```

複数ページはスライスで指定できます。

```python
first_three_pages = pdf[:2]  # インデックス0、1、2
middle_pages = pdf[1:3]      # インデックス1、2、3
remaining_pages = pdf[2:]    # インデックス2から最終ページ
```

> [!IMPORTANT]
> このAPIのスライスでは `stop` のページも抽出範囲に含まれます。通常のPythonスライスが終端を含まない点とは異なります。また、`step` は `None` または `1` のみ使用できます。

抽出元のPDFは変更されません。抽出結果を残す場合は保存します。

```python
extracted = pdf[1:3]
extracted.save("output", "pages-2-to-4.pdf")
```

## ページ数とファイルパス

```python
page_count = len(pdf)
current_path = pdf.path()
```

`path()` は、現在参照しているPDFファイルの `Path` を返します。空の `PDF` では `ValueError` が発生します。

## 保存

```python
saved_path = pdf.save(
    destination_dir="output",
    output_file_name="result.pdf",
)
```

- 戻り値は保存先の `Path` です。
- 保存先ディレクトリは事前に作成されている必要があります。
- `output_file_name` にはディレクトリを含まない `.pdf` ファイル名を指定します。
- 同名のファイルが存在する場合は置き換えます。
- 保存後の `PDF` は保存先ファイルを参照します。
- 一時PDFを保存すると、内部の一時ファイルは解放されます。

引数を一部省略した場合は、現在参照しているパスから保存先を補います。

| `destination_dir` | `output_file_name` | 保存先 |
| --- | --- | --- |
| 指定あり | 指定あり | `destination_dir / output_file_name` |
| 指定あり | `None` | `destination_dir / 現在のファイル名` |
| `None` | 指定あり | `現在のディレクトリ / output_file_name` |
| `None` | `None` | 現在のパス |

一時PDFは現在の一時ファイル自身へ保存できません。保存先ディレクトリまたはファイル名を指定してください。

## 主要API

| API | 戻り値 | 説明 |
| --- | --- | --- |
| `PDF(path)` | `PDF` | 既存のPDFファイルを参照するオブジェクトを作成します。 |
| `PDF()` | `PDF` | 文書を参照していない空のオブジェクトを作成します。 |
| `pdf.merge(other, overwrite=False)` | `PDF` | 2つのPDFを順番に結合します。 |
| `pdf + other` | `PDF` | 非破壊で2つのPDFを結合します。 |
| `pdf[index]` | `PDF` | 指定した1ページを抽出します。 |
| `pdf[start:stop]` | `PDF` | `stop` を含む範囲のページを抽出します。 |
| `len(pdf)` | `int` | ページ数を返します。 |
| `pdf.path()` | `Path` | 現在参照しているPDFのパスを返します。 |
| `pdf.save(destination_dir=None, output_file_name=None)` | `Path` | PDFを保存し、保存先を返します。 |

## pypdfの警告について

入力PDFの内部構造に不整合がある場合、結合時に次のような警告が表示されることがあります。

```text
Ignoring wrong pointing object ...
```

これは `PdfWriter.append()` が内部で入力PDFを読み込み、不正な相互参照情報を無視したことを示す警告です。結合結果を確認できている場合でも、必要に応じて入力PDFをPDFビューアーで再保存し、内部構造を再生成してください。

## テスト

```bash
uv run python -m unittest
```
