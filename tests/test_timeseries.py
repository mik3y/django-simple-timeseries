import json
import unittest
from datetime import timedelta, timezone

from django.utils.timezone import datetime

from django_simple_timeseries.timeseries import Timeseries


class TimeseriesTestCase(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2020, 1, 1, 2, 30, tzinfo=timezone.utc)
        self.ts = Timeseries(start_time=self.now, max_points=5, resolution_seconds=5)

    def test_empty_ts(self):
        self.assertEqual(
            {
                "v": 1,
                "start": "2020-01-01T02:30:00+00:00",
                "max": 5,
                "res": 5,
                "data": [],
            },
            self.ts.to_object(),
        )

    def test_downsampling_and_shifting(self):
        """Ensure datetimes are downsampled to appropriate bucket."""
        result = self.ts.add(1.23, when=self.now)
        self.assertEqual(1, len(self.ts))
        self.assertEqual(1.23, self.ts[0])
        self.assertEqual(result, Timeseries.RESULT_SHIFTED)

        # Adding a sample in the same bucket doesn't extend the series.
        result = self.ts.add(2.34, when=self.now + timedelta(seconds=1))
        self.assertEqual(1, len(self.ts))
        self.assertEqual(2.34, self.ts[0])
        self.assertEqual(result, Timeseries.RESULT_REPLACED)

        # Adding the next sample does extend the series.
        result = self.ts.add(3.14, when=self.now + timedelta(seconds=6))
        self.assertEqual(2, len(self.ts))
        self.assertEqual(2.34, self.ts[0])
        self.assertEqual(3.14, self.ts[1])
        self.assertEqual(result, Timeseries.RESULT_ADDED)

        # Adding a sample a few buckets away causes None-padding
        result = self.ts.add(4.20, when=self.now + timedelta(seconds=21))
        self.assertEqual(5, len(self.ts))
        self.assertEqual(
            [
                2.34,
                3.14,
                None,
                None,
                4.20,
            ],
            self.ts.data_points,
        )
        self.assertEqual(result, Timeseries.RESULT_ADDED)
        self.assertEqual(self.now, self.ts.start_time)

        # Adding another sample shifts the timeseries and updates start_time./
        result = self.ts.add(5.55, when=self.now + timedelta(seconds=26))
        self.assertEqual(5, len(self.ts))
        self.assertEqual(
            [
                3.14,
                None,
                None,
                4.20,
                5.55,
            ],
            self.ts.data_points,
        )
        self.assertEqual(result, Timeseries.RESULT_SHIFTED)
        self.assertEqual(self.now + timedelta(seconds=5), self.ts.start_time)

        # Adding a very far away sample truncates the series.
        result = self.ts.add(6.69, when=self.now + timedelta(seconds=300))
        self.assertEqual(1, len(self.ts))
        self.assertEqual(
            [
                6.69,
            ],
            self.ts.data_points,
        )
        self.assertEqual(result, Timeseries.RESULT_TRUNCATED)
        self.assertEqual(self.now + timedelta(seconds=300), self.ts.start_time)

    def test_to_from_json(self):
        self.ts.add(1.23, when=self.now)
        self.ts.add(2.34, when=self.now + timedelta(seconds=5))
        self.ts.add(3.14, when=self.now + timedelta(seconds=10))
        self.assertEqual(
            {
                "v": 1,
                "start": "2020-01-01T02:30:00+00:00",
                "max": 5,
                "res": 5,
                "data": [
                    1.23,
                    2.34,
                    3.14,
                ],
            },
            self.ts.to_object(),
        )

        json_str = self.ts.to_json_string()
        self.assertEqual(
            {
                "v": 1,
                "start": "2020-01-01T02:30:00+00:00",
                "max": 5,
                "res": 5,
                "data": [
                    1.23,
                    2.34,
                    3.14,
                ],
            },
            json.loads(json_str),
        )

        self.assertEqual(
            {
                "v": 1,
                "start": "2020-01-01T02:30:00+00:00",
                "max": 5,
                "res": 5,
                "data": [
                    1.23,
                    2.34,
                    3.14,
                ],
            },
            Timeseries.from_json_string(json_str).to_object(),
        )

    def test_has_a_current_sample(self):
        """Ensure datetimes are downsampled to appropriate bucket."""
        self.ts.add(1.23, when=self.now)
        self.assertEqual(True, self.ts.has_a_current_sample(when=self.now))
        self.assertEqual(True, self.ts.has_a_current_sample(when=self.now + timedelta(seconds=1)))
        self.assertEqual(
            False, self.ts.has_a_current_sample(when=self.now + timedelta(seconds=10))
        )

    def test_iter_points(self):
        self.ts.add(1.23, when=self.now)
        self.ts.add(2.34, when=self.now + timedelta(seconds=5))
        self.assertEqual(
            [
                (datetime(2020, 1, 1, 2, 30, 0, tzinfo=timezone.utc), 1.23),
                (datetime(2020, 1, 1, 2, 30, 5, tzinfo=timezone.utc), 2.34),
            ],
            list(self.ts.iter_points()),
        )

    def test_get_normalized_points(self):
        self.ts.add(1.23, when=self.now)
        self.ts.add(1.23, when=self.now + timedelta(seconds=5))
        self.assertEqual((None, None, []), self.ts.get_normalized_points())
        self.ts.add(2.23, when=self.now + timedelta(seconds=5))
        self.assertEqual(
            (
                1.23,
                2.23,
                [
                    (datetime(2020, 1, 1, 2, 30, 0, tzinfo=timezone.utc), 0.0),
                    (datetime(2020, 1, 1, 2, 30, 5, tzinfo=timezone.utc), 1.0),
                ],
            ),
            self.ts.get_normalized_points(),
        )
