import config.settings.base as base
import string
import random
from datetime import datetime
import os


def generate_random_string(length=12, mode='ud'):
    if mode == 'ud':
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    elif mode == 'ld':
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    else:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def get_media_directory(request, level, sub_date=True):
    directory_name = f'{base.BASE_DIR}/file/'
    if level == 5:
        directory_name += 'file_bridge/'

    if sub_date:
        directory_name += datetime.utcnow().strftime('%Y-%m-%d') + '/'

    if not os.path.exists(directory_name):
        os.makedirs(directory_name)

    return directory_name
