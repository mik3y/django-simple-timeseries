from django import forms
from django.contrib import admin

from . import models


class BasicModelForm(forms.ModelForm):
    class Meta:
        model = models.BasicModel
        fields = ["ts1", "ts2"]

    # Class will automatically use `TimeseriesFormField` for each field.
    # ts1 = TimeseriesFormField()
    # ts2 = TimeseriesFormField()


@admin.register(models.BasicModel)
class BasicModelFormAdmin(admin.ModelAdmin):
    form = BasicModelForm
