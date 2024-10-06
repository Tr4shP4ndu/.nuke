from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class nodeUpdate():
    node_name : str
    knob_name : str
    value : Any
    @staticmethod
    def from_dict(data : Dict[Any, Any]):
        return nodeUpdate(node_name = data["node_name"], knob_name = data["knob_name"], value = data["value"])
