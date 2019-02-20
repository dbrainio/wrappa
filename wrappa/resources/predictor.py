import importlib.util

import asyncio


class Predictor:
    @classmethod
    async def create(cls, config):
        self = Predictor(config)
        self._queue = asyncio.Queue()
        asyncio.ensure_future(self.start_pooling())
        return self

    def __init__(self, config):
        # Dynamically import package
        spec = importlib.util.spec_from_file_location(
            'DSModel', config['model_path'])
        ds_lib = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ds_lib)
        # Init ds model
        self._ds_model = ds_lib.DSModel(**config['config'])

    async def start_pooling(self):
        requests_with_json = []
        requests_without_json = []
        while True:
            try:
                # print('Pooling :: Waiting from queue')
                request = self._queue.get_nowait()
                # print('Pooling :: Got value from queue ::', request)
                if request[-1]:
                    requests_with_json.append(request[:-1])
                else:
                    requests_without_json.append(request[:-1])
            except asyncio.QueueEmpty:
                # print('Pooling :: Exception from queue')
                await asyncio.sleep(0.05)
                # print(requests_with_json, requests_without_json)
                # Execute task
                res1, res2 = [], []
                if requests_with_json:
                    res1 = await self._predict([x[1] for x in requests_with_json], True)

                if requests_without_json:
                    res2 = await self._predict([x[1] for x in requests_without_json], False)
               
                # print(res1, res2)
                if res1 is not None:
                    for res, (queue, _) in zip(res1, requests_with_json):
                        # print('Pooling :: in res1', queue)
                        queue.put_nowait(res)
               
                if res2 is not None:
                    for res, (queue, _) in zip(res2, requests_without_json):
                        # print('Pooling :: in res2', queue)
                        queue.put_nowait(res)

                requests_with_json = []
                requests_without_json = []

    async def _predict(self, data, is_json):
        f_kwargs = {}
        if 'as_json' in self._ds_model.predict.__code__.co_varnames:
            f_kwargs['as_json'] = is_json or False
        
        if asyncio.iscoroutinefunction(self._ds_model.predict):
            res = await self._ds_model.predict(data, **f_kwargs)
        else:
            res = self._ds_model.predict(data, **f_kwargs)
        
        return res
    
    async def predict(self, data, is_json):
        queue = asyncio.Queue(maxsize=1)
        # print('Putting in queue')
        self._queue.put_nowait((queue, data, is_json))
        # print('Waiting from queue')
        resp = await queue.get()
        # print('Got from queue')
        return resp
