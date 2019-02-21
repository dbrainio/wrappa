from wrappa import Client, WrappaObject, WrappaImage

cl = Client('http://localhost:8000', '123456')

wo = WrappaObject(WrappaImage(
    url='https://pbs.twimg.com/profile_images/54789364/JPG-logo-highres.jpg'))

cl.healthcheck()

resp = cl.predict([wo, wo])

resp.image.save_to_disk('./concat_images.jpg')
