import _thread as thread
import time
from datetime import datetime, timedelta

from sectors.common import admin_config

from db.models import (
    TBLBridge,
    TBLSetting,
    TBLUser,
    TBLTransaction,
)


def check_bridge_out_of_funds(user_id=None):
    if user_id is None:
        bridges = TBLBridge.objects.all()
    else:
        bridges = TBLBridge.objects.filter(user_id=user_id)

    setting = list(TBLSetting.objects.all().values())
    if len(setting) > 0:
        price_setting = setting[0]['price_setting']
        for bridge in bridges:
            if price_setting['disable_pricing']:
                bridge.is_status = 0
                bridge.save()
            else:
                if bridge.user.balance <= 0:
                    for b_p in price_setting['bridge_price']:
                        if b_p['type'] == bridge.type and b_p['is_active']:
                            bridge.is_status = 1
                            bridge.save()


class Billing:
    """
    Manage Billing
    """

    def __init__(self):
        self.bridges_info = []

    def get_price_setting(self):
        setting = list(TBLSetting.objects.all().values())
        if len(setting) == 0:
            return None

        return setting[0]['price_setting']

    def available_cp(self):
        utc_now = datetime.utcnow()
        if 23 <= utc_now.hour < 24 and 50 <= utc_now.minute < 60:
            return True
        else:
            return False

    def charge(self, amount, user_id):
        user = TBLUser.objects.get(id=user_id)
        if amount > 0:
            user.balance = round(user.balance - amount, admin_config.ROUND_DIGIT)
            user.spent = round(user.spent + amount, admin_config.ROUND_DIGIT)
            user.save()

        return user.balance

    def add_transaction(self, user_id, mode, amount, balance, description, notes):
        transaction = TBLTransaction()
        transaction.user_id = user_id
        transaction.mode = mode
        transaction.amount = amount
        transaction.balance = balance
        transaction.description = description
        transaction.notes = notes
        transaction.save()

    def run_cp(self):
        while True:
            if self.available_cp():
                try:
                    price_setting = self.get_price_setting()
                    if price_setting is None:
                        continue

                    bridges = TBLBridge.objects.all()
                    for bridge in bridges:
                        bill_api_calls = bridge.api_calls - bridge.billed_calls
                        if bill_api_calls > 0:
                            conversion_price = 0
                            if not price_setting['disable_pricing']:
                                for b_p in price_setting['bridge_price']:
                                    if b_p['type'] == bridge.type and b_p['is_active']:
                                        conversion_price = b_p['c_p']

                            c_p = round(conversion_price * bill_api_calls / 1000, admin_config.ROUND_DIGIT)

                            balance = self.charge(c_p, bridge.user_id)
                            self.add_transaction(bridge.user_id, 1, c_p, balance,
                                                 f'Bridge ({bridge.name}): Conversion Fee - {bill_api_calls} calls',
                                                 f'Pricing: ' + (f'$ {conversion_price} Per 1000 Conversion' if conversion_price != 0 else 'Free'))

                            bridge.billed_calls = bridge.api_calls
                            bridge.save()

                    check_bridge_out_of_funds()
                except:
                    pass

            time.sleep(600)
        pass

    def start_conversion_pricing(self):
        thread.start_new_thread(self.run_cp, ())

    def run_mpf(self):
        while True:
            time.sleep(3600)
            price_setting = self.get_price_setting()
            if price_setting is None:
                continue

            bridges = TBLBridge.objects.all()

            # count monthly usage
            for bridge in bridges:
                if not bridge.is_active:
                    continue

                if not price_setting['disable_pricing']:
                    for b_p in price_setting['bridge_price']:
                        if b_p['type'] == bridge.type and b_p['is_active'] and b_p['m_p'] > 0:
                            bridge.monthly_usage += 1
                            bridge.save()

            # charge monthly mpf
            for bridge in bridges:
                utc_now = datetime.utcnow()
                if utc_now > bridge.date_created + timedelta(days=30) and bridge.monthly_usage > 24 * admin_config.MONTHLY_USAGE_LIMIT:
                    m_p = 0
                    for b_p in price_setting['bridge_price']:
                        if b_p['type'] == bridge.type and b_p['is_active']:
                            m_p = b_p['m_p']

                    balance = self.charge(m_p, bridge.user_id)
                    self.add_transaction(bridge.user_id, 2, m_p, balance,
                                         f'Bridge ({bridge.name}): Monthly Bridge Fee',
                                         f'Pricing: ' + (f'$ {m_p} Per Month' if m_p != 0 else 'Free'))

                    bridge.monthly_usage = 0
                    bridge.save()

    def start_monthly_pricing_fee(self):
        thread.start_new_thread(self.run_mpf, ())
