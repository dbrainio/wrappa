import asyncio
import datetime
import io
import json
import uuid

from PIL import Image
from aiohttp import web, MultipartWriter, ClientSession
from aiohttp.web_exceptions import HTTPRequestEntityTooLarge
from pdf2image import convert_from_bytes

from .predictor import Predictor
from ..common import *
from ..models import WrappaFile, WrappaText, WrappaImage, WrappaObject


class Predict:
    def __init__(self, db=None, **kwargs):
        self._db = db
        self._server_info = kwargs['server_info']
        self._predictor = Predictor.create(kwargs['ds_model_config'])
        self._storage = kwargs.get('storage')
        self._is_inited = False
        self._tasks = dict()

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
        content_type = key.split('-')[0]
        ext = filename.split('.')[-1]
        if filename is not None and buf is not None:
            if content_type == 'image':
                try:
                    buf.seek(0)
                    _ = Image.open(buf)
                    return [WrappaImage(
                        payload=buf.getvalue(), ext=ext, name=filename)]
                except:
                    imgs = convert_from_bytes(buf.getvalue())
                    for i, img in enumerate(imgs):
                        buf = io.BytesIO()
                        img.save(buf, format='JPEG')
                        buf.flush()
                        imgs[i] = WrappaImage(
                            payload=buf.getvalue(),
                            ext='jpeg',
                            name='{}-{}.jpeg'.format(
                                filename.split('.')[0], str(i)
                            )
                        )
                    return imgs
            data = {
                'payload': buf.getvalue(),
                'ext': ext,
                'name': filename
            }

        return [WrappaFile(**data)]

    @staticmethod
    def _parse_text(args, key):
        data = None
        if args.get(key) is not None:
            data = args[key]
        return [WrappaText(data)]

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
        imgs, files, texts = [None], [None], [None]
        if 'image' in input_spec:
            k = 'image' if key is None else 'image-{}'.format(key)
            imgs = await self._parse_file_object(data, k)
        if 'file' in input_spec:
            k = 'file' if key is None else 'file-{}'.format(key)
            files = await self._parse_file_object(data, k)
        if 'text' in input_spec:
            k = 'text' if key is None else 'text-{}'.format(key)
            texts = self._parse_text(data, k)

        resp = []
        for i in imgs:
            for f in files:
                for t in texts:
                    r = WrappaObject()
                    if i:
                        r.set_value(i)
                    if f:
                        r.set_value(f)
                    if t:
                        r.set_value(t)
                    resp.append(r)
        if 'list' not in input_spec and len(resp) == 1:
            return resp[0]
        return resp

    async def _parse_request(self, request):
        data = await request.post()

        input_spec = self._server_info['specification']['input']
        if 'list' in input_spec:
            if not data:
                return []
            resp = []
            max_ind = max(map(lambda x: int(x.split('-')[-1]), data.keys()))
            for i in range(max_ind + 1):
                resp.extend(await self._parse_one_request(data, i))
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

        return web.json_response(
            data=data,
            status=200,
            dumps=functools.partial(json.dumps, indent=4)
        )

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
                    'Content-Type': 'multipart/form-data;boundary={}'.format(
                        mpwriter.boundary),
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

    async def _post_end(self, request, res, response_type, token, data):
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
            try:
                raise exception
            except:
                return DSModelError.json_response()

        # Prepare and send response
        response = None
        if response_type == 'multipart/form-data':
            response = await self._prepare_form_data_response(request, res)
        elif response_type == 'application/json':
            response = self._prepare_json_response(res)

        if response is None:
            return UnableToPrepareResponseError.json_response()
        return response

    async def _inc_usage(self, token, label):
        if not self._db:
            return
        now = datetime.datetime.utcnow()
        ymd = int(now.strftime('%Y%m%d'))
        ym = int(now.strftime('%Y%m'))
        daily = self._db.usage_stats.daily
        monthly = self._db.usage_stats.monthly
        inc = {'$inc': {label: 1}}
        await daily.update_one(
            {'token': token, 'date': ymd}, inc, upsert=True)
        await monthly.update_one(
            {'token': token, 'date': ym}, inc, upsert=True)

    @UnknownError.if_failed
    async def post(self, request):
        await self._init()
        # Check authorization
        authorized, token = self._check_auth(request)
        if not authorized:
            return UnauthorizedError.json_response()

        await self._inc_usage(token, 'total')

        # Parse request
        response_type = self._get_response_type(request)
        if response_type is None:
            return InvalidAcceptHeaderValueError.json_response()
        try:
            data = await self._parse_request(request)
        except HTTPRequestEntityTooLarge:
            return HTTPRequestEntityTooLargeError.json_response()
        except Exception as e:
            print(
                'Failed to parse request with exception\n{exception}'.format(
                    exception=traceback.format_exc()
                ),
                file=sys.stderr)
            return UnbaleToParseRequestError.json_response()
        if data is None:
            return ForbiddenError.json_response()
        if data == WrappaObject() or (
                    isinstance(data, list) and (
                            not data or WrappaObject() in data)):
            return InvalidDataError.json_response()
        # Send data to request
        is_json = False
        if 'json' in self._server_info['specification']['output']:
            is_json = response_type == 'application/json'

        is_async = request.query.get('async', 'false') == 'true'
        task = self._predictor.predict(data, is_json, request.path)

        if not is_async:
            res = await task
            result = await self._post_end(
                request, res, response_type, token, data)
            await self._inc_usage(token, 'success')
            return result

        task_id = str(uuid.uuid4())
        self._tasks[task_id] = (
            asyncio.ensure_future(task), response_type, token, data
        )
        return web.json_response(
            data={'task_id': task_id},
            dumps=functools.partial(json.dumps, indent=4),
        )

    @UnknownError.if_failed
    async def result(self, request):
        task_id = request.match_info['task_id']
        if task_id not in self._tasks:
            return AsyncTaskNotFoundError.json_response()
        task, response_type, token, data = self._tasks[task_id]
        if not task.done():
            return AsyncTaskNotDoneError.json_response()
        try:
            res = await task
            result = await self._post_end(
                request, res, response_type, token, data)
            await self._inc_usage(token, 'success')
            return result
        except Exception as e:
            return AsyncTaskFailedError.json_response()
        finally:
            del self._tasks[task_id]
