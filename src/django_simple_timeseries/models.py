import logging

from django.db.models import JSONField

from django_simple_timeseries.forms import TimeseriesFormField
from django_simple_timeseries.timeseries import Timeseries

logger = logging.getLogger(__name__)

__all__ = ["TimeseriesField"]


class TimeseriesField(JSONField):
    """A field storing a `Timeseries`, backed by a `JSONField` column.

    The model attribute is always a `Timeseries` instance: new instances get a
    fresh, empty series, and values loaded from the database are deserialized
    back into `Timeseries` objects. A malformed database value is logged and
    replaced with a fresh series rather than raised.

    Arguments:
        resolution_seconds: The width of each bucket, in seconds.
        max_points: Maximum number of buckets to retain; older values are
            dropped as newer samples are recorded.
    """

    def __init__(self, resolution_seconds=60, max_points=60 * 24, *args, **kwargs):
        self.resolution_seconds = resolution_seconds
        self.max_points = max_points
        kwargs["default"] = self.new_default_timeseries
        super().__init__(*args, **kwargs)

    def new_default_timeseries(self):
        return Timeseries(resolution_seconds=self.resolution_seconds, max_points=self.max_points)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["resolution_seconds"] = self.resolution_seconds
        kwargs["max_points"] = self.max_points
        if kwargs.get("default") == self.new_default_timeseries:
            del kwargs["default"]
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        """
        Converts a value as returned by the database to a Python object. It is the
        reverse of get_prep_value().
        """
        json_value = super().from_db_value(value, expression, connection)
        if json_value is None:
            return self.new_default_timeseries()
        try:
            return Timeseries.from_object(json_value)
        except (ValueError, TypeError) as e:
            logger.warning(f"Database value invalid, returning empty timeseries: {e}")
            return self.new_default_timeseries()

    def get_prep_value(self, value):
        """
        value is the current value of the model’s attribute, and the method should return data
        in a format that has been prepared for use as a parameter in a query.
        """
        value = value or self.new_default_timeseries()
        object_value = value.to_object()
        json_value = super().get_prep_value(object_value)
        return json_value

    def to_python(self, value):
        if not value:
            return None
        elif isinstance(value, Timeseries):
            return value
        try:
            if isinstance(value, str):
                return Timeseries.from_json_string(value)
            return Timeseries.from_object(value)
        except (TypeError, ValueError) as e:
            logger.warning(f"Database value invalid, returning empty timeseries: {e}")
            return self.new_default_timeseries()

    def formfield(self, **kwargs):
        return TimeseriesFormField(**kwargs)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)
