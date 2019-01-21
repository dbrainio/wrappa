import numpy as np

from ..image import WrappaImage


def test_from_ndarray_to_ndarray():
    image = np.random.randint(0, 256, size=(10, 10, 3), dtype=np.uint8)

    wrappa_image = WrappaImage.init_from_ndarray(image, 'png')

    assert np.all(image == wrappa_image.as_ndarray)

def test_write_jpg():
    image = np.random.randint(0, 256, size=(10, 10, 3), dtype=np.uint8)

    wrappa_image = WrappaImage.init_from_ndarray(image, 'jpg')



    
    

