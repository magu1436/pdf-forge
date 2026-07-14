class PyPDFToolException(Exception):
    pass


class PDFValidationError(PyPDFToolException):
    """PDFの検証に失敗した場合に送出する例外。"""


class PDFFileNotFoundError(PDFValidationError):
    """検証対象のPDFファイルが存在しない場合に送出する例外。"""


class PDFNotAFileError(PDFValidationError):
    """検証対象のパスが通常ファイルでない場合に送出する例外。"""


class InvalidPDFError(PDFValidationError):
    """検証対象をPDFとして読み込めない場合に送出する例外。"""


class EncryptedPDFError(PDFValidationError):
    """検証対象のPDFが暗号化されている場合に送出する例外。"""
