import json
import dataclasses
from decimal import Decimal
from enum import Enum

class Color(Enum):
    RED = "red"

@dataclasses.dataclass
class Item:
    amount: Decimal
    color: Color

@dataclasses.dataclass
class Container:
    items: list[Item]

class ReconEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        elif isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, Enum):
            return obj.value
        return super().default(obj)
        
c = Container([Item(Decimal("10.5"), Color.RED)])
print(json.dumps(c, cls=ReconEncoder))
