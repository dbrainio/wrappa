from gevent import monkey

monkey.patch_all(subprocess=True)

import argparse
import multiprocessing

import gunicorn.app.base
from gunicorn.six import iteritems

from wrappa import App, read_config


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    parser = argparse.ArgumentParser(description='Process config.yml file')
    parser.add_argument('--config', '-c', default='./config.yml',
                        help='path to config.yml (default: ./config.yml)')
    parser.add_argument('--disable-consul', action='store_true',
                        help='True to sync with consul (default: True)')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='True to run in debug mode (default: False)')

    args = parser.parse_args()
    config = read_config(args.config)

    print(args)

    app = App(debug=args.debug, disable_consul=args.disable_consul, **config)

    options = {
        'bind': '%s:%s' % ('0.0.0.0', config['port']),
        'workers': 1,
        'worker_class': 'gevent'
    }

    # StandaloneApplication(app.app, options).run()
    app.start()


if __name__ == '__main__':
    main()
