from typing import Any

from .action import Action
from .command import Command

class State:
    def __init__(self):
        self.__dict__["info"] = {}
        self.__dict__["commands"] = {}
        self.__dict__["actions"] = {}

    def has(self, key: str) -> bool:
        return key in self.info

    def set(self, key: str, value: Any, frozen: bool = True) -> None:
        self.info[key] = (frozen, value)

    def register_action(self, key: str, action: Action) -> None:
        if key in self.actions:
            print(f"In {self.project_config.name}, action {key} registered more than once.")
            print(f"Remember that some recipies may register actions for you.")
            exit(1)
        self.actions[key] = action
    
    def register_command(self, key: str, command: Command) -> None:
        if key in self.commands:
            print(f"In {self.project_config.name}, command {key} registered more than once.")
            print(f"Remember that some recipies may register commands for you.")
            exit(1)
        self.commands[key] = command

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
        