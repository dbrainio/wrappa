import numpy as np
import cv2

from .file import WrappaFile


class WrappaImage(WrappaFile):
    @classmethod
    def init_from_ndarray(cls, payload, ext):
        ext_to_store = ext
        ext_to_use = ext_to_store
        if ext_to_use[0] != '.':
            ext_to_use = '.' + ext_to_use
        if ext_to_store[0] == '.':
            ext_to_store = ext_to_store[1:]
        _, image = cv2.imencode(ext_to_use, payload)
        image_as_bytes = image.astype(np.uint8).tobytes()
        return WrappaImage(
            ext=ext_to_store,
            payload=image_as_bytes
        )

    @property
    def as_ndarray(self):
        image = np.fromstring(self.payload, dtype=np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        return image
