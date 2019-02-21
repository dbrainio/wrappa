import os
from time import time
from ..models import WrappaObject
import json

from threading import Thread
from functools import partial


class FileStorage:

    def __init__(self, fpath='.'):
        if not (os.path.exists(fpath) or os.path.isdir(fpath)):
            os.mkdir(fpath)
        self._fpath = fpath

    def add(self, token, inp, out):
        thr = Thread(target=self._add, args=(self._fpath, token, inp, out))
        thr.start()

    @staticmethod
    def _add(storagepath, token, inp, out):
        def _handle_wo(storagepath, prefix, wo, t, counter=None):
            data = {}
            suffix = str(counter) + '_' if counter is not None else ''
            if wo.image and wo.image.payload:
                imgpath = os.path.join(
                    storagepath, prefix + '_image_' + suffix + t)
                imgpath = wo.image.save_to_disk(imgpath)
                data['image'] = imgpath.replace(storagepath + '/', '')
            if wo.file and wo.file.payload:
                fpath = os.path.join(
                    storagepath, prefix + '_file_' + suffix + t)
                fpath = wo.image.save_to_disk(fpath)
                data['file'] = fpath.replace(storagepath + '/', '')
            if wo.text:
                data['text'] = wo.text.text
            return data

        if not isinstance(inp, (WrappaObject, list)):
            raise TypeError('inp must be WrappaObject or list')
        _prefix = str(time()).replace('.', '_')
        if token is not None:
            _prefix += '_' + token
        data = {}
        handle_wo = partial(_handle_wo, storagepath, _prefix)
        for t, el in (('inp', inp), ('out', out)):
            data[t] = {}
            if isinstance(el, list):
                wos = []
                for i, x in enumerate(el):
                    if isinstance(x, WrappaObject):
                        wos.append(handle_wo(x, t, i))
                if wos:
                    data[t] = wos
                else:
                    data[t]['json'] = el
            if isinstance(el, WrappaObject):
                data[t] = handle_wo(el, t)
            elif isinstance(el, dict):
                data[t]['json'] = el
            elif isinstance(el, str):
                data[t]['error'] = el
        metapath = os.path.join(
            storagepath, _prefix + '_meta.json')

        with open(metapath, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return metapath
