from datetime import datetime, timezone

from django.test import TestCase
from freezegun import freeze_time

from django_simple_timeseries.timeseries import Timeseries

from .models import BasicModel


class TimeseriesFieldTests(TestCase):
    @freeze_time("2021-04-03")
    def test_unsaved_with_defaults(self):
        o = BasicModel()
        self.assertEqual(1440, o.ts1.max_points)
        self.assertEqual(60, o.ts1.resolution.seconds)
        self.assertEqual(datetime(2021, 4, 3, tzinfo=timezone.utc), o.ts1.start_time)
        self.assertEqual(
            {
                "resolution_seconds": 60,
                "max_points": 1440,
                "data_points": [],
                "start_time": "2021-04-03T00:00:00+00:00",
            },
            o.ts1.to_object(),
        )
        self.assertEqual(Timeseries(max_points=1440, resolution_seconds=60), o.ts1)

        self.assertEqual(3, o.ts2.max_points)
        self.assertEqual(5, o.ts2.resolution.seconds)
        self.assertEqual(
            {
                "resolution_seconds": 5,
                "max_points": 3,
                "data_points": [],
                "start_time": "2021-04-03T00:00:00+00:00",
            },
            o.ts2.to_object(),
        )
        self.assertEqual(Timeseries(max_points=3, resolution_seconds=5), o.ts2)

    def test_save_with_defaults(self):
        with freeze_time("2021-04-03"):
            o = BasicModel()
            o.save()
            o.refresh_from_db()
            self.assertEqual(1440, o.ts1.max_points)
            self.assertEqual(60, o.ts1.resolution.seconds)
            self.assertEqual(Timeseries(max_points=1440, resolution_seconds=60), o.ts1)
            o.ts1.add(1.00)
            o.save()

        o = BasicModel.objects.get(pk=o.pk)
        self.assertEqual(
            {
                "resolution_seconds": 60,
                "max_points": 1440,
                "data_points": [1.0],
                "start_time": "2021-04-03T00:00:00+00:00",
            },
            o.ts1.to_object(),
        )

        with freeze_time("2021-04-03T00:01:07"):
            o = BasicModel.objects.get(pk=o.pk)
            o.ts1.add(2.1)
            o.save()

        o = BasicModel.objects.get(pk=o.pk)
        self.assertEqual(
            {
                "resolution_seconds": 60,
                "max_points": 1440,
                "data_points": [1.0, 2.1],
                "start_time": "2021-04-03T00:00:00+00:00",
            },
            o.ts1.to_object(),
        )