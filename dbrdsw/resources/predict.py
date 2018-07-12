import importlib.util
import io

from flask_restful import abort, reqparse, Resource
from flask import make_response
from requests_toolbelt import MultipartEncoder
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
        parser = reqparse.RequestParser()
        parser.add_argument(
            'file', type=werkzeug.datastructures.FileStorage, location='files')
        parser.add_argument(
            'image_url', type=str)
        parser.add_argument(
            'text', type=str
        )
        parser.add_argument('Authorization', type=str, location='headers')
        args = parser.parse_args()

        if self._server_info['passphrase']:
            if args['Authorization'] is None:
                return None
            if 'Token' in args['Authorization']:
                token = args['Authorization'][6:]
            else:
                token = args['Authorization']
            if token != self._server_info['passphrase']:
                return None

        input_spec = self._server_info['specification']['input']
        resp = {}
        if 'image' in input_spec:
            f = args['file']
            filename = None
            buf = io.BytesIO()
            if f is None:
                # Download file
                r = requests.get(args['image_url'])
                buf.write(r.content)
                buf.flush()

                tmp = args['image_url'].split('/')[-1].split('?')
                if len(tmp) <= 1:
                    filename = ''.join(tmp)
                else:
                    filename = ''.join(tmp[:-1])
            else:
                f.save(buf)
                f.close()
                filename = f.filename
            resp['image'] = {
                'payload': buf.getvalue(),
                'ext': filename.split('.')[-1]
            }
        if 'text' in input_spec:
            resp['text'] = args['text']

        return resp

    @staticmethod
    def _response_type():
        parser = reqparse.RequestParser()
        parser.add_argument('Access', type=str, location='headers')
        args = parser.parse_args()
        access_type = args['Access']

        if access_type in [None, 'multipart/form-data']:
            return 'multipart/form-data'
        elif access_type == 'application/json':
            return 'application/json'

        return None

    def _prepare_json_response(self, response):
        output_spec = self._server_info['specification']['output']
        if not isinstance(response, (dict, list,)) or 'json' not in output_spec:
            return None

        return response

    def _prepare_form_data_response(self, response):
        output_spec = self._server_info['specification']['output']
        resp = make_response()
        fields = {}

        if 'image' in output_spec:
            if 'list' in output_spec:
                for i, v in enumerate(response):
                    if not isinstance(v['image']['payload'], bytes):
                        raise TypeError('Expecting type bytes for image.payload, got {}'.format(
                            type(v['image']['payload'])))
                    if not v['image']['ext'] or not isinstance(v['image']['ext'], str):
                        raise TypeError('Wrong extension, expecting jpg or png, got {}'.format(
                            v['image']['ext']))
                    buf = io.BytesIO(v['image']['payload'])
                    ext = v['image']['ext']
                    fields['image-{}'.format(i)] = (
                        'filename.{}'.format(ext), buf, 'image/{}'.format(ext))
            else:
                if not isinstance(response['image']['payload'], bytes):
                    raise TypeError('Expecting type bytes for image.payload, got {}'.format(
                        type(response['image']['payload'])))
                if not response['image']['ext'] or not isinstance(response['image']['ext'], str):
                    raise TypeError('Wrong extension, expecting jpg or png, got {}'.format(
                        response['image']['ext']))
                buf = io.BytesIO(response['image']['payload'])
                ext = response['image']['ext']
                fields['image'] = (
                    'filename.{}'.format(ext), buf, 'image/{}'.format(ext))

        def _add_fields_text_value(value):
            if 'list' in output_spec:
                for i, v in enumerate(response):
                    if not isinstance(v[value], str):
                        raise TypeError('Expecting type str for {}, got {}'.format(
                            value, type(v[value])))
                    fields['{}-{}'.format(value, i)] = v[value]
            else:
                if not isinstance(response[value], str):
                    raise TypeError('Expecting type str for {}, got {}'.format(
                        value, type(response[value])))
                fields[value] = response[value]
            return fields

        if 'image_url' in output_spec:
            fields = _add_fields_text_value('image_url')
        if 'text' in output_spec:
            fields = _add_fields_text_value('text')

        me = MultipartEncoder(fields=fields)
        resp = make_response(me.to_string())
        resp.mimetype = me.content_type
        return resp

    def post(self):
        # Parse request
        response_type = self._response_type()
        if response_type is None:
            abort(400, message='Invalid Access header value')

        try:
            data = self._parse_request()
        except Exception as e:
            abort(400, message='Unbale to parse request: ' + str(e))
        if data is None:
            abort(403, message='Forbidden')
        if data == {}:
            abort(400, message='Invalid data')

        # Send data to request
        try:
            # Predict should accept array of objects
            # For now just create array of a single object
            if 'json' in self._server_info['specification']['output']:
                [res, *_] = self._ds_model.predict([data],
                                                   json=response_type == 'application/json')
            else:
                f_kwargs = {}
                if 'json' in self._ds_model.predict.__code__.co_varnames:
                    f_kwargs['json'] = False

                [res, *_] = self._ds_model.predict([data], **f_kwargs)
        except Exception as e:
            abort(400, message='DS model failed to process data: ' + str(e))
        # Prepare and send response
        response = {
            'multipart/form-data': self._prepare_form_data_response,
            'application/json': self._prepare_json_response
        }[response_type](res)
        if response is None:
            abort(400, message='Unable to prepare response')
        return response
