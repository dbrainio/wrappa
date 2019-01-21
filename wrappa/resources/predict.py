import importlib.util
import io
import sys
import traceback

from flask_restful import abort, reqparse, Resource
from flask import make_response
from requests_toolbelt import MultipartEncoder
import werkzeug
import requests

from ..models import WrappaFile, WrappaText, WrappaImage, WrappaObject


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
        cls._storage = kwargs.get('storage')
        return cls

    @staticmethod
    def _parse_file_object(args, key):
        filename, buf = None, None
        data = None
        if args.get(key) is not None:
            f = args[key]
            buf = io.BytesIO()
            f.save(buf)
            f.close()
            filename = f.filename
        if args.get('{}_url'.format(key)) is not None:
            obj_url = args['{key}_url'.format(key)]
            # Download file
            r = requests.get(obj_url)
            buf = io.BytesIO()
            buf.write(r.content)
            buf.flush()

            tmp = obj_url.split('/')[-1].split('?')
            if len(tmp) <= 1:
                filename = ''.join(tmp)
            else:
                filename = ''.join(tmp[:-1])
        if filename is not None and buf is not None:
            data = {
                'payload': buf.getvalue(),
                'ext': filename.split('.')[-1],
                'name': filename
            }

        to_wrappa_type = {
            'image': WrappaImage,
            'file': WrappaFile
        }
        return to_wrappa_type[key](**data)

    @staticmethod
    def _parse_text(args):
        data = None
        if args.get('text') is not None:
            data = args['text']
        return WrappaText(data)

    def _parse_request(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            'file', type=werkzeug.datastructures.FileStorage, location='files')
        parser.add_argument(
            'image', type=werkzeug.datastructures.FileStorage, location='files')
        parser.add_argument(
            'file_url', type=str)
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
            if token not in self._server_info['passphrase']:
                return None

        input_spec = self._server_info['specification']['input']
        resp = WrappaObject()
        if 'image' in input_spec:
            resp.set_value(self._parse_file_object(args, 'image'))
        if 'file' in input_spec:
            resp.set_value(self._parse_file_object(args, 'file'))
        if 'text' in input_spec:
            resp.set_value(self._parse_text(args))
        return resp

    @staticmethod
    def _response_type():
        parser = reqparse.RequestParser()
        parser.add_argument('Accept', type=str, location='headers')
        args = parser.parse_args()
        accept_type = args['Accept']

        if accept_type in [None, 'multipart/form-data']:
            return 'multipart/form-data'
        elif accept_type == 'application/json':
            return 'application/json'

        return None

    def _prepare_json_response(self, response):
        output_spec = self._server_info['specification']['output']
        if not isinstance(response, (dict, list,)) or 'json' not in output_spec:
            return None

        return response

    @staticmethod
    def _add_fields_file_object_value(fields, value, key, index=None):
        # v = value.get(key)
        if value is None:
            return fields
        ext = value['ext']
        payload = value['payload']
        filename = value['name']
        payload_type = type(payload)
        if not isinstance(payload, bytes):
            raise TypeError(
                'Expecting type bytes for image.payload, got {payload_type}'.format(
                    payload_type=payload_type))
        if not ext or not isinstance(ext, str):
            raise TypeError(
                'Wrong extension, expecting jpg, png or gif, got {ext}'.format(
                    ext=ext))
        buf = io.BytesIO(payload)
        if index is not None:
            if key == 'image':
                fields['{key}-{index}'.format(key=key, index=index)] = (
                    filename, buf, 'image/{ext}'.format(ext=ext))
            else:
                fields['{key}-{index}'.format(key=key, index=index)] = (
                    filename, buf, 'applications/octet-stream')
        else:
            if key == 'image':
                fields[key] = (
                    filename, buf, 'image/{ext}'.format(ext=ext))
            else:
                fields[key] = (
                    filename, buf, 'applications/octet-stream')
        return fields

    @staticmethod
    def _add_fields_text_value(fields, value, key, index=None):
        if value is None:
            return fields
        value_type = type(value)
        if not isinstance(value, str):
            raise TypeError(
                'Expecting type str for {value}, got {value_type}'.format(
                    value=value, value_type=value_type
                ))
        if index is not None:
            fields['{key}-{index}'.format(key=key, index=index)] = value
        else:
            fields[key] = value
        return fields

    def _prepare_form_data_response(self, response):
        output_spec = self._server_info['specification']['output']
        resp = make_response()
        fields = {}

        for spec in ['image', 'file']:
            if spec in output_spec:
                if 'list' in output_spec:
                    for i, v in enumerate(response):
                        fields = self._add_fields_file_object_value(
                            fields, getattr(v, spec).as_dict, spec, index=i)
                else:
                    fields = self._add_fields_file_object_value(
                        fields, getattr(response, spec).as_dict, spec)

        for spec in ['image_url', 'file_url']:
            if spec in output_spec:
                obj_type = {
                    'file_url': 'file',
                    'image_url': 'image'
                }[spec]
                if 'list' in output_spec:
                    for i, v in enumerate(response):
                        fields = self._add_fields_text_value(
                            fields, getattr(v, obj_type).url, spec, index=i)
                else:
                    fields = self._add_fields_text_value(
                        fields, getattr(response, obj_type).url, spec)

        if 'text' in output_spec:
            if 'list' in output_spec:
                for i, v in enumerate(response):
                    fields = self._add_fields_text_value(
                        fields, getattr(v, 'text').text, 'text', index=i)
            else:
                fields = self._add_fields_text_value(
                    fields, getattr(response, 'text').text, 'text')

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
            print(
                'Failed to parse request with exception\n{exception}'.format(
                    exception=traceback.format_exc()
                ),
                file=sys.stderr)
            abort(400, message='Unbale to parse request: ' + str(e))
        if data is None:
            abort(403, message='Forbidden')
        if data == WrappaObject():
            abort(400, message='Invalid data')

        # Send data to request
        try:
            # Predict should accept array of objects
            # For now just create array of a single object
            if 'json' in self._server_info['specification']['output']:
                is_json = response_type == 'application/json'
                [res, *_] = self._ds_model.predict([data],
                                                   as_json=is_json)
            else:
                f_kwargs = {}
                if 'as_json' in self._ds_model.predict.__code__.co_varnames:
                    f_kwargs['as_json'] = False

                [res, *_] = self._ds_model.predict([data], **f_kwargs)
            if self._storage is not None:
                self._storage.add(data, res)
        except Exception as e:
            print(
                'Failed to parse request with exception\n{exception}'.format(
                    exception=traceback.format_exc()
                ),
                file=sys.stderr)
            if self._storage is not None:
                self._storage.add(data, str(e))
            abort(400, message='DS model failed to process data: ' + str(e))

        # Prepare and send response
        response = {
            'multipart/form-data': self._prepare_form_data_response,
            'application/json': self._prepare_json_response
        }[response_type](res)
        if response is None:
            abort(400, message='Unable to prepare response')
        return response
