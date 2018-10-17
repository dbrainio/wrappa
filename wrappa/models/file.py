import tempfile

import requests


class WrappaFile:
    def __init__(self, data):
        self._payload = data.get('payload', None)
        self._ext = data.get('ext', None)
        self._url = data.get('url', None)

    @property
    def payload(self):
        if self._url is not None and not self._payload:
            self._payload = self._download_file()
        return self._payload

    @property
    def ext(self):
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
