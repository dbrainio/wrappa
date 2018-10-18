import os
import tempfile

import requests


class WrappaFile:
    def __init__(self, payload=None, ext=None, url=None):
        self._payload = payload
        self._ext = ext
        self._url = url

    @property
    def payload(self):
        if not self._payload and self._url is not None:
            self._payload = self._download_file()
        return self._payload

    @property
    def ext(self):
        if not self._ext and self._url is not None:
            tmp = os.path.splitext(self._url)
            if len(tmp) > 1:
                self._ext = tmp[-1][1:]
        return self._ext

    def url(self):
        return self._url

    @property
    def as_dict(self):
        return {
            'payload': self.payload,
            'ext': self.ext
        }

    def _download_file(self):
        data = None
        if self.url is not None:
            r = requests.get(self.url, stream=True)
            if r.status_code == 200:
                with tempfile.TemporaryFile(mode='wb') as f:
                    for chunk in r:
                        f.write(chunk)
                    f.seek(0)
                    data = f.read()

        return data
