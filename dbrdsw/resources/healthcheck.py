from flask_restful import Resource


class Healthcheck(Resource):

    @staticmethod
    def get():
        return None, 204
