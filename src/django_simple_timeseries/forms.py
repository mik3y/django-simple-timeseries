import json
from string import Template

from django.forms import Field, Widget
from django.utils.translation import gettext_lazy as _

__all__ = ("TimeseriesFormField", "TimeseriesWidget")

# A sparkline SVG that draws itself.
SPARKLINE_SVG_TEMPLATE = Template(
    """
<svg version="1.1"
     baseProfile="full"
     id=$elementId
     xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     xmlns:ev="http://www.w3.org/2001/xml-events"
     width="100%" height="100%"
     onload='drawTimeseries($elementId, $points, $minval, $maxval)'>
  <script><![CDATA[
    function drawTimeseries(elementId, parts, mn, mx) {
        var elem = document.getElementById(elementId);
        var x1 = 0, y1 = 0, x2 = 0, y2 = 100 - (100 * (parts[0] - mn) / (mx - mn));
        for (var i=0; i<parts.length; i++) {
            var ln = document.createElementNS ("http://www.w3.org/2000/svg", "line");
            y1 = y2; x1 = x2;
            x2 = 100 * (i / parts.length), y2 = 100 - (100 * (parts[i] - mn) / (mx - mn));
            ln.setAttribute("x1", x1 + "%");
            ln.setAttribute("x2", x2 + "%");
            ln.setAttribute("y1", y1 + "%");
            ln.setAttribute("y2", y2 + "%");
            ln.setAttribute("stroke", "rgba(0,0,0,0.5)");
            ln.setAttribute("stroke-width", "1");
            elem.appendChild(ln);
        }
    }
  ]]></script>
</svg>
"""
)


class TimeseriesWidget(Widget):
    def render(self, name, value, attrs=None, renderer=None):
        minval, maxval, points = value.get_normalized_points()
        svg = SPARKLINE_SVG_TEMPLATE.substitute(
            elementId=json.dumps(f"svg-for-{name}"),
            minval=json.dumps(0),
            maxval=json.dumps(1),
            points=json.dumps([p[1] for p in points]),
        )
        return f"""
            <div style="display: inline-block;">
                <div>Timeseries with {len(points)} points</div>
                <div>{svg}</div>
            </div>
        """


class TimeseriesFormField(Field):
    default_error_messages = {
        "invalid": _("Enter a valid Timeseries."),
    }
    widget = TimeseriesWidget

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_python(self, value):
        return value

    def bound_data(self, data, initial):
        return initial

    def prepare_value(self, value):
        return value

    def has_changed(self, initial, data):
        return False
