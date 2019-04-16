import argparse

from wrappa import App, read_config


def main():
    parser = argparse.ArgumentParser(description='Process config.yml file')
    parser.add_argument('--config', '-c', default='./config.yml',
                        help='path to config.yml (default: ./config.yml)')
    parser.add_argument('--disable-consul', '-dc', action='store_true',
                        help='True to not to sync with consul (default: False)')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='True to run in debug mode (default: False)')
    parser.add_argument('--port', '-p', default=None,
                        help='Port of running server (default: None)')
    parser.add_argument('--db',
                        help='Database access details (only mongo for now)')

    args = parser.parse_args()
    config = read_config(args.config)

    if args.port is not None:
        config['port'] = args.port

    app = App(
        debug=args.debug, disable_consul=args.disable_consul, db=args.db,
        **config
    )

    app.start()


if __name__ == '__main__':
    main()
