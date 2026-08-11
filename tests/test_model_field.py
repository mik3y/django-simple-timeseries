import json
from datetime import UTC, datetime

from django.core import serializers
from django.test import TestCase
from freezegun import freeze_time

from django_simple_timeseries.models import TimeseriesField
from django_simple_timeseries.timeseries import Timeseries

from .models import BasicModel


class TimeseriesFieldTests(TestCase):
    maxDiff = None

    @freeze_time("2021-04-03")
    def test_unsaved_with_defaults(self):
        o = BasicModel()
        self.assertEqual(1440, o.ts1.max_points)
        self.assertEqual(60, o.ts1.resolution.seconds)
        self.assertEqual(datetime(2021, 4, 3, tzinfo=UTC), o.ts1.start_time)
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
                    "ts1": {
                        "v": 1,
                        "start": "2021-04-03T00:00:00+00:00",
                        "data": [],
                        "max": 1440,
                        "res": 60,
                    },
                    "ts2": {
                        "v": 1,
                        "start": "2021-04-03T00:00:00+00:00",
                        "data": [],
                        "max": 3,
                        "res": 5,
                    },
                },
            },
            obj[0],
        )

    def test_empty_series_round_trips(self):
        """An empty series keeps its start_time across saves instead of being reset."""
        with freeze_time("2021-04-03"):
            o = BasicModel()
        with freeze_time("2021-05-05"):
            o.save()
            o.refresh_from_db()
        self.assertEqual(datetime(2021, 4, 3, tzinfo=UTC), o.ts1.start_time)

        field = BasicModel._meta.get_field("ts1")
        self.assertIs(o.ts1, field.to_python(o.ts1))

    def test_custom_default(self):
        """An explicit default is used, and survives deconstruction for migrations."""

        def make_series():
            return Timeseries(max_points=2, resolution_seconds=10)

        field = TimeseriesField(default=make_series)
        self.assertEqual(2, field.get_default().max_points)
        _, _, _, kwargs = field.deconstruct()
        self.assertIs(make_series, kwargs["default"])

        default_field = TimeseriesField()
        _, _, _, kwargs = default_field.deconstruct()
        self.assertNotIn("default", kwargs)

    def test_verbose_name_as_positional(self):
        """The Django convention of a positional verbose_name must not eat the config kwargs."""
        field = TimeseriesField("temperature history")
        self.assertEqual("temperature history", field.verbose_name)
        self.assertEqual(60, field.resolution_seconds)
        self.assertEqual(60 * 24, field.max_points)

    def test_get_prep_value_rejects_unsupported_types(self):
        field = BasicModel._meta.get_field("ts1")
        for bad in (123, "not a timeseries", {"v": 1}, [1, 2]):
            with self.assertRaises(TypeError, msg=repr(bad)):
                field.get_prep_value(bad)

    def test_malformed_db_value_returns_default(self):
        """A stored object missing keys is replaced with a fresh series, not a KeyError."""
        field = BasicModel._meta.get_field("ts1")
        with freeze_time("2021-05-05"):
            ts = field.from_db_value(json.dumps({"v": 1}), None, None)
        self.assertEqual(datetime(2021, 5, 5, tzinfo=UTC), ts.start_time)
        self.assertEqual([], ts.data_points)

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

        self.assertEqual(datetime(2021, 5, 5, tzinfo=UTC), objects[0].object.ts1.start_time)
        self.assertEqual(datetime(2021, 4, 3, tzinfo=UTC), objects[0].object.ts2.start_time)
