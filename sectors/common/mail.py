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
        print(smtp_setting)
        print(smtp_setting['smtp_server_name'])
        print(smtp_setting['smtp_port'])
        # s = smtplib.SMTP(host=smtp_setting['smtp_server_name'], port=int(smtp_setting['smtp_port']))
        s = smtplib.SMTP(host='smtp.gmail.com', port=587)

        print(smtp_setting['smtp_enable_starttls'])
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
        smtp_setting = json.loads(setting[0]['smtp_setting'])

    msg = MIMEMultipart('alternative')
    msg["from"] = smtp_setting['smtp_username']
    msg["to"] = recipient_list

    if email_type == 'SMTP_TEST':
        msg["Subject"] = 'SMTP TEST EMAIL'
        content = 'Hello'
    elif email_type == 'RESET_PASSWORD':
        msg['Subject'] = 'OCEAN VANTAGE - RESET PASSWORD'
        if msg_content:
            content = msg_content
        else:
            content = ''
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
