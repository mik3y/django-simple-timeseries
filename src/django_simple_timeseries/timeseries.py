import datetime
import json
import math

from django.utils import timezone


def parse_isodate(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")


class Timeseries:
    VERSION = 1

    RESULT_ADDED = "added"
    RESULT_REPLACED = "replaced"
    RESULT_TRUNCATED = "truncated"
    RESULT_SHIFTED = "shifted"

    KEY_VERSION = "v"
    KEY_START_TIME = "start"
    KEY_RESOLUTION_SECONDS = "res"
    KEY_MAX_POINTS = "max"
    KEY_DATA_POINTS = "data"

    def __init__(
        self,
        start_time=None,
        data_points=None,
        max_points=20 * 24,
        resolution_seconds=300,
    ):
        self.start_time = start_time or timezone.now()
        self.data_points = data_points if data_points is not None else []
        self.max_points = max_points
        self.resolution = datetime.timedelta(seconds=resolution_seconds)

    def __len__(self):
        return len(self.data_points)

    def __getitem__(self, idx):
        return self.data_points[idx]

    def __eq__(self, other):
        if not isinstance(other, Timeseries):
            return False
        return self.to_object() == other.to_object()

    @classmethod
    def from_object(cls, o):
        object_version = o.get(cls.KEY_VERSION)
        if object_version != cls.VERSION:
            raise ValueError(f"Unsupported object version: {repr(object_version)}")
        return cls(
            start_time=parse_isodate(o[cls.KEY_START_TIME]),
            data_points=o[cls.KEY_DATA_POINTS],
            max_points=o[cls.KEY_MAX_POINTS],
            resolution_seconds=o[cls.KEY_RESOLUTION_SECONDS],
        )

    @classmethod
    def from_json_string(cls, s):
        o = json.loads(s)
        return cls.from_object(o)

    def normalize(self, dt):
        ts = int(dt.replace(tzinfo=timezone.utc).timestamp())
        normtime = ts - (ts % self.resolution.seconds)
        ret = datetime.datetime.fromtimestamp(normtime, timezone.utc)
        return ret

    @property
    def end_time(self):
        """Returns the datetime of the last bucket."""
        num_samples = len(self.data_points)
        if num_samples <= 1:
            return self.start_time
        return self.start_time + self.resolution * (num_samples - 1)

    def has_a_current_sample(self, when=None):
        when = when or timezone.now()
        if not len(self.data_points):
            return False
        return self.end_time == self.normalize(when)

    def to_object(self):
        return {
            self.KEY_VERSION: self.VERSION,
            self.KEY_START_TIME: self.start_time.isoformat(timespec="seconds"),
            self.KEY_DATA_POINTS: self.data_points,
            self.KEY_MAX_POINTS: self.max_points,
            self.KEY_RESOLUTION_SECONDS: self.resolution.seconds,
        }

    def to_json_string(self):
        return json.dumps(self.to_object(), indent=0)

    def add(self, value, when=None):
        when = self.normalize(when or timezone.now())
        current_sample_time = self.end_time
        distance_in_samples = math.floor((when - current_sample_time) / self.resolution)

        if len(self.data_points) == 0:
            # Special case: If there are no samples, `start_time` does not matter at all.
            distance_in_samples = 0

        if distance_in_samples < 0:
            raise ValueError(
                f"Sample would go back in time: from {self.end_time} to {when}"
            )
        elif distance_in_samples == 0:
            # Replace last value.
            if len(self.data_points):
                self.data_points[-1] = value
                return self.RESULT_REPLACED
            else:
                self.start_time = when
                self.data_points = [value]
                return self.RESULT_SHIFTED
        elif distance_in_samples > self.max_points:
            # Optimization: if extending the vector would bypass all samples, just truncate it
            # instead.
            self.data_points = [value]
            self.start_time = when
            return self.RESULT_TRUNCATED
        else:
            # Extend the vector to add this sample.
            for i in range(0, distance_in_samples):
                self.data_points.append(None)
            trim_samples = 0
            if len(self.data_points) > self.max_points:
                trim_samples = len(self.data_points) - self.max_points
                self.data_points = self.data_points[trim_samples:]
                self.start_time += trim_samples * self.resolution
            self.data_points[-1] = value
            return self.RESULT_SHIFTED if trim_samples else self.RESULT_ADDED

    def iter_points(self):
        ts = self.start_time
        for i, v in enumerate(self.data_points):
            ts = self.start_time + (i * self.resolution)
            yield (ts, v)

    def get_normalized_points(self):
        """Returns a list of points, normalized to values between 0 and 1."""
        minval = None
        maxval = None
        ret = []
        points = list(self.iter_points())
        for ts, v in points:
            if v is None:
                continue
            if minval is None or v < minval:
                minval = v
            if maxval is None or v > maxval:
                maxval = v

        if minval is None:
            assert maxval is None
            return None, None, []

        denom = maxval - minval
        if denom == 0:
            return None, None, []

        ret = []
        for ts, v in points:
            if v is not None:
                normv = (v - minval) / denom
            else:
                normv = 0
            ret.append((ts, normv))

        return minval, maxval, ret
