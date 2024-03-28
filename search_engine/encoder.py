from json import JSONEncoder
from datetime import datetime, date, time

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        # Let the base class default method raise the TypeError
        return JSONEncoder.default(self, obj)
