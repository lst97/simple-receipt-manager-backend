class ValidationError(Exception):
    """Base class for validation errors."""
    pass


class InvalidRequestIdError(ValidationError):
    def __init__(self, request_id):
        self.request_id = request_id
        super().__init__(f"Request ID '{request_id}' is invalid.")


class InvalidFileNameError(ValidationError):
    def __init__(self, file_name):
        self.file_name = file_name
        super().__init__(f"File name '{file_name}' is invalid.")


class InvalidNumberError(ValidationError):
    def __init__(self, number):
        self.number = number
        super().__init__(f"Number '{number}' is invalid.")


class InvalidFileError(ValidationError):
    def __init__(self, file_name):
        self.file_name = file_name
        super().__init__(f"File '{file_name}' is invalid.")
