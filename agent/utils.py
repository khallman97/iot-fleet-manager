import configparser

def load_config(path="config.ini"):
    config = configparser.ConfigParser()
    config.read(path)
    return config
