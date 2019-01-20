import io

from PIL import Image

from .file import WrappaFile


class WrappaImage(WrappaFile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._img_as_ndarray = None

    @classmethod
    def init_from_ndarray(cls, payload, ext, name=None):
        ext_to_store = ext
        if ext_to_store[0] == '.':
            ext_to_store = ext_to_store[1:]

        image = Image.fromarray(payload)
        image_as_bytes = image.tobytes()
        return WrappaImage(
            ext=ext_to_store,
            payload=image_as_bytes,
            name=name
        )

    @property
    def as_ndarray(self):
        if self._img_as_ndarray is None:
            self._img_as_ndarray = Image.open(io.BytesIO(self.payload))

        return self._img_as_ndarray
