import os
import tempfile
from uuid import uuid4

import requests


class WrappaFile:
    def __init__(self, payload=None, ext=None, name=None, url=None):
        self._payload = payload
        self._ext = ext
        self._url = url
        self._name = name

    @property
    def payload(self):
        if not self._payload and self._url is not None:
            self._payload = self._download_file()
        return self._payload

    @property
    def ext(self):
        if not self._ext:
            to_ext = self._url or self._name
            if to_ext is not None:
                _, ext = os.path.splitext(to_ext)
                if ext:
                    self._ext = ext[1:]
        return self._ext

    @property
    def name(self):
        if self._name is None:
            self._name = str(uuid4()) + '.' + self.ext
        return self._name

    @property
    def url(self):
        return self._url

    @property
    def as_dict(self):
        return {
            'payload': self.payload,
            'ext': self.ext,
            'name': self.name
        }

    def save_to_disk(self, fpath):
        _, ext = os.path.splitext(fpath)
        if ext:
            _fpath = fpath
        else:
            _fpath = fpath + '.' + self.ext
        with open(_fpath, 'wb') as f:
            f.write(self.payload)
        return _fpath

    def _download_file(self):
        data = None
        if self.url is not None:
            r = requests.get(self.url, stream=True)
            if r.status_code == 200:
                with tempfile.TemporaryFile(mode='r+b') as f:
                    for chunk in r:
                        f.write(chunk)
                    f.seek(0)
                    data = f.read()

        return data
