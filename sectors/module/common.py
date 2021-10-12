import json
import _thread as thread
import requests
from datetime import datetime

from sectors.common import admin_config, error


def get_formatted_content(message, bridge_info):
    try:
        data = json.loads(message)
    except:
        data = message
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
                    data = json.loads(replace_word)
                except:
                    data = replace_word
    else:
        replaceable = True

    return replaceable, {
        'date': datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S'),
        'data': data
    }


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
        if url.lower()[url.rfind('.') + 1:] not in ['txt', 'csv', 'zip', 'gzip']:
            return error.INVALID_FILE_WEB_TYPE, 403

        requests.get(url, verify=False)
        return 'success', 200
    except Exception as e:
        return str(e), 403


def get_remote_file_data(request, bridge_info):
    try:
        url = bridge_info['src_address']

        res = requests.get(url, verify=False)
        try:
            data = res.content.decode()
        except:
            return error.UNABLE_TO_READ_FILE, 403

        data_array = data.split('\n')
        json_data_array = []
        for d in data_array:
            if d:
                try:
                    json_d = json.loads(d)
                except:
                    json_d = d
                json_data_array.append(json_d)

        return json_data_array, 200
    except:
        return error.INVALID_FILE_WEB_URL, 403


def get_diff_lists(request, f_list, s_list):
    r_list = []
    for s in s_list:
        if s not in f_list:
            r_list.append(s)

    return r_list

