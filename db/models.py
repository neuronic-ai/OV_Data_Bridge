from django.db import models
from django.contrib.auth.models import AbstractUser


class TBLUser(AbstractUser):
    permission = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'TBLUSER'


BRIDGE_TYPE = [
    (1, 'ws2wh'),
    (2, 'wh2ws'),
    (3, 'ws2api'),
    (4, 'api2ws'),
]


class TBLBridge(models.Model):
    user = models.ForeignKey(TBLUser, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255, default='')
    type = models.IntegerField(choices=BRIDGE_TYPE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    api_calls = models.IntegerField(default=0)
    src_address = models.CharField(max_length=255, default='')
    dst_address = models.CharField(max_length=255, default='')
    format = models.TextField(blank=True, null=True)
    frequency = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'TBLBRIDGE'
