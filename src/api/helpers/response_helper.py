import uuid
from datetime import datetime


class Pagination:
    def __init__(self, page, limit, total):
        self.page = page
        self.limit = limit
        self.total = total

    def to_json(self):
        return {
            'page': self.page,
            'limit': self.limit,
            'total': self.total
        }


class MetaData:
    def __init__(self):
        self.timestamp = datetime.now()
        self.request_id = str(uuid.uuid4())

    def to_json(self):
        return {
            'timestamp': self.timestamp,
            'request_id': self.request_id
        }


class ResponseHelper:
    def __init__(self, status_code, message, data=None, pagination=None, meta_data=None):
        self.status_code = status_code
        self.message = message
        self.data = data
        self.pagination = pagination
        self.meta_data = meta_data

    def to_json(self):
        return {
            'status_code': self.status_code,
            'message': self.message,
            'data': self.data,
            'pagination': self.pagination,
            'meta_data': self.meta_data
        }


class ResponseType:
    SUCCESS = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


class ResponseMessage:
    SUCCESS = "Success"
    CREATED = "Created"
    ACCEPTED = "Accepted"
    NO_CONTENT = "No Content"
    BAD_REQUEST = "Bad Request"
    UNAUTHORIZED = "Unauthorized"
    FORBIDDEN = "Forbidden"
    NOT_FOUND = "Not Found"
    CONFLICT = "Conflict"
    INTERNAL_SERVER_ERROR = "Internal Server Error"
    NOT_IMPLEMENTED = "Not Implemented"
    SERVICE_UNAVAILABLE = "Service Unavailable"
    GATEWAY_TIMEOUT = "Gateway Timeout"
