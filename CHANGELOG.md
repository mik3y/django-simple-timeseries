# `django_simple_timeseries` changelog

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
