import string
import random
from datetime import datetime
import os


def generate_random_string(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def get_media_directory(request, level, sub_date=True):
    directory_name = 'file/'
    if level == 5:
        directory_name += 'file_bridge/'

    if sub_date:
        directory_name += datetime.utcnow().strftime('%Y-%m-%d') + '/'

    if not os.path.exists(directory_name):
        os.makedirs(directory_name)

    return directory_name
