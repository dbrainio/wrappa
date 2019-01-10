from wrappa import Client, WrappaObject, WrappaImage


cl = Client('http://localhost:8000', '123456')

wo = WrappaObject(WrappaImage(
    url='https://pbs.twimg.com/profile_images/54789364/JPG-logo-highres.jpg'))

resp = cl.healthcheck()
resp = cl.predict(wo)

print('Response:', resp)
