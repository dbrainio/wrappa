from .base import WrappaObject, WrappaImage, WrappaText


def _parse_legacy_response(resp):
    wo = WrappaObject()
    if resp.get('image'):
        wi = WrappaImage(
            payload=resp['image']['payload'],
            ext=resp['image']['ext'],
        )
        wo.set_value(wi)
    if resp.get('text'):
        wt = WrappaText(text=resp['text'])
        wo.set_value(wt)
    if resp.get('image_url'):
        wi = WrappaImage(
            url=resp['image_url']
        )
        wo.set_value(wi)
    return wo


def legacy_converter(f):
    def _f(self, data, json=False):
        legacy_data = []
        for d in data:
            legacy_d = {}
            if d.image:
                legacy_d['image'] = {
                    'payload': d.image.payload,
                    'ext': d.image.ext,
                }
            if d.text:
                legacy_d['text'] = d.text.text
            legacy_data.append(legacy_d)

        if 'json' in f.__code__.co_varnames:
            resp = f(self, legacy_data, json)
        else:
            resp = f(self, legacy_data)

        if json:
            return resp

        new_resp = []
        for el in resp:
            if isinstance(el, list):
                new_resp.append(list(map(_parse_legacy_response, el)))
            else:
                new_resp.append(_parse_legacy_response(el))
        return new_resp
    return _f
