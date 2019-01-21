from wrappa import Client, WrappaObject, WrappaImage

cl = Client('http://localhost:8000', '123456')

wo = WrappaObject(WrappaImage(
    url='https://pbs.twimg.com/profile_images/54789364/JPG-logo-highres.jpg'))

_ = cl.healthcheck()

resp = cl.predict(wo)

for i, obj in enumerate(resp):
    obj.image.save_to_disk('./rotated_{i}.jpg'.format(i=i))
