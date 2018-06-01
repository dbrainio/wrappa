import importlib.util
import io
import json

from flask_restful import abort, reqparse, Resource
from flask import send_file, make_response
import werkzeug
import requests


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
        parse.add_argument(
            'file', type=werkzeug.datastructures.FileStorage, location='files')
        parse.add_argument(
            'image_url', type=str)
        parse.add_argument(
            'text', type=str
        )
        args = parse.parse_args()

        input_spec = self._server_info['specification']['input']
        resp = {'data': {}, 'metadata': {}}
        if 'image' in input_spec:
            f = args['file']
            filename = None
            buf = io.BytesIO()
            if f is None:
                # Download file
                r = requests.get(args['image_url'])
                buf.write(r.content)
                buf.flush()
                filename = ''.join(args['image_url'].split(
                    '/')[-1].split('?')[:-1])
            else:
                f.save(buf)
                f.close()
                filename = f.filename
            resp['data']['image'] = buf.getvalue()
            resp['metadata']['image'] = {
                'filename': filename,
                'ext': filename.split('.')[-1]
            }
            # return buf.getvalue(), {
            #     'filename': f.filename,
            #     'ext': f.filename.split('.')[-1]
            # }
        if 'text' in input_spec:
            resp['text'] = args['text']
            resp['metadata']['text'] = {}

        if len(resp['data']) == 1:
            for k in resp['data']:
                return resp['data'][k], resp['metadata'][k]

        return resp['data'], resp['metadata']

    def _prepare_response(self, response, meta):
        output_spec = self._server_info['specification']['output']
        resp = None
        if 'image' in output_spec:
            buf = io.BytesIO(response['image'])
            resp = send_file(buf, mimetype='image/' + meta['ext'])
        else:
            resp = make_response()

        def _form_header(value):
            if 'list' in output_spec:
                l = []
                for v in response:
                    l.append(v[value])
                resp.headers['dbr-' + value] = json.dumps(l)
            else:
                resp.headers['dbr-' + value] = response[value]
            return resp

        if 'image_url' in output_spec:
            resp = _form_header('image_url')
        if 'text' in output_spec:
            resp = _form_header('text')
        return resp

    def post(self):
        # Parse request
        try:
            data, meta = self._parse_request()
        except Exception as e:
            abort(400, message='Unbale to parse request: ' + str(e))
        if data == {}:
            abort(400, message='Invalid data')
        # Send data to request
        try:
            # Predict should accept array of objects
            # For now just create array of a single object
            [res, *_] = self._ds_model.predict([data])
        except Exception as e:
            abort(400, message='DS model failed to process data: ' + str(e))
        # Prepare and send response
        response = self._prepare_response(res, meta)
        if response is None:
            abort(400, message='Unable to prepare response')
        return response
