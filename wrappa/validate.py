import importlib.util
import argparse
import json

import numpy as np

from wrappa import read_config, WrappaFile, \
    WrappaText, WrappaImage, WrappaObject


def validate_output_spec(spec, v):
    if 'image' in spec['output'] \
            and (not isinstance(v.image, WrappaImage) or
                 v.image is None or v.image.ext is None or '.' in v.image.ext):
        raise TypeError(
            'Image provided in output spec, but result of prediction is type of {t}'.format(
                t=type(v.image)
            ))
    if 'text' in spec['output'] and (not isinstance(v.text, WrappaText) or v.text.text is None):
        raise TypeError(
            'Text provided in output spec, but result of prediction is type of {t}'.format(
                t=type(v.text)
            ))
    if 'file' in spec['output'] and (not isinstance(v.file, WrappaFile) or v.file.payload is None):
        raise TypeError(
            'File provided in output spec, but result of prediction is type of {t}'.format(
                type(v.file)
            ))


def main():
    parser = argparse.ArgumentParser(description='Process config.yml file')
    parser.add_argument('--config', '-c', default='./config.yml',
                        help='path to config.yml (default: ./config.yml)')

    args = parser.parse_args()
    config = read_config(args.config)

    spec = config.get('specification')
    wo = WrappaObject()
    for input_spec in spec['input']:
        if input_spec == 'image':
            default_image = np.array([[254] * 300] * 300, dtype=np.uint8)
            wo.set_value(WrappaImage.init_from_ndarray(**{
                'payload': default_image,
                'ext': 'jpg'
            }))
        elif input_spec == 'file':
            default_bytes = bytes('a' * 1000, encoding='utf8')
            wo.set_value(WrappaFile(**{
                'payload': default_bytes,
                'ext': 'txt'
            }))
        elif input_spec == 'text':
            wo.set_value(WrappaText('Test'))

    module_spec = importlib.util.spec_from_file_location(
        'DSModel', config['ds_model_config']['model_path'])
    ds_lib = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(ds_lib)
    # Init ds model
    model = ds_lib.DSModel(**config['ds_model_config']['config'])

    if 'json' in spec['output']:
        [res, *_] = model.predict([wo], json=True)
        # It will fail if not JSON serializable
        json.dumps(res)

    f_kwargs = {}
    if 'json' in model.predict.__code__.co_varnames:
        f_kwargs['json'] = False

    [res, *_] = model.predict([wo], **f_kwargs)

    if 'list' in spec['output']:
        if not isinstance(res, list):
            raise TypeError(
                'List provided in output spec, but result of prediction is type of {t}'.format(
                    t=type(res)
                ))
        for v in res:
            validate_output_spec(spec, v)
    else:
        validate_output_spec(spec, res)
    print('Everything is fine!')


if __name__ == '__main__':
    main()
