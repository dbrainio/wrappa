from yaml import load


def read_config(path):
    return load(open(path, 'r'))
