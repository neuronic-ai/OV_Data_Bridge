import os
import json
from threading import Lock
from zipfile import ZIP_DEFLATED, ZipFile
from datetime import datetime
import pytz

from sectors.common import admin_config, common

from db.models import (
    TBLLog
)


class BridgeLog:
    """
    Log management for Bridge
    """

    def __init__(self, bridge_info):
        self.bridge_info = bridge_info

        self.log_file_name = f"{admin_config.BRIDGE_LOG_PATH}/{admin_config.BRIDGE_LOG_PREFIX}_{bridge_info['id']}.log"
        self.log_file = open(self.log_file_name, 'a')

        self.quantity = 0
        self.mutex = Lock()

        try:
            log = TBLLog.objects.get(bridge_id=bridge_info['id'], is_full=False)
            self.zip_file_name = log.filename
        except:
            self.add_new_log()

    def close(self):
        self.log_file.close()

    def add_new_log(self):
        self.zip_file_name = f'{common.generate_random_string()}.zip'

        log = TBLLog()
        log.bridge_id = self.bridge_info['id']
        log.filename = self.zip_file_name
        log.save()

    def get_last_log(self, lines=100):
        final_last_log = []
        last_log = []

        try:
            f_name = self.log_file_name

            step_size = 2048
            file_size = os.stat(f_name).st_size
            iter = 0

            with open(f_name) as file:
                if step_size > file_size:
                    move_buf_size = file_size
                else:
                    move_buf_size = step_size

                fetched_lines = []

                while True:
                    iter += 1

                    file.seek(file_size - move_buf_size * iter)

                    fetched_lines.extend(file.readlines())
                    last_log = fetched_lines + last_log

                    if len(fetched_lines) >= lines or step_size * iter > file_size:
                        break

        except Exception as e:
            if admin_config.TRACE_MODE:
                print(e)

        for ll in last_log:
            try:
                ll_json = json.loads(ll[:-1])
                ll_json['date'] = datetime.strptime(ll_json['date'], '%m/%d/%Y, %H:%M:%S')
                ll_json['date'] = ll_json['date'].strftime('%m/%d/%Y, %H:%M:%S')
                final_last_log.append(ll_json)
            except:
                pass

        return final_last_log

    def write_log(self, cache_data):
        self.mutex.acquire()
        try:
            self.log_file.write(cache_data)
            self.log_file.write('\n')
            self.log_file.flush()

            self.quantity += 1

            if self.quantity % admin_config.BRIDGE_LOG_ZIP_FREQUENCY == 0:
                zip_filepath = f'{admin_config.BRIDGE_LOG_ZIP_PATH}/{self.zip_file_name}'
                zip_obj = ZipFile(zip_filepath, 'w', ZIP_DEFLATED)
                head, tail = os.path.split(self.log_file.name)
                zip_obj.write(self.log_file.name, tail)
                zip_obj.close()
                zip_size = os.path.getsize(zip_filepath)

                try:
                    log = TBLLog.objects.get(bridge_id=self.bridge_info['id'], is_full=False)
                    log.size = zip_size
                    log.date_to = datetime.now(tzinfo=pytz.UTC)
                    if zip_size > admin_config.BRIDGE_LOG_MAX_SIZE:
                        log.is_full = True
                        self.add_new_log()
                        self.log_file.truncate(0)

                    log.save()
                except Exception as e:
                    if admin_config.TRACE_MODE:
                        print(e)
        except Exception as e:
            if admin_config.TRACE_MODE:
                print(e)

        self.mutex.release()
