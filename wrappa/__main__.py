import argparse

from wrappa import App, read_config


def main():
    parser = argparse.ArgumentParser(description='Process config.yml file')
    parser.add_argument('--config', '-c', default='./config.yml',
                        help='path to config.yml (default: ./config.yml)')
    parser.add_argument('--disable-consul', action='store_true',
                        help='True to not to sync with consul (default: False)')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='True to run in debug mode (default: False)')

    args = parser.parse_args()
    config = read_config(args.config)

    if config.get('passphrase'):
        if isinstance(config['passphrase'], str):
            config['passphrase'] = [config['passphrase']]

    app = App(debug=args.debug, disable_consul=args.disable_consul, **config)

    app.start()


if __name__ == '__main__':
    main()
