import io
import os
from collections import defaultdict

import requests
from requests_toolbelt import MultipartEncoder, MultipartDecoder

from ..models import WrappaObject, WrappaImage, WrappaFile, WrappaText


class Client:

    def __init__(self, address: str, passphrase: str=''):
        self._address: str = address
        self._passphrase: str = passphrase

    def predict(self, data: WrappaObject, as_json: bool=False):
        fields = {}

        if data.image is not None:
            fields['image'] = (
                data.image.name,
                io.BytesIO(data.image.payload),
                'image/{}'.format(data.image.ext),
            )
        if data.file is not None:
            fields['file'] = (
                data.file.name,
                io.BytesIO(data.file.payload),
                'applications/octet-stream',
            )
        if data.text is not None:
            fields['text'] = data.text.text

        me = MultipartEncoder(fields=fields)
        headers = {
            'Authorization': 'Token ' + self._passphrase,
            'Content-Type': me.content_type,
        }

        if as_json:
            headers['Accept'] = 'application/json'
        else:
            headers['Accept'] = 'multipart/form-data'

        response = requests.post(
            os.path.join(self._address, 'predict'),
            headers=headers,
            data=me,
        )

        response.raise_for_status()

        if as_json:
            return response.json()

        md = MultipartDecoder.from_response(response)

        parts = defaultdict(WrappaObject)
        for part in md.parts:
            cd: bytes = part.headers[b'content-disposition']
            tmp = cd.split(b';')
            field_name = tmp[1].split(b'=')[-1][1:-1]
            filename = None
            if len(tmp) >= 3:
                filename = tmp[2].split(b'=')[-1][1:-1]

            if b'-' in field_name:
                obj_type, ind = field_name.split(b'-')
            else:
                obj_type, ind = field_name, None

            if obj_type == b'image':
                parts[ind].set_value(WrappaImage(
                    name=str(filename), payload=part.content))
            if obj_type == b'file':
                parts[ind].set_value(WrappaFile(
                    name=str(filename), payload=part.content))
            if obj_type == b'text':
                parts[ind].set_value(WrappaText(str(part.text)))

        if parts.get(None, None):
            return parts[None]

        return [parts[i] for i in sorted(parts.keys())]

    def healthcheck(self):
        response = requests.get(
            os.path.join(self._address, 'healthcheck'),
            headers={
                'Authorization': 'Token ' + self._passphrase,
            },
        )

        response.raise_for_status()
        return None
