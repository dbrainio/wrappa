import importlib.util
import traceback

import asyncio

from .requests_manager import RequestsManager

path2def_name = lambda path: path.strip('/').replace('/', '_')

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
        self._requests_manager = RequestsManager()

    async def start_pooling(self):
        while True:
            try:
                request = self._queue.get_nowait()
                self._requests_manager[request[-2:]].append(request[:-2])
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.05)
                
                for key, data in self._requests_manager.items():
                    try:
                        predicts = await self._predict([x[1] for x in data], key[1], key[0])
                    except Exception as e:
                        trace = traceback.format_exc()
                        predicts = [(e, trace) for _ in data]
                    self._requests_manager[key] = [
                        (queue, predict)
                        for predict, (queue, _) in zip(predicts, self._requests_manager[key]) 
                    ]
                
                for predicts in self._requests_manager.values():
                    for queue, predict in predicts:
                        queue.put_nowait(predict)
                self._requests_manager.clear()

    async def _predict(self, data, is_json: bool, predict_name: str):
        predict_method = (
            getattr(self._ds_model, predict_name) 
            if hasattr(self._ds_model, predict_name) 
            else self._ds_model.predict
        )
        f_kwargs = {}
        if 'as_json' in predict_method.__code__.co_varnames:
            f_kwargs['as_json'] = is_json or False
        
        if asyncio.iscoroutinefunction(predict_method):
            res = await predict_method(data, **f_kwargs)
        else:
            res = predict_method(data, **f_kwargs)
        
        return res
    
    async def predict(self, data, is_json: bool, path: str):
        predict_name = path2def_name(path)
        queue = asyncio.Queue(maxsize=1)
        # print('Putting in queue')
        self._queue.put_nowait((queue, data, predict_name, is_json))
        # print('Waiting from queue')
        resp = await queue.get()
        # print('Got from queue')
        return resp
