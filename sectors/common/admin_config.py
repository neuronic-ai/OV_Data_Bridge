TRACE_MODE = False

BRIDGE_HANDLE = None

LOCAL_CACHE_LIMIT = 100

frequency = [
    {'name': '5s', 'second': 5},
    {'name': '1m', 'second': 60},
    {'name': '5m', 'second': 300},
    {'name': '1h', 'second': 3600},
]

BRIDGE_TYPE = [
    {'type': 1, 'abbreviation': 'ws2wh', 'description': 'WebSocket > WebHook'},
    {'type': 2, 'abbreviation': 'wh2ws', 'description': 'WebHook > WebSocket'},
    {'type': 3, 'abbreviation': 'ws2api', 'description': 'API > WebSocket'},
    {'type': 4, 'abbreviation': 'ws2wh', 'description': 'WebSocket > API'},
]


def get_bridge_description(b_type):
    for bridge in BRIDGE_TYPE:
        if bridge['type'] == b_type:
            return bridge

    return None
