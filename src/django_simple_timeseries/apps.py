from django.apps import AppConfig


class SimpleTimeseriesConfig(AppConfig):
    name = "django_simple_timeseries"
    verbose_name = "Django Simple Timeseries"

    def ready(self):
        pass
