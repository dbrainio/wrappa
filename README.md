## Description
**dbrdsw** is a util to wrap any interface implementing DSModel in a http server.

## Config
```yaml
server_info:
  # address where this service wil be available
  address: "http://localhost:8000"
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
# for debug it is optionable
consul:
  host: 127.0.0.1
  port: 8500
# section describing DSModel
ds_model_config:
  # absolute (!) path to importable (!!!) package
  model_path: 'path/to/DSModel'
  # config which will be passed to DSModel contructor
  config: {}
```

## Supported specification
All specification can be passed as mixins.

### Input
**image**

Array of bytes representation of an image will be passed to DSModel.predict
```json
{
  "image": {
    "payload": "bytes representation of image",
    "ext": "jpg"
  }
}
```

**text**
```json
{
  "text": "some text"
}
```

### Output
**image**

Array of bytes representation of an image is expecting to be produced from DSModel.predict
```json
{
  "image": {
    "payload": "bytes representation of image",
    "ext": "jpg"
  }
}
```

**image_url**

DSModel.predict produces following object:
```json
{
  "image_url": "path/to/image"
}
```

**text**

DSModel.predict produces following object:
```json
{
  "text": "some **markdown** __text__"
}
```

**list**

DSModel.predict produces list of objects for each input.

For example, if you provide several outputs in config:
```yaml
output:
  - image
  - text
```
then DSModel predict for each input should return following object:
```json
{
  "image": "bytes representation of image",
  "text": "some **markdown** __text__"
}
```

If you provide:
```yaml
output:
  - image_url
  - text
  - list
```
then you need to return following object:
```json
[{
  "image_url": "path/to/image",
  "text": "some **markdown** __text__"
}]
```

**json**

This one is tricky. If you need to create JSON api, provide this key. It means,
that you need to take additional argument in predict model `json`. If it's true,
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
`DSModel` naming is required for dbrdsw to work.

DSModel interface example:
```python
class DSModel:
  def __init__(self, **kwargs):
    pass

  def predict(self, data, json=False):
    if json:
      return [{
        'text': 'hello',
        'value': 'sup?',
        'something_else': 42
      } for x in data]
    return [{
      'image': {
        'payload': 'bytes representation',
        'ext': 'jpg'
      },
      'text': 'some **markdown** __text__',
      'image_url': 'path/to/image'
    } for x in data]
```

## Server description
GET /heathcheck -> returns empty response with 204 status code.

GET /info -> returns `server_info` section of config.

POST /predict ->
Expect input as follows:
Content-Type: multipart/form-data

**image**

Name: `file` for raw data

or

Name: `image_url` for image url

**text**

Name: `text`

## Server response
Server returns multipart/form-data or application/json if `json` field provided in output specification.

## Working with dbrdsw server

If you provide passphrase it will be required to get access to your service.
Pass passphrase in `Authorization` header like this `Authorization: Token your_passphrase`.

In order to get access to JSON version of api make sure that `json` included in output specification and provide following header `Access: application/json`.

## How to use
It's simple.

Installation: `python3 setup.py install`

If everything is fine, you'll be able to execute following command in your terminal:
`dbrdsw --help`

To run server:
`dbrdsw --config './config.yml'`

To run server in dev mode:
`dbrdsw --config './config.yml' --debug=true`
