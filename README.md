## Description
**dbrdsw** is a util to wrap any interface implementing DSModel in a http server.

## Config
```yaml
server_info:
  # address where this service wil be available
  address: "http://localhost:8000"
  # what DSModel expects as an input and what it produce
  specification:
    input: image
    output: image
  # display name in interface
  name: "test app"
  # message to be shown before accepting input in interface
  invitation_message: "send image"
# port where service will run
port: 8000
# section describing DSModel
ds_model_config:
  # absolute (!) path to importable (!!!) package
  model_path: 'path/to/DSModel'
  # config which will be passed to DSModel contructor
  config: {}
```

## Supported specification

### Input
**image**

Array of bytes representation of an image will be passed to DSModel.predict

### Output
**image**

Array of bytes representation of an image is expecting to be produced from DSModel.predict

**image_url+text**

DSModel.predict produces following object:
```json
{
  "url": "http://path/to/image",
  "text": "Some basic **markdown** __text__"
}
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
Accepts inputs as follows:

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
