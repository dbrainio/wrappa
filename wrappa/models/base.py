from .image import WrappaImage
from .file import WrappaFile
from .text import WrappaText


class WrappaObject:

    def __init__(self, *args):
        self._file = None
        self._image = None
        self._text = None
        for arg in args:
            self.set_value(arg)

    def set_value(self, data):
        if isinstance(data, WrappaImage) and self._image is None:
            self._image = data
        elif isinstance(data, WrappaFile) and self._file is None:
            self._file = data
        elif isinstance(data, WrappaText) and self._text is None:
            self._text = data
        else:
            raise TypeError('Not supported type: {t}'.format(t=type(data)))
        return data

    @property
    def image(self):
        return self._image

    @property
    def file(self):
        return self._file

    @property
    def text(self):
        return self._text
