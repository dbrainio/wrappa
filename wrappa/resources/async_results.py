from wrappa.common.http_utils import get_task_result


class AsyncResults:
    def __init__(self):
        pass

    @staticmethod
    async def get(request):
        task_id = request.match_info['task_id']
        return await get_task_result(task_id)
