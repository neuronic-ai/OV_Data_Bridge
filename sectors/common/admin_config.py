import config.settings.base as base
import os

HOST_URL = os.getenv('OV_HOST_URL', 'http://127.0.0.1:8000/')
OV_WEBSOCKET_HOST_URL = os.getenv('OV_WEBSOCKET_HOST', '127.0.0.1:8002')

TRACE_MODE = False
DELETE_LOG_AFTER_BRIDGE_DELETED = True

BRIDGE_HANDLE = None
BILLING_HANDLE = None

ROUND_DIGIT = 10
MONTHLY_USAGE_LIMIT = 7

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
BRIDGE_LOG_MAX_SIZE = 2097152  # byte
# BRIDGE_LOG_MAX_SIZE = 1000  # byte

DEFAULT_MAX_ACTIVE_BRIDGES = 1
DEFAULT_RATE_LIMIT_PER_URL = 14
DEFAULT_ALLOWED_FREQUENCY = {
    'af1': True,
    'af2': True,
    'af3': True,
    'af4': True
}
DEFAULT_ALLOWED_FILE_FLUSH = {
    'aff1': True,
    'aff2': True,
    'aff3': True,
    'aff4': True,
}
DEFAULT_AVAILABLE_BRIDGE = {
    'ab1': True,
    'ab2': True,
    'ab3': True,
    'ab4': True,
    'ab5': True,
    'ab6': True,
    'ab7': True,
    'ab8': True,
    'ab9': True,
    'ab10': True,
}

FREQUENCY = [
    {'type': 1, 'name': '5s', 'second': 5, 'reg': '5s Conversions'},
    {'type': 2, 'name': '1m', 'second': 60, 'reg': '1m Conversions'},
    {'type': 3, 'name': '5m', 'second': 300, 'reg': '5m Conversions'},
    {'type': 4, 'name': '1h', 'second': 3600, 'reg': '1h Conversions'},
]

FLUSH = [
    {'name': '5m', 'second': 300},
    {'name': '30m', 'second': 1800},
    {'name': '1h', 'second': 3600},
    {'name': '24h', 'second': 86400},
]

FILE_FORMAT = [
    {'name': 'txt', 'value': 'txt'},
    {'name': 'csv', 'value': 'csv'},
    {'name': 'zip', 'value': 'zip'},
]

BRIDGE = [
    {'type': 1, 'abbreviation': 'ws-wh', 'description': 'WebSocket > WebHook', 'reg': 'WSS/WS>WH', 'src': 'ws_url', 'dst': 'wh_url'},
    {'type': 2, 'abbreviation': 'wh-ws', 'description': 'WebHook > WebSocket', 'reg': 'WH>WSS/WS', 'src': 'wh_url', 'dst': 'ws_url'},
    {'type': 3, 'abbreviation': 'ws-api', 'description': 'WebSocket > API', 'reg': 'WSS/WS>API', 'src': 'ws_url', 'dst': 'api_url'},
    {'type': 4, 'abbreviation': 'api-ws', 'description': 'API > WebSocket', 'reg': 'API>WSS/WS', 'src': 'api_url', 'dst': 'ws_url'},
    {'type': 5, 'abbreviation': 'file-wh', 'description': 'FILE > WebHook', 'reg': 'FILE>WH', 'src': 'file_url', 'dst': 'wh_url'},
    {'type': 6, 'abbreviation': 'file-ws', 'description': 'FILE > WebSocket', 'reg': 'FILE>WSS/WS', 'src': 'file_url', 'dst': 'ws_url'},
    {'type': 7, 'abbreviation': 'file-api', 'description': 'FILE > API', 'reg': 'FILE>API', 'src': 'file_url', 'dst': 'api_url'},
    {'type': 8, 'abbreviation': 'wh-file', 'description': 'WebHook > FILE', 'reg': 'WH>FILE', 'src': 'wh_url', 'dst': 'file_url'},
    {'type': 9, 'abbreviation': 'ws-file', 'description': 'WebSocket > FILE', 'reg': 'WSS/WS>FILE', 'src': 'ws_url', 'dst': 'file_url'},
    {'type': 10, 'abbreviation': 'api-file', 'description': 'API > FILE', 'reg': 'API>FILE', 'src': 'api_url', 'dst': 'file_url'},
]

DISABLE_PRICING = True

BRIDGE_PRICE = [
    {'type': 1, 'm_p': 0, 'c_p': 0, 'is_active': True},
    {'type': 2, 'm_p': 0, 'c_p': 0, 'is_active': True},
    {'type': 3, 'm_p': 0, 'c_p': 0, 'is_active': True},
    {'type': 4, 'm_p': 0, 'c_p': 0, 'is_active': True},
    {'type': 5, 'm_p': 0, 'c_p': 0, 'is_active': True},
    {'type': 6, 'm_p': 0, 'c_p': 0, 'is_active': True},
    {'type': 7, 'm_p': 0, 'c_p': 0, 'is_active': True},
    {'type': 8, 'm_p': 0, 'c_p': 0, 'is_active': True},
    {'type': 9, 'm_p': 0, 'c_p': 0, 'is_active': True},
    {'type': 10, 'm_p': 0, 'c_p': 0, 'is_active': True},
]

FREQUENCY_PRICE = [
    {'type': 1, 'm_p': 0, 'is_active': True},
    {'type': 2, 'm_p': 0, 'is_active': True},
    {'type': 3, 'm_p': 0, 'is_active': True},
    {'type': 4, 'm_p': 0, 'is_active': True},
]
