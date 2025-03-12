class UnderDocException(Exception):
    """Base exception for UnderDoc."""
    pass

class UnderDocUnsupportedFileFormatException(UnderDocException):
    """Exception raised when an unsupported file format is provided."""
    pass
