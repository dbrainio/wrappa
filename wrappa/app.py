import json
# import asyncio

from aiohttp import web
# from flask import Flask
# from flask_restful import Api
import consul


from .resources import Healthcheck, Predict


# class UnicodeApi(Api):
#     def __init__(self, *args, **kwargs):
#         super(UnicodeApi, self).__init__(*args, **kwargs)
#         self.app.config['RESTFUL_JSON'] = {
#             'ensure_ascii': False
#         }


class App:
    def __init__(self, debug=False, disable_consul=False, timeout=None, **kwargs):

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

        app = web.Application()
        # app = Flask(__name__)
        # if timeout is not None:
        #     app.config.update(PERMANENT_SESSION_LIFETIME=timeout)
        # api = UnicodeApi(app)

        healthchecker = Healthcheck()
        predictor = Predict(**kwargs)

        app.add_routes([web.get('/healthcheck', healthchecker.get)])
        app.add_routes([web.post('/predict', predictor.post)])

        # api.add_resource(Healthcheck, '/healthcheck')
        # api.add_resource(, '/predict')

        # self._api = api
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
        # self._app.run(host='0.0.0.0', port=self._port,
        #               debug=self._debug, use_reloader=False)
