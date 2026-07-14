# `PDF` オブジェクト仕様

## 1. 目的

`PDF` は、PDF文書の読み込み、ページ参照、結合、保存およびテキスト抽出などを、1つの文書オブジェクトを通じて行うための高水準APIである。

PyPDFの `PdfReader` と `PdfWriter` は実装詳細として利用する。既存PDFはパスで参照し、結合などで生成したPDFは自動削除される一時ファイルとして保持することで、文書全体を常時メモリへ保持しない。

```python
pdf = PDF().read("input.pdf")
appendix = PDF().read("appendix.pdf")

merged = pdf.merge(appendix)
output = merged.save(
    destination_dir="output",
    output_file_name="merged.pdf",
)
```

## 2. 設計原則

- `PDF` インスタンスは論理的に1つのPDF文書を表す。
- 既存ファイルは参照するだけであり、`PDF` はそのファイルを勝手に削除しない。
- 生成した文書は一時ファイルへ直接書き出し、`PDF` がその一時ファイルを所有する。
- `PDF` 自身はファイルハンドルやReaderを常時保持しない。
- ストリームとReaderが必要な処理では `PDF.open()` を使用する。
- 一時ファイルの明示的な解放は内部実装が担当し、公開 `PDF` APIに `close()` は設けない。
- 文書を生成する操作は、明示的に上書きを指定しない限り元の `PDF` を変更しない。

## 3. 一時ファイル所有者

生成されたPDFの保存先と寿命は、内部クラス `TemporaryPDFFile` が管理する。

```python
class TemporaryPDFFile:
    _path: Path
    _finalizer: weakref.finalize
```

`TemporaryPDFFile` の責務は次の通りとする。

- `.pdf` の接尾辞を持つ名前付き一時ファイルを作成する。
- 作成時のファイルハンドルを閉じ、パスから再度開ける状態にする。
- 読み取り専用の `path` プロパティを提供する。
- 解放済みかを示す読み取り専用の `closed` プロパティを提供する。
- 内部 `close()` により所有するファイルを削除する。
- `close()` を複数回呼んでも安全な、冪等な解放処理を提供する。
- 所有者への参照がなくなった場合、`weakref.finalize` により削除を試みる。

ファイナライザーのコールバックは所有者自身を強参照してはならない。静的メソッドまたはクラス外関数へ、削除対象の `Path` だけを渡す。

```python
self._finalizer = weakref.finalize(
    self,
    TemporaryPDFFile._delete,
    path,
)
```

一時ファイルは `delete=False` で作成する。これは、作成時のハンドルを閉じた後にPyPDFがパスからファイルを開けるようにするためである。

## 4. `PDF` の内部属性

```python
_path: Path | None
_temporary: TemporaryPDFFile | None
```

### `_path`

現在のPDF文書が存在するファイルのパスを保持する。

- 通常ファイルと一時ファイルの両方で使用する。
- 内容を持たないPDFでは `None` とする。
- 一時ファイルの場合は `_temporary.path` と同じパスを保持する。

### `_temporary`

現在のPDF文書が一時ファイルである場合に、その所有者を保持する。

- 通常ファイル参照時は `None` とする。
- 値を持つ場合、`PDF` はその一時ファイルを削除する責任を持つ。
- `_temporary` への強参照により、`PDF` の利用中に一時ファイルがGCで削除されることを防ぐ。

PDF本体を保持する `_data` 属性は設けない。

## 5. 状態と不変条件

| 状態 | `_path` | `_temporary` | 意味 |
| --- | --- | --- | --- |
| 空 | `None` | `None` | 文書を参照していない |
| 通常ファイル参照 | `Path` | `None` | 外部が所有するファイルを参照する |
| 一時ファイル所有 | `Path` | `TemporaryPDFFile` | `PDF` が一時ファイルを所有する |

常に次の不変条件を満たす。

```python
if self._temporary is not None:
    assert self._path == self._temporary.path
    assert not self._temporary.closed
```

空状態で内容を必要とする操作を行った場合は `ValueError` を送出する。

## 6. 公開API

```python
from contextlib import AbstractContextManager
from os import PathLike
from pathlib import Path
from typing import Self

from pypdf import PageObject, PdfReader

type Pathish = str | PathLike[str]


class PDF:
    def __init__(self) -> None: ...

    def read(self, source: Pathish) -> Self: ...

    def open(self) -> AbstractContextManager[PdfReader]: ...

    def save(
        self,
        destination_dir: Pathish | None = None,
        output_file_name: str | None = None,
    ) -> Path: ...

    def merge(
        self,
        other: "PDF",
        overwrite: bool = False,
    ) -> "PDF": ...

    def __getitem__(self, index: int) -> PageObject: ...

    def __len__(self) -> int: ...
```

`PDF` 自身には `close()`、`closed`、`__enter__()`、`__exit__()` を設けない。コンテキスト管理の対象は、`open()` が生成するReaderセッションである。

## 7. 読み込み

### `pdf.read(source)`

現在のインスタンスを通常ファイル参照状態へ移し、そのインスタンス自身を返す。

```python
pdf = PDF()
same_pdf = pdf.read("document.pdf")

assert same_pdf is pdf
```

処理要件は次の通りとする。

- `str` および `PathLike[str]` を受け付ける。
- パスが存在し、通常ファイルであり、PDFとして開けることを検証する。
- 成功後は `_path = Path(source)`、`_temporary = None` とする。
- 以前の状態が一時ファイル所有状態なら、検証成功後に以前の一時ファイルを解放する。
- 戻り値は `self` とする。
- パスが存在しない場合は `FileNotFoundError` を送出する。
- 不正なPDFではPyPDF由来の例外をそのまま送出してよい。
- 失敗した場合は、呼び出し前の状態と一時ファイルを維持する。

読み込み時点でファイル全体をメモリまたは別の一時ファイルへ複製しない。

## 8. Readerセッション

### `pdf.open()`

現在のPDFを読むための `PdfReader` を提供するコンテキストマネージャーを返す。

```python
with pdf.open() as reader:
    text = reader.pages[0].extract_text()
```

処理要件は次の通りとする。

- `with` へ入る際に `_path` をバイナリ読み込みモードで開き、`PdfReader` を生成する。
- `with` ブロックには `PdfReader` を渡す。
- ブロック終了時に、例外の有無にかかわらず入力ストリームを閉じる。
- ブロック内の例外を抑制しない。
- セッションの存続中は元の `PDF` と `_temporary` を強参照し、一時ファイルが削除されないようにする。
- 返されたReaderと、そのReaderに依存する `PageObject` は原則として `with` ブロック内だけで使用する。
- 空状態では `ValueError` を送出する。

`open()` は生のストリームではなく、組み立て済みの `PdfReader` を提供する。PyPDFを直接利用した複数ページ処理では同じReaderを使い回せる。

```python
with pdf.open() as reader:
    texts = [page.extract_text() or "" for page in reader.pages]
```

テキスト抽出などの高水準メソッドを将来追加する場合、その内部でも `open()` を使用する。

## 9. ページ参照

### `pdf[index]`

0始まりのページ番号を整数で指定し、対応する `PageObject` を返す。

```python
first_page = pdf[0]
last_page = pdf[-1]
```

- Pythonのシーケンスと同様に負数インデックスを許可する。
- 範囲外では `IndexError`、`int` 以外では `TypeError` を送出する。
- 初期仕様ではスライスをサポートしない。
- `open()` の外へ返すため、ページと必要な関連オブジェクトを元Readerから独立させる。

概念的には `PdfReader(self._path).pages[index]` に相当するが、入力ストリームを閉じた後も通常のページ操作ができる `PageObject` を返さなければならない。実装ではWriter側へページを複製するなどして依存関係を切り離す。

独立性をPyPDF上で保証できない場合は、生の `PageObject` を返さず、親PDFを強参照する専用ページ型へ仕様を変更する。

### `len(pdf)`

PDFの総ページ数を返す。内部では `open()` を使用し、ページ数はキャッシュしない。

## 10. 結合

### `pdf.merge(other, overwrite=False)`

呼び出し元の後ろに `other` の全ページを追加し、結合結果を表す `PDF` を返す。

```python
merged = pdf1.merge(pdf2)
```

共通要件は次の通りとする。

- ページ順は `self`、`other` の順とする。
- `other` が `PDF` でない場合は `TypeError` を送出する。
- 結合結果は新しい `TemporaryPDFFile` へ直接書き込む。
- 文書全体を中間的な `bytes` または `BytesIO` として保持しない。
- 結合に失敗した場合は処理途中の一時ファイルを削除し、両方の入力PDFを変更しない。
- 入力Reader、入力ストリーム、出力Writerおよび出力ストリームは、戻る前に閉じる。

#### `overwrite=False`

デフォルトの非破壊動作とする。

- `self` と `other` は変更しない。
- 結合結果を所有する新しい `PDF` を返す。
- 戻り値は `_path` に一時ファイルのパス、`_temporary` にその所有者を持つ。

```python
merged = pdf1.merge(pdf2)

assert merged is not pdf1
```

#### `overwrite=True`

結合結果で `self` の論理内容を置き換える。

- 結合が完全に成功するまでは `self` を変更しない。
- 成功後、`self._path` と `self._temporary` を新しい一時ファイルへ切り替える。
- `self` が以前に一時ファイルを所有していた場合は、切り替え後に古い一時ファイルを解放する。
- `self` が通常ファイルを参照していた場合、その元ファイル自体は変更しない。
- 戻り値は `self` とする。

```python
same_pdf = pdf1.merge(pdf2, overwrite=True)

assert same_pdf is pdf1
```

ここでの `overwrite` は `PDF` オブジェクトが表す論理内容の置き換えを意味し、ディスク上の既存ファイルの上書きは意味しない。既存ファイルへの書き出しは `save()` の責務とする。

## 11. 保存

### `pdf.save(destination_dir=None, output_file_name=None)`

現在のPDF内容を恒久ファイルへ保存し、保存先の `Path` を返す。

```python
path = pdf.save(
    destination_dir="output",
    output_file_name="result.pdf",
)
```

### 保存先の解決

保存先は次の規則で決定する。

| `destination_dir` | `output_file_name` | 保存先 |
| --- | --- | --- |
| 指定あり | 指定あり | `Path(destination_dir) / output_file_name` |
| 指定あり | `None` | `Path(destination_dir) / self._path.name` |
| `None` | 指定あり | `self._path.parent / output_file_name` |
| `None` | `None` | 現在の `self._path` |

追加要件は次の通りとする。

- `destination_dir` は既存のディレクトリでなければならない。初期仕様では自動作成しない。
- `output_file_name` はファイル名だけを受け付け、絶対パスや親ディレクトリ要素を含んではならない。
- `output_file_name` の拡張子が `.pdf` でない場合の自動補完は行わず、`ValueError` を送出する。
- 保存先が既に存在する場合は上書きする。
- 既存ファイルの上書きは、同一ディレクトリの別一時ファイルへ書き込み、成功後にアトミックに置換する。
- 保存に失敗した場合は既存ファイルを維持し、`PDF` の状態も変更しない。

一時ファイル所有状態で解決結果が現在の一時ファイル自身になる場合は `ValueError` を送出する。一時ファイルを恒久ファイルとして扱うには、少なくとも保存先ディレクトリまたは出力ファイル名を変更する必要がある。

一時ファイル所有状態から保存に成功した場合は、次の順序で通常ファイル参照状態へ移行する。

1. 保存先への書き込みと置換が完了したことを確認する。
2. `_path` を保存先へ変更する。
3. `_temporary` を `None` にする。
4. 以前の `TemporaryPDFFile` を内部 `close()` で解放する。

通常ファイルを別名保存した場合も、成功後は保存先を現在の参照先とする。保存後の `PDF` は常に返された `Path` と同じファイルを参照する。

## 12. 一時ファイルの解放とGC

`PDF` は公開 `close()` を持たない。一時ファイルは次のタイミングで内部的に解放する。

- `read()` の成功によって別の通常ファイルへ切り替えたとき。
- `merge(..., overwrite=True)` の成功によって別の一時ファイルへ切り替えたとき。
- `save()` の成功によって恒久ファイルへ移行したとき。
- 処理途中で作成した一時ファイルが、例外により不要になったとき。
- 所有する `PDF` と `TemporaryPDFFile` への参照がなくなり、ファイナライザーが実行されたとき。

GCによる削除は最終的な保険であり、実行時刻を保証しない。Windowsでは別のReaderやプロセスがファイルを開いていると削除に失敗するため、すべてのストリームを閉じてから明示的な内部解放を行う。

ファイナライザー内の削除失敗は呼び出し元へ返せない。初期仕様では永続的な再試行を必須とせず、必要に応じてログへ記録する。

## 13. ファイル参照と所有権

通常ファイル参照状態の `PDF` は、内容のスナップショットではなくパスによる参照である。外部プロセスがファイルを書き換えた場合、後続操作は新しい内容を参照し得る。

一時ファイル所有状態のパスは内部実装用である。パスだけを外部へ渡しても所有権は移動せず、利用者が直接移動、置換または削除してはならない。

同じ一時ファイルを複数の `TemporaryPDFFile` が削除対象として所有してはならない。

## 14. 初期仕様の対象外

- 暗号化PDFのパスワード管理
- スライスによる複数ページ抽出
- ページの代入および削除
- 遅延した結合処理グラフ
- 非同期I/O
- URLやクラウドストレージからの直接読み込み
- 複数プロセスによる同時編集の排他制御
- GC時の削除失敗に対する永続的な再試行

これらを追加する場合も、通常ファイルと一時ファイルの所有権、Readerセッションの寿命、および上書き処理の原子性を曖昧にしない。
