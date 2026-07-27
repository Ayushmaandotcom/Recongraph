import json
import dataclasses
from decimal import Decimal
from datetime import date, datetime
from enum import Enum

class ReconEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        elif isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, frozenset):
            return list(obj)
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        return super().default(obj)
        
