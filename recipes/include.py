from __future__ import annotations

from utils.loader import GobiFile
from utils.recipes import GobiError, Action, Recipe

from recipes.gobi import GobiRecipe

import os
import tempfile
import time
from string import Template

class IncludeRecipe(Recipe):
    def __init__(self):
        self.name = "include"

    def help(self) -> str:
        return """
This recipe is used to import a file and provide environments to override parts of it.

To use this just specify as many imports of the following format:

[import.<name>]
path = "/path/to/import.toml"
[import.<name>.env]]
key = "value"
key2 = 3

Name will be prepended to all imported action to allow for disambiguating them.

Note! imported actions will be considered lower priority than ones defined in the file, so the full name will be needed for an imported action if it's subname appears in the current file.
"""

    def create_actions(self, gobi_file: GobiFile) -> GobiError | tuple[list[Action], list[str]]:
        config = gobi_file.data.get("include", {})

        actions: list[Action] = []
        deps: list[str] = []
        for name in config:
            include = config.get(name)
            if "path" not in include:
                return GobiError(self, -1, "Include actions require path")
            
            path = include.get("path")
            if not os.path.isabs(path):
                path = os.path.join(os.path.dirname(gobi_file.path), path)

            env = include.get("env", {})

            if not os.path.isfile(path):
                return GobiError(self, -1, f"Could not find '{path}'")

            with open(path, "r") as base_file:
                base_file_info = base_file.read();
                new_file_info = Template(base_file_info).safe_substitute(env)
                new_file = tempfile.NamedTemporaryFile("w+")
                new_file.write(new_file_info)
                new_file.flush()
                gobi_file = GobiFile(new_file.name)
                gobi_file.cacheable = False
                if gobi_file.error:
                    return GobiError(self, -1, f"Failed to read gobi file {path}: {gobi_file.error}")
                
            gobi_recipe = GobiRecipe()
            new_actions = gobi_recipe.create_actions(gobi_file)
            if isinstance(new_actions, GobiError):
                return new_actions
            else:
                actions.extend(new_actions[0])
                deps.append(path)
                deps.extend(new_actions[1])

        for action in actions:
            action.name = f"{name}.{action.name}"
            action.priority = False

        return actions, deps

def create() -> Recipe:
    return IncludeRecipe()
