import os
import sys

import importlib

from .containers import State, Recipe
from .logger import Logger

def load_recipe(name: str, state: State) -> Recipe:
    mod = importlib.import_module(name)

    # check mod has a create function
    if not hasattr(mod, "create"):
        Logger.fatal(
            f"[Project {state.project.name}]: Recipe {name} does not have a create function"
        )

    # check mod.create takes a state and return a recipe
    create = getattr(mod, "create")
    if not hasattr(create, "__call__"):
        Logger.fatal(
            f"[Project {state.project.name}]: Recipe {name} create function is not callable"
        )
    if not hasattr(create, "__annotations__"):
        Logger.fatal(
            f"[Project {state.project.name}]: Recipe {name} create function does not have type annotations"
        )
    if create.__annotations__ != {
        "state": State,
        "return": Recipe,
    }:
        Logger.fatal(
            f"[Project {state.project.name}]: Recipe {name} create function does not have the correct types"
        )

    return create(state)
