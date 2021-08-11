from sectors.common import admin_config
from sectors.module import bridge
import _thread as thread
import time


def run_module():
    time.sleep(5)
    if admin_config.BRIDGE_HANDLE is None:
        print('Module start...')
        try:
            admin_config.BRIDGE_HANDLE = bridge.BridgeQueue()
            admin_config.BRIDGE_HANDLE.fetch_all_bridges()
            admin_config.BRIDGE_HANDLE.start_all()
            print('Module end...')
        except Exception as e:
            print(f'Module exception...{e}')
    else:
        pass


thread.start_new_thread(run_module, ())
