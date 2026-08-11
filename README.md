# django-simple-timeseries

Serializes small, simple timeseries to a database with Django. Provides the `Timeseries` class for manipulating timeseries, and the `TimeseriesField` custom field type for serializing.

Status: Experimental.

[![PyPI version](https://badge.fury.io/py/django-simple-timeseries.svg)](https://badge.fury.io/py/django-simple-timeseries)
[![PyPI Supported Python Versions](https://img.shields.io/pypi/pyversions/django-simple-timeseries.svg)](https://pypi.python.org/pypi/django-simple-timeseries/) ![Test status](https://github.com/mik3y/django-simple-timeseries/actions/workflows/test.yml/badge.svg)

## Table of Contents

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Example](#example)
- [Requirements](#requirements)
- [Installation](#installation)
- [How it works](#how-it-works)
  - [`Timeseries`](#timeseries)
  - [`TimeseriesField`](#timeseriesfield)
- [Usage Notes](#usage-notes)
- [API reference](#api-reference)
- [Maintainer notes](#maintainer-notes)
- [Changelog](#changelog)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

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
        help_text="Last 24 hours of temperature data",
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
>>> print(list(a.temperature.iter_points()))
[
    (datetime(2020, 1, 1, 2, 30, 0, tzinfo=<UTC>), 23.2),
    (datetime(2020, 1, 2, 2, 30, 0, tzinfo=<UTC>), 26.5),
]
```

## Requirements

This package is tested against the latest versions of:

* **Python:** 3.12, 3.13, 3.14
* **Django:** 4.2, 5.2, 6.0
* **MySQL:** 8.0
* **PostgreSQL:** 14
* **SQLite:** 3.9.0+

All database backends are tested with the latest versions of their drivers. SQLite is also tested on GitHub Actions' latest macOS virtual environment.


## Installation

```
pip install django_simple_timeseries
```

## How it works

### `Timeseries`

The `Timeseries` class implements a simple vector-like timeseries. Timeseries data is always contiguous.  

Internally, all timeseries instances have:
* `.start_time`, a `datetime.datetime` corresponding to the first data point;
* `.data_points`, the recorded data points (or y-values); and
* `.resolution`, a timedelta which describes the fixed interval between samples.

Samples are added by calling the `add()` method. The `add()` method ensures contiguousness with the following policy:
* If fewer than `resolution` seconds have elapsed since the most recent sample, the most recent sample is replaced.
* If more than `resolution` seconds have elapsed since the last sample, the vector is extended by the appropriate number of samples (`time_delta % resolution - 1`), each which will be recorded as gaps with the value `None`.
* In all cases, the vector is trimmed to no more than `max_points` samples.


### `TimeseriesField`

`TimeseriesField` is implemented as, and extends, a `JSONField`. The `Timeseries` methods `.to_object()` and `.from_object()` serialize a `Timeseries` instance to and from plain python objects, which the custom field type transparently implements.

## Usage Notes

This module is experimental and hasn't been exhaustively tested. It is not intended for large timeseries. Use at your own risk!

## API reference

Complete reference documentation for the public classes and methods, generated from the library's docstrings, lives in [`docs/api.md`](docs/api.md).

## Maintainer notes

See [`docs/maintainer-notes.md`](docs/maintainer-notes.md) for how releases are cut and published.

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md).
