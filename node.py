import json

class BaseNode:
    def __init__(self, neighbor_info=None):
        self._neighbor_info = neighbor_info or {}

    def __getattr__(self, name):
        if name in self._neighbor_info:
            return self._neighbor_info[name]
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def __setattr__(self, name, value):
        if name == "_neighbor_info":
            super().__setattr__(name, value)
        elif name in self._neighbor_info:
            self._neighbor_info[name] = value
        else:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

    def __str__(self):
        return json.dumps(self._neighbor_info, indent=4)
    
    def get_all_attributes(self):
        return self._neighbor_info


class SatNode(BaseNode):
    def __init__(
        self,
        up_neighbor_info=None,
        down_neighbor_info=None,
        left_neighbor_info=None,
        right_neighbor_info=None,
        ground_neighbor_info=None,
    ):
        super().__init__({
            "up_neighbor_info": up_neighbor_info,
            "down_neighbor_info": down_neighbor_info,
            "left_neighbor_info": left_neighbor_info,
            "right_neighbor_info": right_neighbor_info,
            "ground_neighbor_info": ground_neighbor_info,
        })

class FacilityNode(BaseNode):
    def __init__(self, sat_neighbor_info=None):
        super().__init__({"sat_neighbor_info": sat_neighbor_info})
