from flask_restful import Resource


class Info(Resource):

    @classmethod
    def setup(cls, **kwargs):
        cls._spec = kwargs
        return cls

    def get(self):
        return self._spec
