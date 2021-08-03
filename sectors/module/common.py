import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import _thread as thread


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

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        content
    )


def send_ws_message(group_name, content):
    thread.start_new_thread(thread_swm, (group_name, content))
