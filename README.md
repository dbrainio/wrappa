## Description
**wrappa** is a util to wrap any interface implementing DSModel in a http server. Python3.5+

## Example
Simple service which rotates provided image.
```python
import numpy as np

from wrappa import WrappaObject, WrappaImage

class DSModel:

    def __init__(self, **kwargs):
        pass

    def predict(self, data, **kwargs):
        _ = kwargs
        # Data is always an array of WrappaObject
        responses = []
        for obj in data:
            img = obj.image.as_ndarray
            rotated_img = np.rot90(img)
            resp = WrappaObject(WrappaImage.init_from_ndarray(
                payload=rotated_img,
                ext=obj.image.ext,
            ))
            responses.append(resp)
        return responses
```

To launch server simply run `wrappa --config examples/rotate/config.yml --disable-consul`.
In order to send request to created server use curl
```
curl -X "POST" "http://localhost:8000/predict" \
     -H 'Authorization: Token 123456' \
     -H 'Content-Type: multipart/form-data; charset=utf-8; boundary=__smth__' \
     -H 'Accept: multipart/form-data' \
     -F "image=@path_to_img.jpg"
```
or run client example `python examples/rotate/rotate_client.py`.

## How to use
It's simple.

Installation: `pip install wrappa`.

Or clone repo and execute `python3 setup.py install`.

Or you can build distribution wheel by running `make` in repository root.
Your wheel will be stored in `dist` directory. You can install it by running `pip install wrappa-<version>-py3-none-any.whl`.

If everything is fine, you'll be able to execute following command in your terminal:
`wrappa --help`

To run server:
`wrappa --config './config.yml'`

To run server in dev mode:
`wrappa --config './config.yml' --debug`

To run server without consul support:
`wrappa --config './config.yml' --disable-consul`

To validate your model against provided specs:
`wrappa-validate --config './config_validate.yml'`

Example of validation config:
```yaml
specification:
  input:
    - image
  output:
    - image
ds_model_config:
  model_path: 'examples/rotate/rotate.py'
  config: {}
```

## Config
```yaml
server_info:
  # address where this service will be available
  address: "http://localhost:8000"
  passphrase:
    - "1234"
    - "1235"
  # what DSModel expects as an input and what it produce
  specification:
    input:
      - image
    output:
      - image
      - text
  # display name in interface
  name: "test app"
  # message to be shown before accepting input in interface
  invitation_message: "send image"
# port where service will run
port: 8000
# connect to consul node
# for debug it is optional
consul:
  host: 127.0.0.1
  port: 8500
# storage to save all inputs and outputs
# can be ommited
# for now only supports file storage
storage:
  files:
    path: 'path/to/store'
# section describing DSModel
ds_model_config:
  # absolute (!) path to importable (!!!) package
  model_path: 'path/to/DSModel'
  # config which will be passed to DSModel constructor
  config: {}
```

## Supported specification
All specification can be passed as mixins.

### Input
All inputs wrapped in **WrappaObject**, it has `image`, `file` and `text` properties, which returns corresponding wrappa objects to work with.

**image**

Array of **WrappaImage** will be passed to DSModel.predict.
**WrappaImage** class has `payload`, `name` and `ext` properties.
If you need payload as ndarray call `as_ndarray` property.

**file**

Array of **WrappaFile** will be passed to DSModel.predict.
**WrappaFile** class has `payload`, `name` and `ext` properties.

**text**
Array of **WrappaText** will be passed to DSModel.predict.
**WrappaText** class has `text` property.


**list**
Array of **WrappaObject** will be passed to DSModel.predict.

### Output
All outputs must be wrapped in **WrappaObject**.

You can add objects as follows:
```python
wo = WrappaObject(
  WrappaImage(payload= 'bytes_repr_of_an_image', ext='jpg', name='tmp'}),
  WrappaText('some text'))
# you can pass objects not only in init call
wo.set_value(WrappaFile({payload='bytes_repr_of_a_file', ext='zip'}))
```

**image**

DSModel.predict expected to produce **WrappaObject** with **WrappaImage** set.
You can init **WrappaImage** with ndarray by using this snippet:
```python
img = np.array([[0]*300]*300, dtype=np.uint8)

wi = WrappaImage.init_from_ndarray(payload=img, ext='jpg'})
# or from raw bytes
wi = WrappaImage({'payload': raw_bytes, 'ext': 'jpg'})
```

**image_url**

DSModel.predict expected to produce **WrappaObject** with **WrappaImage** set.
You can init **WrappaImage** with image url by using this snippet:
```python
wi = WrappaImage(url='url_of_image'})
```

**file**

Same as **image** but with **WrappaFile**.

**file_url**

Same as **image** but with **WrappaFile**.

**text**

DSModel.predict expected to produce **WrappaObject** with **WrappaText** set.

You can init **WrappaText** with your markdown text by using this snippet:
```python
wt = WrappaText('some **markdown** text')
```

**list**

DSModel.predict expected to produce list of **WrappaObject** with needed properties set.

For example, if you provide several outputs in config:
```yaml
output:
  - image
  - text
```
then DSModel predict for each input should return following object:
```python
wi = WrappaImage(...)
wt = WrappaText(...)
out = WrappaObject(wi, wt)
```

If you provide:
```yaml
output:
  - image_url
  - text
  - list
```
then you need to return following object for each input you get:
```python
wi1 = WrappaImage(...)
wt1 = WrappaText(...)
wi2 = WrappaImage(...)
wt2 = WrappaText(...)
out = [WrappaObject(wi1, wt1), WrappaObject(wi2, wt2)]
```

**json**

This one is tricky. If you need to create JSON api, provide this key. It means,
that you need to take additional argument in predict model `as_json`. If it's true,
return valid JSON, if false, return values appropriate for your output specification.
You can return anything you like ignoring any other specification.

If you provide:
```yaml
output:
  - image_url
  - text
  - list
  - json
```
then you need to return following object:
```json
[{
  "image_url": "path/to/image",
  "text": "some **markdown** __text__",
  "some_other_property": 42,
  "and_another_one": "foo"
}]
```

## DSModel interface
DSModel need to be accessible from provided path, what means it need to be importable.
It means [relative imports](https://docs.python.org/2.5/whatsnew/pep-328.html) and etc.
`DSModel` naming is required for wrappa to work.

DSModel interface example:
```python
from wrappa import WrappaObject, WrappaText, WrappaImage

class DSModel:
  def __init__(self, **kwargs):
    pass

  def predict(self, data, as_json=False):
    if as_json:
      return [{
        'text': 'hello',
        'value': 'sup?',
        'something_else': 42
      } for x in data]
    return [WrappaObject(
      WrappaImage(
        payload='bytes representation',
        ext='jpg'
      }),
      WrappaText('some **markdown** __text__')
    ) for x in data]
```

## Server description
GET /heathcheck -> returns empty response with 204 status code.

GET /info -> returns `server_info` section of config.

POST /predict ->
Expect input as follows:
Content-Type: multipart/form-data

**image**

Name: `image` for raw data

or

Name: `image_url` for image url

**file**

Name: `file` for raw data

or

Name: `file_url` for image url

**text**

Name: `text`

## Server response
Server returns multipart/form-data or application/json if `json` field provided in output specification.

## Working with wrappa server

If you provide passphrase it will be required to get access to your service.
Pass passphrase in `Authorization` header like this `Authorization: Token your_passphrase`.

In order to get access to JSON version of api make sure that `json` included in output specification and provide following header `Accept: application/json`.

## Working with wrappa client

You can use wrappa client to access wrappa server in a convenient way.
When http code differs from 2xx error will be raised.
```python
from wrappa import Client, WrappaObject, WrappaImage


cl = Client('http://localhost:8000', '123456')

wo = WrappaObject(WrappaImage(
    url='https://pbs.twimg.com/profile_images/54789364/JPG-logo-highres.jpg'))

# Heathcheck example
resp = cl.healthcheck()
# Prediction is a WrappaObject or [WrappaObject]
# Depends on provided specification
resp = cl.predict(wo)
```


### Legacy support
To use DSModel suitable for wrappa 0.1.x add legacy decorator as follows:
```python
from wrappa import legacy_converter
class DSModel:

    def __init__(self, **kwargs):
        pass

    @legacy_converter
    def predict(self, data, json):
        if json:
            return [[{
                'text': 'Test1'
            }, {
                'text': 'Тест2'
            }]]

        res = [[
            {
                'image': v['image'],
                'text': 'Test1',
            }, {
                'image': v['image'],
                'text': 'Тест2',
            }] for v in data]
        return res
```
