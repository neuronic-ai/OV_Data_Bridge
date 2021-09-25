import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from sectors.common import admin_config, error

from db.models import (
    TBLSetting
)


def test_smtp(request, smtp_setting):
    try:
        s = smtplib.SMTP(host=smtp_setting['smtp_server_name'], port=int(smtp_setting['smtp_port']))
        s.ehlo()
        if smtp_setting['smtp_enable_starttls']:
            s.starttls()
        s.login(smtp_setting['smtp_username'], smtp_setting['smtp_password'])
    except Exception as e:
        if admin_config.TRACE_MODE:
            print(e)

        return False, str(e)

    return True, error.SUCCESS


def send_email(request, recipient_list, email_type, msg_content=None, html_content=None):
    setting = list(TBLSetting.objects.values('smtp_setting'))
    if len(setting) < 0:
        return False, error.SMTP_SETTING_NOT_AVAILABLE
    else:
        smtp_setting = setting[0]['smtp_setting']

    msg = MIMEMultipart('alternative')
    msg["from"] = smtp_setting['smtp_username']
    msg["to"] = recipient_list

    if email_type == 'RESET_LINK':
        msg['Subject'] = 'OCEAN VANTAGE - RESET PASSWORD'
        if msg_content:
            content = msg_content
        else:
            content = ''
    elif email_type == 'PASSWORD_CHANGED':
        msg['Subject'] = 'OCEAN VANTAGE - YOU CHANGED YOUR PASSWORD'
        content = 'If you did not change your password, please contact us right away.'
    else:
        return False, error.UNKNOWN_EMAIL_TYPE

    msg.attach(MIMEText(content))

    try:
        s = smtplib.SMTP(host=smtp_setting['smtp_server_name'], port=int(smtp_setting['smtp_port']))
        s.ehlo()
        if smtp_setting['smtp_enable_starttls']:
            s.starttls()
        s.login(smtp_setting['smtp_username'], smtp_setting['smtp_password'])
        s.send_message(msg)
    except Exception as e:
        if admin_config.TRACE_MODE:
            print(e)

        return False, str(e)

    return True, error.SUCCESS
