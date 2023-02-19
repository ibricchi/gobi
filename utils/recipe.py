import os
import sys

import importlib

from .action import Action
from .logger import Logger
from .state import State

class Recipe:
    def validate_config(self, config: dict) -> None:
        pass

    def pre_action(self) -> None:
        pass

    def post_action(self) -> None:
        pass

def load_recipe(state: State, name: str) -> Recipe:
    mod = importlib.import_module(name)

    # check mod has a create function
    if not hasattr(mod, "create"):
        Logger.fatal(
            f"[{state.project.name}]: Recipe {name} does not have a create function"
        )

    # check mod.create takes a state and return a recipe
    create = getattr(mod, "create")
    if not hasattr(create, "__call__"):
        Logger.fatal(
            f"[{state.project.name}]: Recipe {name} create function is not callable"
        )
    if not hasattr(create, "__annotations__"):
        Logger.fatal(
            f"[{state.project.name}]: Recipe {name} create function does not have type annotations"
        )
    if create.__annotations__ != {
        "state": State,
        "return": Recipe,
    }:
        Logger.fatal(
            f"[{state.project.name}]: Recipe {name} create function does not have the correct types"
        )

    return create(state)
