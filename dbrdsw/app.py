from flask import Flask
from flask_restful import Api

from .resources import Healthcheck, Info, Predict


class App:
    def __init__(self, **kwargs):

        # Parse kwargs
        server_info = kwargs['server_info']
        self._port = kwargs['port']

        app = Flask(__name__)
        api = Api(app)

        api.add_resource(Healthcheck, '/healthcheck')
        api.add_resource(Info.setup(**server_info), '/info')
        api.add_resource(Predict.setup(**kwargs), '/predict')

        self._api = api
        self._app = app

    def start(self, debug=False):
        self._app.run(host='0.0.0.0', port=self._port, debug=debug)
