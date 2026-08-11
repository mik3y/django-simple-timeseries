# `django_simple_timeseries` changelog

## Current version (in development)

* Bugfix: Resolutions of one day or longer no longer crash with `ZeroDivisionError` and serialize correctly.
* Bugfix: Aware non-UTC datetimes are now bucketed by the instant they refer to; previously their wall-clock time was misread as UTC.
* Bugfix: `Timeseries.from_object` raises `ValueError` for every malformed input; previously a dict with missing keys raised `KeyError`, which escaped `TimeseriesField`'s malformed-value handling.
* Bugfix: An empty series is no longer confused with a missing value; previously saving one silently reset its `start_time`.
* Bugfix: Saving a non-`Timeseries` value raises a clear `TypeError` instead of an opaque `AttributeError`.
* Bugfix: `resolution_seconds` and `max_points` are now keyword-only, so a positional `verbose_name` is no longer silently misread as `resolution_seconds`.
* Bugfix: The admin widget renders a placeholder for missing values instead of crashing, and reports the true number of points when all values are equal.

* Build: Switched packaging from poetry to uv.
* Compatibility: Now tested on Python 3.12-3.14 and Django 4.2/5.2/6.0.
* Docs: Added an API reference generated from docstrings (`docs/api.md`).

## v0.3.0 (2025-05-04)

* Bugfix: Django serialization compatibility.
* Compatibility: Dropped official support for older Python/Django versions, but things probably still work fine.
* Compatibility: Dropped official tests for Oracle and MariaDB, but things probably still work fine.
* Improvement: Return an empty timeseries if a malformed value is deserialized from the database.

## v0.2.0 (2021-04-13)

* Bugfix: Avoid generating unnecessary `default` argument in migrations.

## v0.1.2 (2021-04-04)

* Bugfix: Fix divide-by-zero.

## v0.1.1 (2021-04-04)

* Fix Django 2.2 & 3.0 compatibility.

## v0.1.0 (2021-04-04)

* Initial release.
