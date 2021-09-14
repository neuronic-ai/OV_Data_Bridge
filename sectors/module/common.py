import json
import _thread as thread
import requests
import urllib.request as req
import os

from sectors.common import admin_config, common, error


def get_formatted_content(message, bridge_info):
    content = {'content': message}
    format_json = json.loads(bridge_info['format'])
    search_word = format_json['search_word']
    replace_word = format_json['replace_word']
    any = format_json['any']

    if search_word:
        replaceable = False
        search_word_array = search_word.split(',')
        if any:
            for sw in search_word_array:
                if sw.strip() in message:
                    replaceable = True
                    break
        else:
            replaceable = True
            for sw in search_word_array:
                if sw.strip() not in message:
                    replaceable = False
                    break

        if replaceable:
            if replace_word:
                try:
                    content = json.loads(replace_word)
                except:
                    content = {'content': replace_word}
    else:
        replaceable = True

    return replaceable, content


def thread_swm(group_name, content):
    if 'type' not in content or content['type'] != 'notify':
        content['type'] = 'notify'

    res = requests.post(f'http://{admin_config.OV_WEBSOCKET_HOST_URL}/event/notify_event', json={
        'type': 'on_message',
        'bridge_id': None,
        'data': {
            'group_name': group_name,
            'content': content
        }
    })


def send_ws_message(group_name, content):
    thread.start_new_thread(thread_swm, (group_name, content))


def check_validity_remote_file(request, url):
    try:
        if url.lower()[url.rfind('.') + 1:] not in ['txt', 'csv', 'zip', 'gzip', 'js']:
            return error.INVALID_FILE_WEB_TYPE, 403

        directory_name = common.get_media_directory(request, 5)
        filename = directory_name + url[url.rfind('/') + 1:]
        req.urlretrieve(url, filename)
        os.remove(filename)
        return 'success', 200
    except:
        return error.INVALID_FILE_WEB_URL, 403


def get_remote_file_data(request, bridge_info):
    try:
        url = bridge_info['src_address']

        directory_name = common.get_media_directory(request, 5)
        filename = directory_name + url[url.rfind('/') + 1:]
        req.urlretrieve(url, filename)

        try:
            file = open(filename, 'r')
            data = file.read()
            file.close()
        except:
            return error.UNABLE_TO_READ_FILE, 403

        os.remove(filename)
        return data, 200
    except:
        return error.INVALID_FILE_WEB_URL, 403
