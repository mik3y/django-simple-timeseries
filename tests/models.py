from django.db import models

from django_simple_timeseries.models import TimeseriesField


class BasicModel(models.Model):
    ts1 = TimeseriesField()
    ts2 = TimeseriesField(max_points=3, resolution_seconds=5)
