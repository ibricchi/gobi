from __future__ import annotations
from dataclasses import dataclass

import os

from .logger import Logger

@dataclass(frozen=True)
class Environment:
    config_folder: str
    config_project_path: str  
    recipe_folder: str

    @classmethod
    def default(cls):
        config_folder = os.path.join(os.path.expanduser("~"), ".gobi")
        if os.environ.get("GOBI_CONFIG_FOLDER"):
            config_folder = os.environ.get("GOBI_CONFIG_FOLDER")
            assert config_folder is not None
            # check config folder exists
            if not os.path.isdir(config_folder):
                Logger.error("Could not find gobi config folder specified by GOBI_CONFIG_FOLDER environment variable")
                Logger.fatal("Please set GOBI_CONFIG_FOLDER to a valid folder, or remove the environment variable to use the default ~/.gobi folder")
        else:
            if not os.path.isdir(config_folder):
                Logger.error("Could not find gobi config folder at default ~/.gobi/, you can override this using GOBI_CONFIG_FOLDER")
                Logger.fatal("If you have moved your gobi config folder, please set GOBI_CONFIG_FOLDER to the new location")

        config_project_path = os.path.join(config_folder, "gobi.toml")
        if not os.path.isfile(config_project_path):
            Logger.fatal(f"Could not find gobi config file at expected: '{config_project_path}'")
        
        recipe_folder = os.path.join(config_folder, "recipes")
        if not os.path.isdir(recipe_folder):
            Logger.fatal(f"Could not find gobi recipe folder at expected: '{recipe_folder}'")
        
        return cls(config_folder, config_project_path, recipe_folder)

class State():
    env: Environment
    args: list[str]
    original_args: list[str]
    context: dict
    project: Project
    project_breadcrumbs: list[Project]
    perm_recipes: list[str]

    def __init__(self) -> None:
        self.args = []
        self.context = {}
        self.project_name = ""
        self.project_breadcrumbs = []
        self.perm_recipes = []
    
    def set_args(self, args: list[str]) -> None:
        self.args = args[1:]
        self.original_args = args[1:].copy()
    
    def set_project(self, project: Project) -> None:
        self.project_breadcrumbs.append(project)
        self.project = project
    
    def unset_project(self) -> None:
        self.project_breadcrumbs.pop()
        if len(self.project_breadcrumbs) > 0:
            self.project = self.project_breadcrumbs[-1]
    
    def set_env(self, env: Environment) -> None:
        self.env = env

class Action:
    hooks: list[Action]
    recipe: str

    def __init__(self) -> None:
        self.hooks = []
    
    def run(self, state: State) -> None:
        raise NotImplementedError()
    
class Recipe:
    name: str
    def validate(self, config: dict, state: State) -> None:
        pass

    def register_actions(self, config: dict, state: State) -> list[tuple[str, Action]]:
        return []

    def register_hooks(self, config: dict, actions: dict[str, Action], state: State) -> None:
        pass

class Project:
    name: str
    config_path: str
    config: dict
    projects = dict[str, str]
    recipes = list[Recipe]
    actions = dict[str, Action]

    def __init__(self, name: str, config_path: str, config: dict) -> None:
        self.name = name
        self.config_path = config_path
        self.config = config
        self.projects = {}
        self.recipes = []
        self.actions = {}