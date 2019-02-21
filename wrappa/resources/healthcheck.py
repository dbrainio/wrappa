from aiohttp import web


class Healthcheck:

    def __init__(self):
        pass

    @staticmethod
    async def get(_request):
        return web.Response(body=None, status=204)
