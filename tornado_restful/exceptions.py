from tornado_restful import status


class APIException(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Internal Server Error"

    def __init__(self, detail: dict = None) -> None:
        self.detail = detail


class BadRequestError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    message = "Bad Request"


class UnauthorizedError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Unauthorized"


class ForbiddenError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    message = "Forbidden"


class NotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Not Found"


class MethodNotAllowedError(APIException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    message = "Method Not Allowed"


class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    message = "Conflict"
