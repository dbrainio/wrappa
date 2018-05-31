import argparse

from dbrdsw import App, read_config


def main():
    parser = argparse.ArgumentParser(description='Process config.yml file')
    parser.add_argument('--config', '-c', default='./config.yml',
                        help='path to config.yml (default: ./config.yml)')
    parser.add_argument('--debug', '-d', default=False,
                        help='True to run un debug mode (default: False)')

    args = parser.parse_args()

    config = read_config(args.config)
    app = App(debug=args.debug, **config)
    app.start()


if __name__ == '__main__':
    main()
