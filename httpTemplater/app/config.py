import os
import logging.config
import yaml


def get_config():
    return {
        'REDIS_ADDR': os.environ.get('RHOST', '127.0.0.1'),
        'REDIS_PORT': os.environ.get('RPORT', '6379'),
        'DB_NAME': int(os.environ.get('RDB_NAME', 0)),
        'REDIS_PASS': os.environ.get('RPASS', None)
    }


def config_logging():
    with open('logging.yaml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
