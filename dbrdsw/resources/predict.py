import importlib.util
import io

from flask_restful import abort, reqparse, Resource
from flask import send_file
import werkzeug


class Predict(Resource):

    @classmethod
    def setup(cls, **kwargs):
        cls._ds_model_config = kwargs['ds_model_config']
        cls._server_info = kwargs['server_info']
        # Dynamically import package
        spec = importlib.util.spec_from_file_location(
            'DSModel', cls._ds_model_config['model_path'])
        ds_lib = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ds_lib)
        # Init ds model
        cls._ds_model = ds_lib.DSModel(**cls._ds_model_config['config'])
        return cls

    def _parse_request(self):
        parse = reqparse.RequestParser()
        input_spec = self._server_info['specification']['input']
        if input_spec == 'image':
            parse.add_argument(
                'file', type=werkzeug.datastructures.FileStorage, location='files')
            args = parse.parse_args()
            f = args['file']
            buf = io.BytesIO()
            f.save(buf)
            f.close()
            return buf.getvalue(), {
                'filename': f.filename,
                'ext': f.filename.split('.')[-1]
            }

        return None, None

    def _prepare_response(self, response, meta):
        output_spec = self._server_info['specification']['output']
        if output_spec == 'image':
            buf = io.BytesIO(response)
            return send_file(buf, mimetype='image/' + meta['ext'])
        elif output_spec == 'image_url+text':
            return {
                'text': response['text'],
                'url': response['url']
            }

    def post(self):
        # Parse request
        try:
            data, meta = self._parse_request()
        except Exception:
            abort(400, message='Unbale to parse request')
        if data is None:
            abort(400, message='Invalid data')
        # Send data to request
        try:
            # Predict should accept array of objects
            # For now just create array of a single object
            [res, *_] = self._ds_model.predict([data])
        except Exception:
            abort(400, message='DS model failed to process data')
        # Prepare and send response
        return self._prepare_response(res, meta)
