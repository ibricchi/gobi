from __future__ import annotations

import importlib

from .loader import GobiFile


class GobiError:
    code: int
    msg: str
    source: Action | Recipe

    def __init__(self, action: Action | Recipe, code: int, msg: str) -> None:
        self.code = code
        self.msg = msg
        self.source = action


class Action:
    name: str
    subname: str

    def help(self) -> str:
        return "No help available"

    def run(
        self, recipes: list[Recipe], actions: list[Action], args: list[str]
    ) -> GobiError | None:
        raise NotImplementedError()


class Recipe:
    name: str

    def help(self) -> str:
        return "No help available"

    def create_actions(self, gobi_file: GobiFile) -> GobiError | list[Action]:
        raise NotImplementedError()


def load_recipe(name) -> Recipe | None:
    try:
        mod = importlib.import_module(name)
        return mod.create()
    except ImportError:
        return None
