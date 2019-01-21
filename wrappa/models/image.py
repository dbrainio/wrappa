import io

import numpy as np
from PIL import Image

from .file import WrappaFile


class WrappaImage(WrappaFile):
    _EXT_TO_FORMAT = {
        'jpg': 'JPEG'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._img_as_ndarray = None

    @staticmethod
    def init_from_ndarray(payload, ext, name=None) -> 'WrappaImage':
        ext_to_store = ext
        if ext_to_store[0] == '.':
            ext_to_store = ext_to_store[1:]

        image = Image.fromarray(payload)
        # Use PIL format name instead of extension if applicable
        fmt = WrappaImage._EXT_TO_FORMAT.get(ext_to_store.lower(), ext_to_store)

        with io.BytesIO() as f:
            image.save(f, fmt)
            image_as_bytes = f.getvalue()

        return WrappaImage(
            ext=ext_to_store,
            payload=image_as_bytes,
            name=name
        )

    @property
    def as_ndarray(self) -> np.ndarray:
        if self._img_as_ndarray is None:
            with io.BytesIO(self.payload) as f:
                self._img_as_ndarray = np.asarray(Image.open(f))

        return self._img_as_ndarray
