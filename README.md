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

### Output
**image**

Array of bytes representation of an image is expecting to be produced from DSModel.predict
```json
{
  "image": "bytes representaion of image"
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
__Note__: list is not supported for image specification.

For example, if you provide several outputs in config:
```yaml
output:
  - image
  - text
```
then DSModel predict for each input should return following object:
```json
{
  "image": "bytes representaion of image",
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

## DSModel interface
DSModel need to be accessible from provided path, what means it need to be importable.
It means [relative imports](https://docs.python.org/2.5/whatsnew/pep-328.html) and etc.
`DSModel` naming is required for dbrdsw to work.

DSModel interface example:
```python
class DSModel:
  def __init__(self, **kwargs):
    pass

  def predict(self, data):
    return [x**2 for x in data]
```

## Server description
GET /heathcheck -> returns empty response with 204 status code.

GET /info -> returns `server_info` section of config.

POST /predict ->
Expect input as follows:

**image**

Content-Type: multipart/form-data

Name: `file`


## How to use
It's simple.

Installation: `python3 setup.py install`

If everything is fine, you'll be able to execute following command in your terminal:
`dbrdsw --help`

To run server:
`dbrdsw --config './config.yml'`

To run server in dev mode:
`dbrdsw --config './config.yml' --debug=true`
