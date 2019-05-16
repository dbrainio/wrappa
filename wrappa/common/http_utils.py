from aiohttp import web


def abort(http_code, message, errno=None, traceback=None):
    resp = {
        'code': http_code,
        'message': message,
        'errno': errno,
        'traceback': traceback
    }
    return web.json_response(data=resp, status=http_code)
