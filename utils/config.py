from __future__ import annotations
from dataclasses import dataclass
import tomli
import os
from typing import Any
from jsonschema import validate

@dataclass(frozen=True)
class Environment:
    config_folder: str
    config_file: str
    recipe_folder: str
    command_folder: str

    @classmethod
    def default(cls):
        config_folder = os.path.join(os.path.expanduser("~"), ".gobi")
        if os.environ.get("GOBI_CONFIG_FOLDER"):
            config_folder = os.environ.get("GOBI_CONFIG_FOLDER")
            assert config_folder is not None
            # check config folder exists
            if not os.path.isdir(config_folder):
                print("Could not find gobi config folder specified by GOBI_CONFIG_FOLDER environment variable")
                exit(1)
        else:
            if not os.path.isdir(config_folder):
                print("Could not find gobi config folder at default ~/.gobi/, you can override this using GOBI_CONFIG_FOLDER")
                exit(1)
        
        config_file = os.path.join(config_folder, "config.toml")
        if not os.path.isfile(config_file):
            print(f"Could not find gobi config file at expected: '{config_file}'")
            exit(1)

        recipe_folder = os.path.join(config_folder, "recipes")
        if not os.path.isdir(recipe_folder):
            print(f"Could not find gobi recipe folder at expected: '{recipe_folder}'")
            exit(1)
        
        command_folder = os.path.join(config_folder, "commands")
        if not os.path.isdir(command_folder):
            print(f"Could not find gobi command folder at expected: '{command_folder}'")
            exit(1)
        
        return cls(config_folder, config_file, recipe_folder, command_folder)

class ProjectConfig:
    env: Environment
    path: str
    name: str
    config: dict[str, Any]
    recipes: list[str]

    def __init__(self, env: Environment, project: str, project_path: str) -> None:
        self.env = env
        self.path = project_path
        self.name = project

        # check that config path is a file
        if not os.path.isfile(self.path):
            print(f"Specified config file for {project} '{self.path}' not found at {self.path}")
            exit(1)

        with open(self.path, "rb") as f:
            try:
                self.config = tomli.load(f)
            except tomli.TOMLDecodeError as e:
                print(f"Error parsing config file '{self.path}' for {project}: {e}")
                exit(1)

        # check that gobi has a recipes key
        if not "gobi" in self.config:
            print(f"Config file for {project} '{self.path}' does not contain a 'gobi' key")
            exit(1)
        if not "recipes" in self.config["gobi"]:
            print(f"Config file for {project} '{self.path}' does not contain a 'gobi.recipes' key")
            exit(1)
        if not isinstance(self.config["gobi"]["recipes"], list):
            print(f"Config file for {project} '{self.path}' does not contain a 'gobi.recipes' key of type list")
            exit(1)
        for recipe in self.config["gobi"]["recipes"]:
            if not isinstance(recipe, str):
                print(f"Config file for {project} '{self.path}' does not contain a 'gobi.recipes' key of type list of strings")
                exit(1)
        
        self.recipes = self.config["gobi"]["recipes"]

    def __getitem__(self, key):
        return self.config[key]

global_config_schema = {
    "type": "object",
    "properties": {
        "projects": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "string"
                }
            }
        },
        "gobi": {
            "type": "object",
            "properties": {
                "commands": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        }
    },
    "required": ["projects"]
}

class GlobalConfig:
    env: Environment
    path: str
    projects: dict[str, str]
    config: dict[str, Any]
    commands: list[str]

    def __init__(self, env: Environment) -> None:
        self.env = env
        self.path = env.config_file

        with open(self.path, "rb") as f:
            try:
                self.config = tomli.load(f)
            except tomli.TOMLDecodeError as e:
                print(f"Error parsing config file '{self.path}': {e}")
                exit(1)

        # check that config has recipes key
        validate(instance=self.config, schema=global_config_schema)
        
        self.projects = self.config["projects"]

        if "gobi" in self.config and "commands" in self.config["gobi"]:
            self.commands = self.config["gobi"]["commands"]
        else:
            self.commands = []

    def __getitem__(self, key):
        return self.config[key]

    def get_project(self, project: str):
        if not project in self.projects:
            print(f"Project {project} not found in config file '{self.path}'")
            exit(1)

        project_path = self.projects[project]
        return ProjectConfig(self.env, project, project_path)