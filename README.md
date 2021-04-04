# django-simple-timeseries

Serializes small, simple timeseries to a database with Django. Provides the `Timeseries` class for manipulating timeseries, and the `TimeseriesField` custom field type for serializing.

Status: Experimental.

![Lint status](https://github.com/mik3y/django-simple-timeseries/actions/workflows/lint.yml/badge.svg)
![Test status](https://github.com/mik3y/django-simple-timeseries/actions/workflows/test.yml/badge.svg)

## Example

Define a `TimeseriesField` on a model:

```py
from django.db import models
from django_simple_timeseries import TimeseriesField

class Appliance(models.Model):
    name = models.CharField(max_length=64)
    temperature = TimeseriesField(
        resolution_seconds=60 * 60,
        max_points=24,
        help_text='Last 24 hours of temperature data',
    )
```

You can then access `Timeseries` methods on it:

```py
>>> a = Appliance(name='fridge')
>>> a.temperature.add(23.2)
>>> a.save()
>>> # Wait some time.
>>> a.temperature.add(26.5)
>>> a.save()
>>> print(list(a.iter_points()))
[
    (datetime(2020, 1, 1, 2, 30, 0, tzinfo=<UTC>), 23.2),
    (datetime(2020, 1, 2, 2, 30, 0, tzinfo=<UTC>), 26.5),
]
```

## Requirements

This package supports and is tested against the latest patch versions of:

* **Python:** 3.7, 3.8, 3.9
* **Django:** 2.2, 3.0, 3.1
* **MariaDB:** 10.2, 10.3, 10.4, 10.5
* **MySQL:** 5.7, 8.0
* **Oracle:** 12.2+ (only tested against 12.2.0.1 SE)
* **PostgreSQL:** 9.5, 10, 11, 12
* **SQLite:** 3.9.0+

All database backends are tested with the latest versions of their drivers. SQLite is also tested on GitHub Actions' latest macOS and Windows virtual environments.


## Installation

```
pip install django_simple_timeseries
```

For Django 3.1 and newer, no additional dependencies are required. For earlier versions, this project requires `django_jsonfield_backport`:

```
pip install django_jsonfield_backport
```

## How it works

### `Timeseries`

The `Timeseries` class implements a simple vector-like timeseries. Timeseries data is always contiguous.  

Internally, all timeseries instances have:
* `.start_time`, a `datetime.datetime` corresponding to the first data point;
* `.data`, the recorded data points (or y-values); and
* `.resolution`, a timedelta which describes the fixed interval between samples.

Samples are added by calling the `add()` method. The `add()` method ensures contiguousness with the following policy:
* If fewer than `resolution` seconds have elapsed since the most recent sample, the most recent sample is replaced.
* If more than `resolution` seconds have elapsed since the last sample, the vector is extended by the appropriate number of samples (`time_delta % resolution - 1`), each which will be recorded as gaps with the value `None`.
* In all cases, the vector is trimmed to no more than `max_points` samples.


### `TimeseriesField`

`TimeseriesField` is implemented as, and extends, a `JSONField`. The `Timeseries` methods `.to_object()` and `.from_object()` serialize a `Timeseries` instance to and from plain python objects, which the custom field type transparently implements.

## Usage Notes

This module is experimental and hasn't been exhaustively tested. It is not intended for large timeseries. Use at your own risk!
