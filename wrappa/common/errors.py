import functools
import inspect
import sys
import traceback

from .http_utils import abort

MIN_CUSTOM_ERRNO = 1000


class WrappaError(Exception):
    def __init__(self, http_code, message, errno):
        self.http_code = http_code
        self.message = message
        self.errno = errno
        self.exc_info = sys.exc_info()
        if self.exc_info[1] is None:
            self.tb = None
        else:
            self.tb = traceback.format_exc()


class BaseHTTPError:
    http_code = 400
    message = 'Bad request'
    errno = 0

    @classmethod
    def json_response(cls):
        tb = None
        v = sys.exc_info()[1]
        errno = cls.errno
        http_code = cls.http_code
        message = cls.message
        if isinstance(v, WrappaError):
            http_code = v.http_code
            message = v.message
            errno = v.errno
            tb = v.tb
            assert errno >= MIN_CUSTOM_ERRNO
        elif v is not None:
            tb = traceback.format_exc()
        return abort(http_code, message, errno, tb)

    @classmethod
    def if_failed(cls, func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except WrappaError as e:
                    return abort(e.http_code, e.message, e.errno)
                except:
                    return cls.json_response()
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except WrappaError as e:
                    return abort(e.http_code, e.message, e.errno)
                except:
                    return cls.json_response()
        return wrapper


class UnableToPrepareResponseError(BaseHTTPError):
    message = 'Unable to prepare response'
    errno = 1


class UnauthorizedError(BaseHTTPError):
    http_code = 401
    message = 'Unauthorized'
    errno = 2


class InvalidAcceptHeaderValueError(BaseHTTPError):
    message = 'Invalid Accept header value'
    errno = 3


class UnbaleToParseRequestError(BaseHTTPError):
    message = 'Unbale to parse request'
    errno = 4


class ForbiddenError(BaseHTTPError):
    http_code = 403
    message = 'Forbidden'
    errno = 5


class InvalidDataError(BaseHTTPError):
    message = 'Invalid data'
    errno = 6


class DSModelError(BaseHTTPError):
    message = 'DS model failed to process data'
    errno = 7


class AsyncTaskNotFoundError(BaseHTTPError):
    http_code = 404
    message = 'Async task not found'
    errno = 8


class AsyncTaskNotDoneError(BaseHTTPError):
    http_code = 200
    message = 'Async task not done'
    errno = 9


class AsyncTaskFailedError(BaseHTTPError):
    http_code = 500
    message = 'Async task failed'
    errno = 10


class HTTPRequestEntityTooLargeError(BaseHTTPError):
    message = 'HTTP request entity too large'
    errno = 11


class UnknownError(BaseHTTPError):
    http_code = 500
    message = 'Unknown error'
    errno = 100
