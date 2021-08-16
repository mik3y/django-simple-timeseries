import json
from datetime import datetime, timezone

from django.core import serializers
from django.test import TestCase
from freezegun import freeze_time

from django_simple_timeseries.timeseries import Timeseries

from .models import BasicModel


class TimeseriesFieldTests(TestCase):
    maxDiff = None

    @freeze_time("2021-04-03")
    def test_unsaved_with_defaults(self):
        o = BasicModel()
        self.assertEqual(1440, o.ts1.max_points)
        self.assertEqual(60, o.ts1.resolution.seconds)
        self.assertEqual(datetime(2021, 4, 3, tzinfo=timezone.utc), o.ts1.start_time)
        self.assertEqual(
            {
                "v": 1,
                "res": 60,
                "max": 1440,
                "data": [],
                "start": "2021-04-03T00:00:00+00:00",
            },
            o.ts1.to_object(),
        )
        self.assertEqual(Timeseries(max_points=1440, resolution_seconds=60), o.ts1)

        self.assertEqual(3, o.ts2.max_points)
        self.assertEqual(5, o.ts2.resolution.seconds)
        self.assertEqual(
            {
                "v": 1,
                "res": 5,
                "max": 3,
                "data": [],
                "start": "2021-04-03T00:00:00+00:00",
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
                "v": 1,
                "res": 60,
                "max": 1440,
                "data": [1.0],
                "start": "2021-04-03T00:00:00+00:00",
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
                "v": 1,
                "res": 60,
                "max": 1440,
                "data": [1.0, 2.1],
                "start": "2021-04-03T00:00:00+00:00",
            },
            o.ts1.to_object(),
        )

    def test_serialization(self):
        with freeze_time("2021-04-03"):
            o = BasicModel()
            o.save()
            data = serializers.serialize("json", BasicModel.objects.all())
        obj = json.loads(data)
        self.assertEqual(1, len(obj))
        self.assertDictEqual(
            {
                "model": "tests.basicmodel",
                "pk": o.id,
                "fields": {
                    "ts1": '{"v": 1, "start": "2021-04-03T00:00:00+00:00", "data": [], "max": 1440, "res": 60}',  # noqa
                    "ts2": '{"v": 1, "start": "2021-04-03T00:00:00+00:00", "data": [], "max": 3, "res": 5}',  # noqa
                },
            },
            obj[0],
        )

    def test_deserialize_bad_value(self):
        bad_values = json.dumps(
            [
                {
                    "model": "tests.basicmodel",
                    "pk": 123,
                    "fields": {
                        "ts1": "invalid_json",
                        "ts2": '{"v": 1, "start": "2021-04-03T00:00:00+00:00", "data": [], "max": 3, "res": 5}',  # noqa
                    },
                },
            ]
        )
        with freeze_time("2021-05-05"):
            objects = list(serializers.deserialize("json", bad_values))

        self.assertEqual(
            datetime(2021, 5, 5, tzinfo=timezone.utc), objects[0].object.ts1.start_time
        )
        self.assertEqual(
            datetime(2021, 4, 3, tzinfo=timezone.utc), objects[0].object.ts2.start_time
        )
