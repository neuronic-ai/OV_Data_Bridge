from django.db import models
from django.contrib.auth.models import AbstractUser
import json

from sectors.common import admin_config


class TBLUser(AbstractUser):
    balance = models.FloatField(default=0)
    spent = models.FloatField(default=0)
    reset_link = models.CharField(max_length=255, default='')
    permission = models.TextField(default=json.dumps({
        'max_active_bridges': admin_config.DEFAULT_MAX_ACTIVE_BRIDGES,
        'rate_limit_per_url': admin_config.DEFAULT_RATE_LIMIT_PER_URL,
        'allowed_frequency': admin_config.DEFAULT_ALLOWED_FREQUENCY,
        'allowed_file_flush': admin_config.DEFAULT_ALLOWED_FILE_FLUSH,
        'available_bridges': admin_config.DEFAULT_AVAILABLE_BRIDGE
    }))

    class Meta:
        db_table = 'TBLUSER'


class TBLBridge(models.Model):
    user = models.ForeignKey(TBLUser, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255, default='')
    type = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    api_calls = models.IntegerField(default=0)
    src_address = models.CharField(max_length=255, default='')
    dst_address = models.CharField(max_length=255, default='')
    format = models.TextField(blank=True, null=True)
    frequency = models.IntegerField(default=0)
    flush = models.IntegerField(default=0)
    file_format = models.CharField(max_length=255, default='')
    billed_calls = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_status = models.IntegerField(default=0)
    monthly_usage = models.IntegerField(default=0)

    class Meta:
        db_table = 'TBLBRIDGE'


class TBLLog(models.Model):
    bridge = models.ForeignKey(TBLBridge, on_delete=models.CASCADE, blank=True, null=True)
    filename = models.CharField(max_length=255, default='')
    size = models.IntegerField(default=0)
    date_from = models.DateTimeField(auto_now_add=True)
    date_to = models.DateTimeField(auto_now_add=True)
    is_full = models.BooleanField(default=False)

    class Meta:
        db_table = 'TBLLOG'


class TBLSetting(models.Model):
    server_setting = models.JSONField(default=dict)
    max_active_bridges = models.IntegerField(default=0)
    rate_limit_per_url = models.IntegerField(default=0)
    allowed_frequency = models.JSONField(default=dict)
    allowed_file_flush = models.JSONField(default=dict)
    available_bridges = models.JSONField(default=dict)
    price_setting = models.JSONField(default=dict)
    smtp_setting = models.JSONField(default=dict)

    class Meta:
        db_table = 'TBLSETTING'


class TBLTransaction(models.Model):
    user = models.ForeignKey(TBLUser, on_delete=models.CASCADE, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    mode = models.IntegerField(default=0)
    amount = models.FloatField(default=0)
    balance = models.FloatField(default=0)
    description = models.CharField(max_length=255, default='')
    notes = models.CharField(max_length=255, default='')

    class Meta:
        db_table = 'TBLTRANSACTION'
