import _thread as thread
import time
from datetime import datetime

from sectors.common import admin_config

from db.models import (
    TBLBridge,
    TBLSetting,
    TBLUser,
    TBLTransaction,
)


class Billing:
    """
    Manage Billing
    """

    def __init__(self):
        self.bridges_info = []

    def run_cp(self):
        while True:
            utc_now = datetime.utcnow()
            if 23 <= utc_now.hour < 24:
                setting = list(TBLSetting.objects.all().values())
                if len(setting) == 0:
                    continue

                price_setting = setting[0]['price_setting']

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

                        user = TBLUser.objects.get(id=bridge.user_id)
                        if c_p > 0:
                            user.balance = round(user.balance - c_p, admin_config.ROUND_DIGIT)
                            user.spent = round(user.spent + c_p, admin_config.ROUND_DIGIT)
                            user.save()

                        transaction = TBLTransaction()
                        transaction.user_id = bridge.user_id
                        transaction.mode = 1
                        transaction.amount = c_p
                        transaction.balance = user.balance
                        transaction.description = f'Bridge ({bridge.name}): Conversion Fee - {bill_api_calls} calls'
                        transaction.notes = f'Pricing: ' + (f'$ {conversion_price} Per 1000 Conversion' if conversion_price != 0 else 'Free')
                        transaction.save()

                        bridge.billed_calls = bridge.api_calls
                        bridge.save()

                self.check_bridge_out_of_funds()

            time.sleep(3600)
        pass

    def start_conversion_pricing(self):
        thread.start_new_thread(self.run_cp, ())

    # def run_mp(self):
    #     pass
    #
    # def start_monthly_pricing(self):
    #     pass
    #
    # def run_mf(self):
    #     pass
    #
    # def start_monthly_fee(self):
    #     pass

    def check_bridge_out_of_funds(self):
        bridges = TBLBridge.objects.all()

        for bridge in bridges:
            if bridge.user.balance <= 0:
                bridge.is_status = 1
            else:
                bridge.is_status = 0

            bridge.save()
