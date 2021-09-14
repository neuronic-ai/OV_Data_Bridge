import os
from threading import Lock
from datetime import datetime
from zipfile import ZIP_DEFLATED, ZipFile

from sectors.common import admin_config


class File:
    """
    File management for Bridge
    """

    def __init__(self, file_name, ext):

        self.file_name = file_name[file_name.find('file'):]
        self.directory_name = self.file_name[:self.file_name.rfind('/') + 1]
        self.ext = ext
        if not os.path.exists(self.directory_name):
            os.makedirs(self.directory_name)

        if self.ext == 'zip':
            self.file = open(f'{self.file_name}.txt', 'a')
        else:
            self.file = open(f'{self.file_name}.{self.ext}', 'a')

        self.mutex = Lock()

    def close(self):
        self.file.close()

    def write(self, data):
        self.mutex.acquire()
        try:
            f_data = f"{datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S')} | {data}"

            if self.ext == 'csv':
                self.file.write(f"'{f_data}',")
            else:
                self.file.write(f_data)
                self.file.write('\n')

            self.file.flush()

            if self.ext == 'zip':
                zip_obj = ZipFile(f'{self.file_name}.zip', 'w', ZIP_DEFLATED)
                head, tail = os.path.split(f'{self.file_name}.txt')
                zip_obj.write(f'{self.file_name}.txt', tail)
                zip_obj.close()
        except Exception as e:
            if admin_config.TRACE_MODE:
                print(e)

        self.mutex.release()

    def truncate(self):
        self.file.truncate(0)
        self.file.flush()
