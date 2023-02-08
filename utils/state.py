from typing import Any

class State:
    def __init__(self):
        self.__dict__["info"] = {}

    def has(self, key: str) -> bool:
        return key in self.info

    def set(self, key: str, value: Any, frozen: bool = True) -> None:
        self.info[key] = (frozen, value)

    def get(self, key: str) -> Any:
        return self.info[key][1]
    
    def __getattr__(self, __name: str) -> Any:
        try:
            _, out = self.__dict__['info'][__name]
            return out
        except KeyError:
            raise AttributeError(f"Attribute {__name} not found")


    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in self.info and self.info[__name][0]:
            raise AttributeError(f"Cannot set attribute {__name} as it is read only")
        else:
            self.info[__name] = (False, __value)
        