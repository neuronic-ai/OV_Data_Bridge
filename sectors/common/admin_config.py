import config.settings.base as base

# HOST_URL = 'http://127.0.0.1:8000/'
HOST_URL = 'https://bridge.vantagecrypto.com/'
TRACE_MODE = False
DELETE_LOG_AFTER_BRIDGE_DELETED = True

BRIDGE_HANDLE = None

LOCAL_CACHE_LIMIT = 100  # qty
DELAY_FOR_BAD_REQUEST = 0.5  # second

BRIDGE_CONSUMER_PREFIX = 'bridge'
BRIDGE_LOG_PREFIX = 'bridge'
BRIDGE_REDIS_CACHE_PREFIX = 'bridge'
RATE_LIMIT_REDIS_CACHE_PREFIX = 'rate_limit'

BRIDGE_LOG_PATH = f'{base.BASE_DIR}/log'
BRIDGE_LOG_ZIP_PATH = f'{base.BASE_DIR}/sectors/static/log_zip'
BRIDGE_LOG_ZIP_DOWNLOAD = 'static/log_zip'

BRIDGE_LOG_ZIP_FREQUENCY = 1
BRIDGE_LOG_MAX_SIZE = 2097152     # byte
# BRIDGE_LOG_MAX_SIZE = 1000  # byte

DEFAULT_MAX_ACTIVE_BRIDGES = 1
DEFAULT_RATE_LIMIT_PER_URL = 14
DEFAULT_ALLOWED_FREQUENCY = {
    'af1': True,
    'af2': True,
    'af3': True,
    'af4': True
}
DEFAULT_AVAILABLE_BRIDGE = {
    'ab1': True,
    'ab2': True,
    'ab3': True,
    'ab4': True
}

frequency = [
    {'name': '5s', 'second': 5},
    {'name': '1m', 'second': 60},
    {'name': '5m', 'second': 300},
    {'name': '1h', 'second': 3600},
]

BRIDGE_TYPE = [
    {'type': 1, 'abbreviation': 'ws2wh', 'description': 'WebSocket > WebHook'},
    {'type': 2, 'abbreviation': 'wh2ws', 'description': 'WebHook > WebSocket'},
    {'type': 3, 'abbreviation': 'ws2wh', 'description': 'WebSocket > API'},
    {'type': 4, 'abbreviation': 'ws2api', 'description': 'API > WebSocket'},
]


def get_bridge_description(b_type):
    for bridge in BRIDGE_TYPE:
        if bridge['type'] == b_type:
            return bridge

    return None
