import json
from typing import *

from aiohttp import web
import consul


from .resources import Healthcheck, Predict

class App:
    def __init__(
        self,
        debug=False,
        disable_consul=False,
        max_request_size=1024**2*10, # 10 Mb by default
        **kwargs
    ):

        # Parse kwargs
        self._port = kwargs['port']
        self._debug = debug

        if not disable_consul:
            try:
                self._register_consul(kwargs)
            except Exception as e:
                if not self._debug:
                    raise e
                else:
                    print('[Warning] Missing consul config')

        app = web.Application(
            debug=self._debug,
            client_max_size=max_request_size
        )
        # TODO: figure out what to do with timeout

        healthchecker = Healthcheck()
        predictor = Predict(**kwargs)

        app.add_routes([web.get('/healthcheck', healthchecker.get)])
        app.add_routes([web.post('/predict', predictor.post)])

        for path in kwargs.get('ds_model_config', {}).get('predict_aliases', []):
            app.add_routes([web.post(path, predictor.post)])

        self._app = app

    @staticmethod
    def _register_consul(config):
        consul_config = config.get('consul')
        if consul_config is None:
            raise EnvironmentError('missing consul in config')

        server_info = config['server_info']
        server_name = server_info['name']

        _consul = consul.Consul(consul_config['host'], consul_config['port'])

        _consul.agent.service.deregister(server_name)
        _consul.agent.service.register(
            name=server_name,
            service_id=server_name,
            port=config['port'],
            tags=['ds'],
            check=consul.Check.http(server_info['address'] + '/healthcheck',
                                    interval='5s')
        )

        _consul.kv.put(server_name, json.dumps(server_info))

    @property
    def app(self):
        return self._app

    def start(self):
        web.run_app(self.app, host='0.0.0.0', port=self._port)
