import uuid
from functools import wraps

from aiohttp import web
from aiojobs.aiohttp import spawn

ASYNC_TASKS = dict()


def abort(http_code, message):
    resp = {
        'code': http_code,
        'message': message,
    }
    return web.json_response(data=resp, status=http_code)


def asyncable(func):
    @wraps(func)
    async def wrapper(obj, request, *args, **kw):
        task = func(obj, request, *args, **kw)
        if request.query.get('async', 'false') != 'true':
            return await task
        task_id = str(uuid.uuid4())
        ASYNC_TASKS[task_id] = await spawn(request, task)
        return web.json_response(data={'task_id': task_id})

    return wrapper


async def get_task_result(task_id):
    if task_id not in ASYNC_TASKS:
        return web.json_response(data={
            'success': False,
            'error': 'not found',
        }, status=404)
    task = ASYNC_TASKS[task_id]
    if not task.closed:
        return web.json_response(data={
            'success': False,
            'error': 'not done',
        }, status=200)
    try:
        return await task.wait()
    except Exception as e:
        return web.json_response(data={
            'success': False,
            'error': str(e),
        }, status=500)
    finally:
        del ASYNC_TASKS[task_id]
