import datetime
import decimal
import json
import sys

import os

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            ARGS = ("year", "month", "day", "hour", "minute", "second", "microsecond")
            return {
                "__type__": "datetime.datetime",
                "args": [getattr(obj, a) for a in ARGS],
            }
        elif isinstance(obj, datetime.date):
            ARGS = ("year", "month", "day")
            return {
                "__type__": "datetime.date",
                "args": [getattr(obj, a) for a in ARGS],
            }
        elif isinstance(obj, datetime.time):
            ARGS = ("hour", "minute", "second", "microsecond")
            return {
                "__type__": "datetime.time",
                "args": [getattr(obj, a) for a in ARGS],
            }
        elif isinstance(obj, datetime.timedelta):
            ARGS = ("days", "seconds", "microseconds")
            return {
                "__type__": "datetime.timedelta",
                "args": [getattr(obj, a) for a in ARGS],
            }
        elif isinstance(obj, decimal.Decimal):
            return {
                "__type__": "decimal.Decimal",
                "args": [
                    str(obj),
                ],
            }
        elif isinstance(obj, bytes):
            return {
                "__type__": "bytes",
                "args": [" ".join([str(i) for i in obj])],
            }
        else:
            return super().default(obj)

        

class EnhancedJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, object_hook=self.object_hook, **kwargs)

    def object_hook(self, d):
        if "__type__" not in d:
            return d
        o = sys.modules[__name__]
        for e in d["__type__"].split("."):
            o = getattr(o, e)
        args, kwargs = d.get("args", ()), d.get("kwargs", {})
        return o(*args, **kwargs)



class ConfigFile:
    def __init__(self, path="config.json", default=None):
        if default is None:
            default = {}
        self.default = default
        self.path = path
        try:
            self.config = json.loads(
                open(self.path, "rb").read(), cls=EnhancedJSONDecoder
            )
        except FileNotFoundError:
            self.config = default
            self.save()

    def __getitem__(self, key):
        if key in self.config:
            return self.config[key]
        else:
            if key in self.default:
                return self.default[key]

    def __setitem__(self, key, value):
        self.config[key] = value
        self.save()

    def save(self):
        with open(self.path, "w") as f:
            f.write(
                json.dumps(
                    self.config, indent=4, sort_keys=True, cls=EnhancedJSONEncoder
                )
            )


def GetConfig():
    return ConfigFile(default={})