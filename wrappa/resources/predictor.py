import asyncio
import importlib.util
import traceback

from .requests_manager import RequestsManager

path2def_name = lambda path: path.strip('/').replace('/', '_')


class Predictor:
    @classmethod
    async def create(cls, config):
        self = cls(config)
        self._queue = asyncio.Queue()
        asyncio.ensure_future(self.start_pooling())
        return self

    def __init__(self, config):
        DSModel = config.get('model_class')
        if not DSModel:
            # Dynamically import package
            spec = importlib.util.spec_from_file_location(
                'DSModel', config['model_path'])
            ds_lib = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ds_lib)
            DSModel = ds_lib.DSModel
        # Init ds model
        self._ds_model = DSModel(**config['config'])
        self._requests_manager = RequestsManager()
        self._batch_size = config.get('batch_size', 4)

    async def start_pooling(self):
        while True:
            try:
                request = self._queue.get_nowait()
                self._requests_manager[request[-2:]].append(request[:-2])
                bs = self._batch_size
                tasks = sum(len(v) for v in self._requests_manager.values())
                if bs and tasks >= bs:
                    raise asyncio.QueueEmpty()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.05)

                for key, data in self._requests_manager.items():
                    try:
                        predicts = await self._predict(
                            [x[1] for x in data],
                            key[1],
                            key[0]
                        )
                        for x, predict in zip(data, predicts):
                            queue = x[0]
                            queue.put_nowait(predict)
                    except:
                        for x in data:
                            try:
                                predict = await self._predict(
                                    [x[1]],
                                    key[1],
                                    key[0]
                                )
                            except Exception as e:
                                trace = traceback.format_exc()
                                predict = e, trace
                            queue = x[0]
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
