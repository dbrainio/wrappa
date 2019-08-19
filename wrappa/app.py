import json
import argparse
import consul
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient

from .common import read_config
from .resources import Healthcheck, Predict
from .storage import FileStorage


class App:
    def __init__(
            self,
            debug=False,
            disable_consul=False,
            max_request_size=1024 ** 2 * 100,  # 100 Mb by default
            healthcheck_class=Healthcheck,
            predict_class=Predict,
            db=None,
            **kw
    ):
        if kw.get('server_info') and kw['server_info'].get('passphrase'):
            if isinstance(kw['server_info']['passphrase'], str):
                kw['server_info']['passphrase'] = [
                    kw['server_info']['passphrase']]

        if kw.get('storage'):
            if kw['storage'].get('files'):
                if kw['storage']['files'].get('path'):
                    kw['storage'] = FileStorage(
                        kw['storage']['files']['path'])
                else:
                    raise ValueError('Set path of files storage')

        if db:
            self._db = AsyncIOMotorClient(db)
        else:
            self._db = None

        # Parse kwargs
        self._port = kw['port']
        self._debug = debug

        if not disable_consul:
            try:
                self._register_consul(kw)
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

        healthchecker = healthcheck_class()
        predictor = predict_class(db=self._db, **kw)

        app.add_routes([web.get('/healthcheck', healthchecker.get)])
        app.add_routes([web.post('/predict', predictor.post)])
        app.add_routes([web.get('/result/{task_id}', predictor.result)])

        for path in kw.get('ds_model_config', {}).get('predict_aliases', []):
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

        _consul.kv.put(server_name, json.dumps(server_info, indent=4))

    @property
    def app(self):
        return self._app

    def start(self):
        web.run_app(self.app, host='0.0.0.0', port=self._port)


def run(ds_model=None, **kw):
    parser = argparse.ArgumentParser(description='Process config.yml file')
    parser.add_argument('--config', '-c', default='./config.yml',
                        help='path to config.yml (default: ./config.yml)')
    parser.add_argument('--passphrases', action='append', default=[],
                        help='path to file with passphrases (can be used multiple times)')
    parser.add_argument('--disable-consul', '-dc', action='store_true',
                        help='True to not to sync with consul (default: False)')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='True to run in debug mode (default: False)')
    parser.add_argument('--port', '-p', default=None,
                        help='Port of running server (default: None)')
    parser.add_argument('--db',
                        help='Database access details (only mongo for now)')

    args = parser.parse_args()
    config = read_config(args.config)

    if args.port is not None:
        config['port'] = args.port

    config.update(kw)

    for opt in ['debug', 'disable_consul', 'db']:
        if opt not in kw and hasattr(args, opt):
            config[opt] = getattr(args, opt)

    if ds_model is not None:
        config['ds_model_config']['model_class'] = ds_model

    for passphrases_file in args.passphrases:
        with open(passphrases_file) as fd:
            for line in fd:
                passphrase = line.strip().split()[0]
                if passphrase:
                    if 'server_info' not in config:
                        config['server_info'] = {}
                    if not config['server_info'].get('passphrase'):
                        config['server_info']['passphrase'] = []
                    if isinstance(
                            config['server_info'].get('passphrase'),
                            str
                    ):
                        config['server_info']['passphrase'] = [
                            config['server_info']['passphrase']
                        ]
                    config['server_info']['passphrase'].append(passphrase)

    App(**config).start()
