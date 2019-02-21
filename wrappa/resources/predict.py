import io
import sys
import traceback
import asyncio

from aiohttp import web, MultipartWriter, ClientSession

from ..models import WrappaFile, WrappaText, WrappaImage, WrappaObject
from ..common import abort
from .predictor import Predictor

class Predict:

    def __init__(self, **kwargs):
        self._server_info = kwargs['server_info']
        self._predictor = Predictor.create(kwargs['ds_model_config'])
        self._storage = kwargs.get('storage')
        self._is_inited = False

    async def _init(self):
        if not self._is_inited:
            self._predictor = await self._predictor
            self._is_inited = True

    @staticmethod
    async def _parse_file_object(args, key):
        filename, buf = None, None
        data = None
        if args.get(key) is not None:
            f = args[key].file
            buf = io.BytesIO()
            buf.write(f.read())
            buf.flush()
            f.close()
            filename = args[key].filename
        if args.get('{}_url'.format(key)) is not None:
            obj_url = args['{key}_url'.format(key=key)]
            # Download file
            with ClientSession() as session:
                async with session.get(obj_url) as resp:
                    data = await resp.content()
                    buf = io.BytesIO()
                    buf.write(data)
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
        return to_wrappa_type[key.split('-')[0]](**data)

    @staticmethod
    def _parse_text(args, key):
        data = None
        if args.get(key) is not None:
            data = args[key]
        return WrappaText(data)

    def _check_auth(self, request):
        if not self._server_info['passphrase']:
            return True, None

        token = request.headers.get('Authorization')
        
        if token is None:
            return False, None
        if 'Token' in token:
            token = token[6:]

        return token in self._server_info['passphrase'], token

    async def _parse_one_request(self, data, key=None):
        input_spec = self._server_info['specification']['input']
        resp = WrappaObject()
        if 'image' in input_spec:
            k = 'image' if key is None else 'image-{}'.format(key)
            resp.set_value(await self._parse_file_object(data, k))
        if 'file' in input_spec:
            k = 'file' if key is None else 'file-{}'.format(key)
            resp.set_value(await self._parse_file_object(data, k))
        if 'text' in input_spec:
            k = 'text' if key is None else 'text-{}'.format(key)
            resp.set_value(self._parse_text(data, k))
        return resp

    async def _parse_request(self, request):
        data = await request.post()
  
        input_spec = self._server_info['specification']['input']
        if 'list' in input_spec:
            resp = []
            max_ind = max(map(lambda x: int(x.split('-')[-1]), data.keys()))
            for i in range(max_ind+1):
                resp.append(await self._parse_one_request(data, i))
        else:
            resp = await self._parse_one_request(data)
       
        return resp

    @staticmethod
    def _get_response_type(request):
        accept_type = request.headers.get('Accept')

        if accept_type in [None, 'multipart/form-data']:
            return 'multipart/form-data'
        elif accept_type == 'application/json':
            return 'application/json'

        return None

    def _prepare_json_response(self, data):
        output_spec = self._server_info['specification']['output']
        if not isinstance(data, (dict, list,)) or 'json' not in output_spec:
            return None

        return web.json_response(data=data, status=200)

    @staticmethod
    def _add_fields_file_object_value(fields, value, key, index=None):
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

    async def _prepare_form_data_response(self, request, data):
        output_spec = self._server_info['specification']['output']
        fields = {}

        for spec in ['image', 'file']:
            if spec in output_spec:
                if 'list' in output_spec:
                    for i, v in enumerate(data):
                        fields = self._add_fields_file_object_value(
                            fields, getattr(v, spec).as_dict, spec, index=i)
                else:
                    fields = self._add_fields_file_object_value(
                        fields, getattr(data, spec).as_dict, spec)

        for spec in ['image_url', 'file_url']:
            if spec in output_spec:
                obj_type = {
                    'file_url': 'file',
                    'image_url': 'image'
                }[spec]
                if 'list' in output_spec:
                    for i, v in enumerate(data):
                        fields = self._add_fields_text_value(
                            fields, getattr(v, obj_type).url, spec, index=i)
                else:
                    fields = self._add_fields_text_value(
                        fields, getattr(data, obj_type).url, spec)

        if 'text' in output_spec:
            if 'list' in output_spec:
                for i, v in enumerate(data):
                    fields = self._add_fields_text_value(
                        fields, getattr(v, 'text').text, 'text', index=i)
            else:
                fields = self._add_fields_text_value(
                    fields, getattr(data, 'text').text, 'text')

        with MultipartWriter('form-data') as mpwriter:
            response = web.StreamResponse(
                status=200,
                headers={
                    'Content-Type': 'multipart/form-data;boundary={}'.format(mpwriter.boundary),
                }
            )
            await response.prepare(request)
            for k, value in fields.items():
                if isinstance(value, tuple):
                    mpwriter.append(value[1], {
                        'Content-Disposition': 'form-data; name="{name}"; filename="{filename}"'.format(
                            name=k, filename=value[0]
                        ),
                        'Content-Type': value[2],
                    })
                else:
                    mpwriter.append(value, {
                        'Content-Disposition': 'form-data; name="{name}"'.format(
                            name=k
                        ),
                    })
            await mpwriter.write(response)
        return response

    async def post(self, request):
        await self._init()
        # Check authorization
        authorized, token = self._check_auth(request)
        if not authorized:
            return abort(401, message='Unauthorized')
     
        # Parse request
        response_type = self._get_response_type(request)
        if response_type is None:
            return abort(400, message='Invalid Accept header value')
        try:
            data = await self._parse_request(request)
        except Exception as e:
            print(
                'Failed to parse request with exception\n{exception}'.format(
                    exception=traceback.format_exc()
                ),
                file=sys.stderr)
            return abort(400, message='Unbale to parse request: ' + str(e))
        if data is None:
            return abort(403, message='Forbidden')
        if data == WrappaObject() or (isinstance(data, list) and (not data or WrappaObject() in data)):
            return abort(400, message='Invalid data')
        # Send data to request
        is_json = False
        if 'json' in self._server_info['specification']['output']:
            is_json = response_type == 'application/json'

        res = await self._predictor.predict(data, is_json)

        exception = None
        if isinstance(res, tuple):
            exception, trace = res
            print(
                'Failed to parse request with exception\n{exception}'.format(
                    exception=trace
                ),
                file=sys.stderr)
            res = str(exception)
        
        if self._storage is not None:
            self._storage.add(token, data, res)
            
        if exception is not None:
            return abort(400, message='DS model failed to process data: ' + res)

        # Prepare and send response
        response = None
        if response_type == 'multipart/form-data':
            response = await self._prepare_form_data_response(request, res)
        elif response_type == 'application/json':
            response = self._prepare_json_response(res)

        if response is None:
            return abort(400, message='Unable to prepare response')
        return response
