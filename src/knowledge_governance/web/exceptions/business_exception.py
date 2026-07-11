class BusinessException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "BUSINESS_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class NotFoundError(BusinessException):
    def __init__(self, message: str):
        super().__init__(message, 404, "NOT_FOUND")


class ConflictError(BusinessException):
    def __init__(self, message: str):
        super().__init__(message, 409, "CONFLICT")
