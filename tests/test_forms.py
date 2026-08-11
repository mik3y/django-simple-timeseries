import unittest
from datetime import UTC, timedelta

from django.utils.timezone import datetime

from django_simple_timeseries.forms import TimeseriesWidget
from django_simple_timeseries.timeseries import Timeseries


class TimeseriesWidgetTests(unittest.TestCase):
    def setUp(self):
        self.widget = TimeseriesWidget()
        self.now = datetime(2020, 1, 1, 2, 30, tzinfo=UTC)

    def test_render(self):
        ts = Timeseries(start_time=self.now, max_points=5, resolution_seconds=5)
        ts.add(1.0, when=self.now)
        ts.add(2.0, when=self.now + timedelta(seconds=5))
        html = self.widget.render("ts1", ts)
        self.assertIn("Timeseries with 2 points", html)
        self.assertIn("<svg", html)

    def test_render_without_value(self):
        """A missing or non-Timeseries value renders a placeholder, not a crash."""
        self.assertIn("No timeseries data", self.widget.render("ts1", None))
        self.assertIn("No timeseries data", self.widget.render("ts1", "garbage"))

    def test_render_uniform_values(self):
        """A series whose values are all equal still reports its true size."""
        ts = Timeseries(start_time=self.now, max_points=5, resolution_seconds=5)
        ts.add(1.0, when=self.now)
        ts.add(1.0, when=self.now + timedelta(seconds=5))
        self.assertIn("Timeseries with 2 points", self.widget.render("ts1", ts))
