from aiohttp import web

def abort(http_code, message):
    resp = {
        'code': http_code,
        'message': message,
    }
    return web.json_response(data=resp, status=http_code)